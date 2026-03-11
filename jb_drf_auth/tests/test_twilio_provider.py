import os
import unittest
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.providers.twilio_sms import TwilioSmsProvider


class TwilioSmsProviderTests(unittest.TestCase):
    @patch("jb_drf_auth.providers.twilio_sms.urlopen")
    @patch("jb_drf_auth.providers.twilio_sms.get_setting")
    def test_send_sms_success(self, get_setting, urlopen):
        get_setting.side_effect = lambda name: {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "auth-token",
            "TWILIO_FROM_NUMBER": "+15550000000",
            "TWILIO_MESSAGING_SERVICE_SID": None,
        }.get(name)

        response = MagicMock()
        response.read.return_value = b'{"sid":"SM123","status":"queued"}'
        urlopen.return_value.__enter__.return_value = response

        provider = TwilioSmsProvider()
        result = provider.send_sms("+15551112222", "hello")
        self.assertEqual(result["sid"], "SM123")
        args, _kwargs = urlopen.call_args
        req = args[0]
        self.assertIn("/Accounts/AC123/Messages.json", req.full_url)

    @patch("jb_drf_auth.providers.twilio_sms.get_setting")
    def test_send_sms_requires_credentials(self, get_setting):
        get_setting.return_value = None
        provider = TwilioSmsProvider()
        with self.assertRaises(RuntimeError):
            provider.send_sms("+15551112222", "hello")
