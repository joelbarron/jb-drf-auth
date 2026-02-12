import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt
from jwt import PyJWTError
from django.utils.translation import gettext_lazy as _

from jb_drf_auth.conf import get_social_settings
from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.providers.base import BaseSocialProvider, SocialIdentity


class OidcSocialProvider(BaseSocialProvider):
    """
    OIDC provider that validates id_token against issuer audience and JWKS.
    """

    def _social_debug_enabled(self) -> bool:
        return bool(get_social_settings().get("DEBUG_ERRORS", False))

    def _raise_exchange_error(self, exc):
        if isinstance(exc, HTTPError):
            error_code = "social_token_exchange_failed"
            error_detail = _("Could not exchange authorization_code with social provider.")
            provider_error = None
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                payload = {}
            if isinstance(payload, dict):
                provider_error = payload.get("error")
                if provider_error == "invalid_grant":
                    error_code = "social_invalid_grant"
                    error_detail = _(
                        "authorization_code is invalid, expired, already used, or redirect_uri mismatched."
                    )
                elif provider_error == "invalid_client":
                    error_code = "social_invalid_client"
                    error_detail = _("Social provider client credentials are invalid.")
            if self._social_debug_enabled():
                raise SocialAuthError(
                    _("%(detail)s provider_error=%(provider_error)s status=%(status)s")
                    % {
                        "detail": error_detail,
                        "provider_error": provider_error or "unknown",
                        "status": exc.code,
                    },
                    status_code=401,
                    code=error_code,
                )
            raise SocialAuthError(error_detail, status_code=401, code=error_code)

        raise SocialAuthError(
            _("Could not exchange authorization_code with social provider."),
            status_code=401,
            code="social_token_exchange_failed",
        )

    def _exchange_authorization_code(self, payload: dict) -> str:
        token_url = self.provider_settings.get("TOKEN_URL")
        client_ids = self.provider_settings.get("CLIENT_IDS") or ()
        client_secret = self.provider_settings.get("CLIENT_SECRET")
        code = payload.get("authorization_code")
        if isinstance(client_ids, str):
            client_ids = (client_ids,)
        client_id = payload.get("client_id") or (client_ids[0] if client_ids else None)

        if not token_url:
            raise SocialAuthError(
                _("Missing TOKEN_URL configuration for provider '%(provider)s'.")
                % {"provider": self.provider},
                status_code=400,
                code="social_config_error",
            )
        if not client_id:
            raise SocialAuthError(
                _("Missing client_id for provider '%(provider)s'.") % {"provider": self.provider},
                status_code=400,
                code="social_config_error",
            )
        if not code:
            raise SocialAuthError(
                _("authorization_code is required for this social login request."),
                status_code=400,
                code="social_bad_request",
            )

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
        }
        if client_secret:
            data["client_secret"] = client_secret
        if payload.get("redirect_uri"):
            data["redirect_uri"] = payload.get("redirect_uri")
        if payload.get("code_verifier"):
            data["code_verifier"] = payload.get("code_verifier")

        request = Request(
            token_url,
            data=urlencode(data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                token_payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            self._raise_exchange_error(exc)

        id_token = token_payload.get("id_token")
        if not id_token:
            raise SocialAuthError(
                _("Social provider response did not include id_token."),
                status_code=401,
                code="social_invalid_token",
            )
        return id_token

    def authenticate(self, payload: dict) -> SocialIdentity:
        id_token = payload.get("id_token")
        if not id_token and payload.get("authorization_code"):
            id_token = self._exchange_authorization_code(payload)
        if not id_token:
            raise SocialAuthError(
                _("id_token or authorization_code is required for social login."),
                status_code=400,
                code="social_bad_request",
            )

        issuer = self.provider_settings.get("ISSUER")
        jwks_url = self.provider_settings.get("JWKS_URL")
        client_ids = self.provider_settings.get("CLIENT_IDS") or ()
        if isinstance(client_ids, str):
            client_ids = (client_ids,)

        if not issuer or not jwks_url:
            raise SocialAuthError(
                _("Missing OIDC issuer/JWKS configuration for provider '%(provider)s'.")
                % {"provider": self.provider},
                status_code=400,
                code="social_config_error",
            )
        if not client_ids:
            raise SocialAuthError(
                _("Missing OIDC client ids for provider '%(provider)s'.")
                % {"provider": self.provider},
                status_code=400,
                code="social_config_error",
            )

        try:
            signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(id_token).key
            claims = jwt.decode(
                id_token,
                signing_key,
                algorithms=["RS256", "ES256"],
                audience=list(client_ids),
                issuer=issuer,
            )
        except PyJWTError:
            raise SocialAuthError(
                _("Social token is invalid or expired."),
                status_code=401,
                code="social_invalid_token",
            )
        provider_user_id = claims.get("sub")
        if not provider_user_id:
            raise SocialAuthError(
                _("OIDC token missing 'sub' claim."),
                status_code=401,
                code="social_invalid_token",
            )

        return SocialIdentity(
            provider=self.provider,
            provider_user_id=str(provider_user_id),
            email=claims.get("email"),
            email_verified=bool(claims.get("email_verified", False)),
            first_name=claims.get("given_name"),
            last_name_1=claims.get("family_name"),
            picture_url=claims.get("picture"),
            raw_response=claims,
        )
