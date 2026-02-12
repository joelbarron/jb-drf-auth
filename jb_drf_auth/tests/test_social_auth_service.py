import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.providers.base import SocialIdentity
from jb_drf_auth.services.social_auth import SocialAuthService


class SocialAuthServiceTests(unittest.TestCase):
    @patch("jb_drf_auth.services.social_auth.get_social_settings")
    @patch("jb_drf_auth.services.social_auth.get_social_account_model_cls")
    @patch("jb_drf_auth.services.social_auth.get_social_provider")
    def test_login_or_register_raises_when_auto_create_disabled(
        self,
        get_social_provider,
        get_social_account_model_cls,
        get_social_settings,
    ):
        get_social_settings.return_value = {
            "LINK_BY_EMAIL": False,
            "AUTO_CREATE_USER": False,
        }
        get_social_provider.return_value.authenticate.return_value = SocialIdentity(
            provider="google",
            provider_user_id="sub-1",
            email="user@example.com",
            email_verified=True,
        )

        qs = MagicMock()
        qs.select_related.return_value.first.return_value = None
        model_cls = MagicMock()
        model_cls.objects.filter.return_value = qs
        get_social_account_model_cls.return_value = model_cls

        with self.assertRaises(SocialAuthError) as ctx:
            SocialAuthService.login_or_register(
                provider_name="google",
                payload={"id_token": "token"},
                client="web",
                device_data=None,
            )
        self.assertEqual(ctx.exception.code, "social_account_not_linked")

    @patch("jb_drf_auth.services.social_auth.get_social_account_model_cls")
    @patch("jb_drf_auth.services.social_auth.get_social_provider")
    def test_link_account_raises_if_linked_to_another_user(
        self,
        get_social_provider,
        get_social_account_model_cls,
    ):
        user = SimpleNamespace(id=10, get_default_profile=lambda: None)
        get_social_provider.return_value.authenticate.return_value = SocialIdentity(
            provider="google",
            provider_user_id="sub-2",
        )

        existing = SimpleNamespace(user_id=99)
        qs = MagicMock()
        qs.select_related.return_value.first.return_value = existing
        model_cls = MagicMock()
        model_cls.objects.filter.return_value = qs
        get_social_account_model_cls.return_value = model_cls

        with self.assertRaises(SocialAuthError) as ctx:
            SocialAuthService.link_account(user, "google", {"id_token": "token"})
        self.assertEqual(ctx.exception.code, "social_already_linked")

    @patch("jb_drf_auth.services.social_auth.get_social_account_model_cls")
    def test_unlink_account_raises_not_found(self, get_social_account_model_cls):
        user = SimpleNamespace(id=11)
        model_cls = MagicMock()
        model_cls.objects.filter.return_value.first.return_value = None
        get_social_account_model_cls.return_value = model_cls

        with self.assertRaises(SocialAuthError) as ctx:
            SocialAuthService.unlink_account(user, "google")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.code, "social_not_found")

    @patch("jb_drf_auth.services.social_auth.urlopen")
    @patch("jb_drf_auth.services.social_auth.get_social_settings")
    def test_sync_profile_picture_skips_oversized_payload(self, get_social_settings, urlopen):
        get_social_settings.return_value = {
            "SYNC_PICTURE_ON_LOGIN": True,
            "PICTURE_DOWNLOAD_TIMEOUT_SECONDS": 5,
            "PICTURE_MAX_BYTES": 10,
            "PICTURE_ALLOWED_CONTENT_TYPES": ("image/jpeg",),
        }
        response = MagicMock()
        response.headers.get.return_value = "image/jpeg"
        response.read.return_value = b"x" * 11
        urlopen.return_value.__enter__.return_value = response

        profile = SimpleNamespace(pk=1, picture=MagicMock())
        SocialAuthService._sync_profile_picture(profile, "https://img.example/a.jpg")
        profile.picture.save.assert_not_called()
