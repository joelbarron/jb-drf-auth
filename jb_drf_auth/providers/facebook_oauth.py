import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.utils.translation import gettext_lazy as _

from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.providers.base import BaseSocialProvider, SocialIdentity


class FacebookOAuthProvider(BaseSocialProvider):
    def _read_json(self, url: str) -> dict:
        try:
            with urlopen(url, timeout=8) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError):
            raise SocialAuthError(
                _("Could not validate Facebook access_token."),
                status_code=401,
                code="social_invalid_token",
            )

    def _debug_token(self, access_token: str):
        app_id = self.provider_settings.get("APP_ID")
        app_secret = self.provider_settings.get("APP_SECRET")
        if not app_id or not app_secret:
            return

        params = urlencode(
            {
                "input_token": access_token,
                "access_token": f"{app_id}|{app_secret}",
            }
        )
        url = f"https://graph.facebook.com/debug_token?{params}"
        payload = self._read_json(url)
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        if not data.get("is_valid", False):
            raise SocialAuthError(
                _("Facebook access token is invalid."),
                status_code=401,
                code="social_invalid_token",
            )
        if str(data.get("app_id", "")) != str(app_id):
            raise SocialAuthError(
                _("Facebook access token app_id does not match configuration."),
                status_code=401,
                code="social_invalid_token",
            )

    def authenticate(self, payload: dict) -> SocialIdentity:
        access_token = payload.get("access_token")
        if not access_token:
            raise SocialAuthError(
                _("access_token is required for Facebook social login."),
                status_code=400,
                code="social_bad_request",
            )

        self._debug_token(access_token)

        graph_api_version = self.provider_settings.get("GRAPH_API_VERSION", "v21.0")
        fields = "id,email,first_name,last_name,picture.type(large)"
        params = urlencode({"fields": fields, "access_token": access_token})
        profile_url = f"https://graph.facebook.com/{graph_api_version}/me?{params}"
        raw = self._read_json(profile_url)

        provider_user_id = raw.get("id")
        if not provider_user_id:
            raise SocialAuthError(
                _("Facebook response missing user id."),
                status_code=401,
                code="social_invalid_token",
            )

        picture_url = None
        picture = raw.get("picture")
        if isinstance(picture, dict):
            picture_data = picture.get("data")
            if isinstance(picture_data, dict):
                picture_url = picture_data.get("url")

        email = raw.get("email")
        assume_email_verified = bool(self.provider_settings.get("ASSUME_EMAIL_VERIFIED", True))
        return SocialIdentity(
            provider=self.provider,
            provider_user_id=str(provider_user_id),
            email=email,
            email_verified=bool(email) and assume_email_verified,
            first_name=raw.get("first_name"),
            last_name_1=raw.get("last_name"),
            picture_url=picture_url,
            raw_response=raw if isinstance(raw, dict) else {},
        )
