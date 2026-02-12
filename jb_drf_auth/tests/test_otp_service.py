import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.services.otp import OtpService


class OtpServiceTests(unittest.TestCase):
    @patch("jb_drf_auth.services.otp.get_setting")
    @patch("jb_drf_auth.services.otp.ClientService.response_for_client")
    @patch("jb_drf_auth.services.otp.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.otp.get_profile_model_cls")
    @patch("jb_drf_auth.services.otp.get_otp_model_cls")
    @patch("jb_drf_auth.services.otp.User")
    def test_verify_otp_code_phone_only_uses_fallback_email(
        self,
        user_cls,
        get_otp_model_cls,
        get_profile_model_cls,
        get_tokens_for_user,
        response_for_client,
        get_setting,
    ):
        get_setting.side_effect = lambda key: {
            "OTP_MAX_ATTEMPTS": 5,
            "DEFAULT_PROFILE_ROLE": "USER",
        }[key]

        otp = SimpleNamespace(
            email="",
            phone="+525512345674",
            code="123456",
            attempts=0,
            is_used=False,
            save=MagicMock(),
        )
        otp_qs = MagicMock()
        otp_qs.filter.return_value = otp_qs
        otp_qs.order_by.return_value.first.return_value = otp

        otp_model = MagicMock()
        otp_model.objects.filter.return_value = otp_qs
        get_otp_model_cls.return_value = otp_model

        user_qs = MagicMock()
        user_qs.first.return_value = None
        user_cls.objects.filter.return_value = user_qs

        created_user = MagicMock()
        created_user.is_verified = False
        created_user.get_default_profile.return_value = MagicMock()
        user_cls.objects.create_user.return_value = created_user

        profile_model = MagicMock()
        get_profile_model_cls.return_value = profile_model

        get_tokens_for_user.return_value = {"access": "a", "refresh": "b"}
        response_for_client.return_value = {"ok": True}

        result = OtpService.verify_otp_code(
            {
                "phone": "+525512345674",
                "code": "123456",
                "client": "web",
            }
        )

        self.assertEqual(result, {"ok": True})
        user_cls.objects.create_user.assert_called_once_with(
            email="phone_525512345674@otp.local",
            phone="+525512345674",
            is_active=True,
        )

