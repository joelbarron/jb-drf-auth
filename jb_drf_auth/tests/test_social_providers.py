import os
import unittest
from unittest.mock import MagicMock, patch

import django
from jwt import PyJWTError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.providers.facebook_oauth import FacebookOAuthProvider
from jb_drf_auth.providers.oidc import OidcSocialProvider


class OidcProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = OidcSocialProvider(
            provider="google",
            provider_settings={
                "ISSUER": "https://accounts.google.com",
                "JWKS_URL": "https://www.googleapis.com/oauth2/v3/certs",
                "CLIENT_IDS": ("google-web-client-id",),
                "TOKEN_URL": "https://oauth2.googleapis.com/token",
            },
        )

    @patch("jb_drf_auth.providers.oidc.jwt.decode")
    @patch("jb_drf_auth.providers.oidc.jwt.PyJWKClient")
    def test_authenticate_with_id_token_success(self, pyjwk_cls, jwt_decode):
        pyjwk_cls.return_value.get_signing_key_from_jwt.return_value.key = "public-key"
        jwt_decode.return_value = {
            "sub": "provider-123",
            "email": "user@example.com",
            "email_verified": True,
            "given_name": "Joel",
            "family_name": "Barron",
            "picture": "https://img.example/a.jpg",
        }

        identity = self.provider.authenticate({"id_token": "id-token"})
        self.assertEqual(identity.provider, "google")
        self.assertEqual(identity.provider_user_id, "provider-123")
        self.assertEqual(identity.email, "user@example.com")
        self.assertEqual(identity.email_verified, True)

    @patch("jb_drf_auth.providers.oidc.jwt.decode")
    @patch("jb_drf_auth.providers.oidc.jwt.PyJWKClient")
    def test_authenticate_invalid_token_raises_401(self, pyjwk_cls, jwt_decode):
        pyjwk_cls.return_value.get_signing_key_from_jwt.return_value.key = "public-key"
        jwt_decode.side_effect = PyJWTError("invalid")

        with self.assertRaises(SocialAuthError) as ctx:
            self.provider.authenticate({"id_token": "bad"})
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.code, "social_invalid_token")

    def test_authenticate_requires_id_or_code(self):
        with self.assertRaises(SocialAuthError) as ctx:
            self.provider.authenticate({})
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.code, "social_bad_request")

    @patch("jb_drf_auth.providers.oidc.jwt.decode")
    @patch("jb_drf_auth.providers.oidc.jwt.PyJWKClient")
    @patch("jb_drf_auth.providers.oidc.urlopen")
    def test_authenticate_with_authorization_code_success(self, urlopen_mock, pyjwk_cls, jwt_decode):
        response = MagicMock()
        response.read.return_value = b'{"id_token":"from-code"}'
        urlopen_mock.return_value.__enter__.return_value = response
        pyjwk_cls.return_value.get_signing_key_from_jwt.return_value.key = "public-key"
        jwt_decode.return_value = {"sub": "sub-1"}

        identity = self.provider.authenticate(
            {
                "authorization_code": "auth-code",
                "redirect_uri": "https://app/callback",
                "code_verifier": "pkce",
                "client_id": "google-web-client-id",
            }
        )
        self.assertEqual(identity.provider_user_id, "sub-1")


class FacebookProviderTests(unittest.TestCase):
    def test_missing_access_token_raises_400(self):
        provider = FacebookOAuthProvider(provider="facebook", provider_settings={})
        with self.assertRaises(SocialAuthError) as ctx:
            provider.authenticate({})
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.code, "social_bad_request")

    def test_authenticate_success(self):
        provider = FacebookOAuthProvider(provider="facebook", provider_settings={})
        with patch.object(
            provider,
            "_read_json",
            return_value={
                "id": "fb-1",
                "email": "user@example.com",
                "first_name": "Joel",
                "last_name": "Barron",
                "picture": {"data": {"url": "https://img.example/fb.jpg"}},
            },
        ):
            identity = provider.authenticate({"access_token": "token"})
        self.assertEqual(identity.provider_user_id, "fb-1")
        self.assertEqual(identity.email, "user@example.com")
        self.assertEqual(identity.email_verified, True)

    def test_debug_token_app_id_mismatch_raises_401(self):
        provider = FacebookOAuthProvider(
            provider="facebook",
            provider_settings={"APP_ID": "123", "APP_SECRET": "secret"},
        )
        with patch.object(
            provider,
            "_read_json",
            return_value={"data": {"is_valid": True, "app_id": "999"}},
        ):
            with self.assertRaises(SocialAuthError) as ctx:
                provider.authenticate({"access_token": "token"})
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.code, "social_invalid_token")
