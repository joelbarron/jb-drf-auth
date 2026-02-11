import os
import unittest
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth import utils


class UtilsTests(unittest.TestCase):
    @patch("jb_drf_auth.utils.get_setting")
    def test_normalize_phone_number_requires_country_code_without_default(self, mock_get_setting):
        mock_get_setting.side_effect = lambda name: {
            "PHONE_DEFAULT_COUNTRY_CODE": None,
            "PHONE_MIN_LENGTH": 10,
            "PHONE_MAX_LENGTH": 15,
        }.get(name)

        with self.assertRaises(ValueError):
            utils.normalize_phone_number("5512345678")

    @patch("jb_drf_auth.utils.get_setting")
    def test_normalize_phone_number_with_default_country_code(self, mock_get_setting):
        mock_get_setting.side_effect = lambda name: {
            "PHONE_DEFAULT_COUNTRY_CODE": "52",
            "PHONE_MIN_LENGTH": 10,
            "PHONE_MAX_LENGTH": 15,
        }.get(name)

        result = utils.normalize_phone_number("55 1234 5678")
        self.assertEqual(result, "+525512345678")

    @patch("jb_drf_auth.utils.get_setting")
    def test_get_sms_message_uses_ascii_fallback(self, mock_get_setting):
        mock_get_setting.return_value = "Tu codigo es {code}. Expira en {minutes} minutos."
        result = utils.get_sms_message(code="123456", minutes=5)
        self.assertEqual(result, "Tu codigo es 123456. Expira en 5 minutos.")

    @patch("jb_drf_auth.utils.get_setting")
    def test_get_sms_message_allows_custom_ascii_template(self, mock_get_setting):
        mock_get_setting.return_value = "Code {code} expires in {minutes} min"
        result = utils.get_sms_message(code="987654", minutes=10)
        self.assertEqual(result, "Code 987654 expires in 10 min")
