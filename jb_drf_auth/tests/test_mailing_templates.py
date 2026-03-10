import os
import unittest

import django
from django.test import override_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.utils import get_mailing_settings, render_email_template


LOC_MEM_TEMPLATES = {
    "mailing/custom.txt": "Hola {{ user_email }}",
    "mailing/custom.html": "<p>Hola {{ user_email }}</p>",
}

BASE_TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [],
            "loaders": [
                (
                    "django.template.loaders.locmem.Loader",
                    LOC_MEM_TEMPLATES,
                ),
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]


class MailingTemplateTests(unittest.TestCase):
    @override_settings(
        TEMPLATES=BASE_TEMPLATES,
        JB_DRF_AUTH={
            "PROFILE_MODEL": "auth.User",
            "DEVICE_MODEL": "auth.User",
            "OTP_MODEL": "auth.User",
            "SMS_LOG_MODEL": "auth.User",
            "EMAIL_LOG_MODEL": "auth.User",
            "MAILING": {
                "brand": {"app_name": "RootApp"},
            },
        },
        MAILING={
            "brand": {"app_name": "GlobalApp"},
        },
    )
    def test_mailing_settings_precedence(self):
        mailing = get_mailing_settings()
        self.assertEqual(mailing["brand"]["app_name"], "GlobalApp")

    @override_settings(
        TEMPLATES=BASE_TEMPLATES,
        MAILING={
            "templates": {
                "custom_template": {
                    "subject": "Asunto {user_email}",
                    "text_template": "mailing/custom.txt",
                    "html_template": "mailing/custom.html",
                }
            }
        },
    )
    def test_render_template_from_file_paths(self):
        subject, text_body, html_body = render_email_template(
            "custom_template",
            {"user_email": "test@example.com"},
        )

        self.assertEqual(subject, "Asunto test@example.com")
        self.assertIn("test@example.com", text_body)
        self.assertIn("test@example.com", html_body)

    @override_settings(
        TEMPLATES=BASE_TEMPLATES,
        JB_DRF_AUTH={
            "PROFILE_MODEL": "auth.User",
            "DEVICE_MODEL": "auth.User",
            "OTP_MODEL": "auth.User",
            "SMS_LOG_MODEL": "auth.User",
            "EMAIL_LOG_MODEL": "auth.User",
            "EMAIL_TEMPLATES": {
                "legacy_inline": {
                    "subject": "Legacy",
                    "text": "Hola {user_email}",
                    "html": "<b>{user_email}</b>",
                }
            },
        },
    )
    def test_render_legacy_inline_template(self):
        subject, text_body, html_body = render_email_template(
            "legacy_inline",
            {"user_email": "legacy@example.com"},
        )

        self.assertEqual(subject, "Legacy")
        self.assertEqual(text_body, "Hola legacy@example.com")
        self.assertEqual(html_body, "<b>legacy@example.com</b>")

    @override_settings(
        TEMPLATES=BASE_TEMPLATES,
        MAILING={
            "brand": {
                "app_name": "Mentalysis",
                "company_name": "MENTALYSIS SAPI DE CV",
            },
            "links": {
                "privacy_url": "https://mentalysis.mx/privacy-policy/",
                "unsubscribe_url": "https://app.mentalysis.mx/",
            },
            "assets": {
                "logo_url": "https://example.com/logo.png",
                "logo_alt": "Mentalysis",
            },
        },
    )
    def test_default_auth_templates_render_non_empty_text_and_html(self):
        subject, text_body, html_body = render_email_template(
            "email_confirmation",
            {
                "user_email": "user@example.com",
                "verify_url": "https://app.mentalysis.mx/verify-email/?token=abc",
            },
        )

        self.assertTrue(subject)
        self.assertTrue(text_body)
        self.assertTrue(html_body)
        self.assertIn("verify-email", text_body)
        self.assertIn("verify-email", html_body)


if __name__ == "__main__":
    unittest.main()
