import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.services.password_reset import PasswordResetService


class PasswordResetServiceTests(unittest.TestCase):
    @patch("jb_drf_auth.services.password_reset.get_setting")
    @patch("jb_drf_auth.services.password_reset.get_email_provider")
    @patch("jb_drf_auth.services.password_reset.get_email_log_model_cls")
    @patch("jb_drf_auth.services.password_reset.render_email_template")
    @patch("jb_drf_auth.services.password_reset.User")
    def test_send_reset_email_sent_and_logged(
        self,
        user_cls,
        render_email_template,
        get_email_log_model_cls,
        get_email_provider,
        get_setting,
    ):
        user = SimpleNamespace(
            pk=1,
            email="user@example.com",
            password="pbkdf2_sha256$260000$mock$hash",
            last_login=None,
        )
        user.get_email_field_name = lambda: "email"
        user_cls.objects.get.return_value = user
        render_email_template.return_value = ("Reset", "text body", "<p>html body</p>")
        get_setting.side_effect = lambda key: {
            "EMAIL_PROVIDER": "jb_drf_auth.providers.console_email.ConsoleEmailProvider",
            "FRONTEND_URL": "http://localhost:3000",
        }.get(key)

        email_log_model = MagicMock()
        get_email_log_model_cls.return_value = email_log_model
        provider = MagicMock()
        get_email_provider.return_value = provider

        sent = PasswordResetService.send_reset_email("user@example.com", raise_on_fail=False)

        self.assertEqual(sent, True)
        provider.send_email.assert_called_once()
        email_log_model.objects.create.assert_called_once()
        self.assertEqual(email_log_model.objects.create.call_args.kwargs["status"], "sent")

    @patch("jb_drf_auth.services.password_reset.get_setting")
    @patch("jb_drf_auth.services.password_reset.get_email_log_model_cls")
    @patch("jb_drf_auth.services.password_reset.User")
    def test_send_reset_email_user_not_found_logs_failed(
        self,
        user_cls,
        get_email_log_model_cls,
        get_setting,
    ):
        does_not_exist = type("DoesNotExist", (Exception,), {})
        user_cls.DoesNotExist = does_not_exist
        user_cls.objects.get.side_effect = does_not_exist
        get_setting.side_effect = lambda key: {
            "EMAIL_PROVIDER": "jb_drf_auth.providers.console_email.ConsoleEmailProvider",
        }.get(key)

        email_log_model = MagicMock()
        get_email_log_model_cls.return_value = email_log_model

        sent = PasswordResetService.send_reset_email("missing@example.com", raise_on_fail=False)

        self.assertIsNone(sent)
        email_log_model.objects.create.assert_called_once()
        kwargs = email_log_model.objects.create.call_args.kwargs
        self.assertEqual(kwargs["to_email"], "missing@example.com")
        self.assertEqual(kwargs["status"], "failed")
        self.assertEqual(kwargs["error_message"], "user_not_found")
