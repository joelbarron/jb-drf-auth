import os
import unittest
from io import BytesIO
from unittest.mock import patch

import django
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth import utils
from jb_drf_auth.image_utils import optimize_profile_picture


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

    @patch("jb_drf_auth.image_utils.get_setting")
    def test_optimize_profile_picture_returns_same_file_when_disabled(self, mock_get_setting):
        mock_get_setting.side_effect = lambda name: {
            "PROFILE_PICTURE_OPTIMIZE": False,
        }.get(name)

        payload = SimpleUploadedFile("avatar.png", b"abc", content_type="image/png")
        result = optimize_profile_picture(payload)
        self.assertIs(result, payload)

    @patch("jb_drf_auth.image_utils.get_setting")
    def test_optimize_profile_picture_compresses_large_image(self, mock_get_setting):
        mock_get_setting.side_effect = lambda name: {
            "PROFILE_PICTURE_OPTIMIZE": True,
            "PROFILE_PICTURE_MAX_BYTES": 100000,
            "PROFILE_PICTURE_MAX_WIDTH": 256,
            "PROFILE_PICTURE_MAX_HEIGHT": 256,
            "PROFILE_PICTURE_JPEG_QUALITY": 85,
            "PROFILE_PICTURE_MIN_JPEG_QUALITY": 60,
        }.get(name)

        image = Image.effect_noise((2000, 2000), 100).convert("RGB")
        stream = BytesIO()
        image.save(stream, format="PNG")
        raw = stream.getvalue()
        payload = SimpleUploadedFile("avatar.png", raw, content_type="image/png")

        result = optimize_profile_picture(payload)
        self.assertTrue(result.name.endswith(".jpg"))
        self.assertLess(len(result.read()), len(raw))
