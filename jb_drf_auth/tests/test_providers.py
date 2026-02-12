import os
import unittest
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from jb_drf_auth.providers.aws_sns import AwsSnsSmsProvider
from jb_drf_auth.providers.console_sms import ConsoleSmsProvider
from jb_drf_auth.providers.django_email import DjangoEmailProvider


class AwsSnsProviderTests(unittest.TestCase):
    @patch("jb_drf_auth.providers.aws_sns.get_setting")
    @patch("jb_drf_auth.providers.aws_sns.boto3.client")
    def test_send_sms_with_sender_id(self, boto_client, get_setting):
        get_setting.side_effect = lambda name: {
            "SMS_TYPE": "Transactional",
            "SMS_SENDER_ID": "MyBrand",
        }.get(name)
        client = MagicMock()
        boto_client.return_value = client
        provider = AwsSnsSmsProvider()

        provider.send_sms("+15551112222", "hello")
        client.publish.assert_called_once()
        kwargs = client.publish.call_args.kwargs
        self.assertEqual(kwargs["PhoneNumber"], "+15551112222")
        self.assertEqual(kwargs["Message"], "hello")
        self.assertIn("AWS.SNS.SMS.SenderID", kwargs["MessageAttributes"])

    @patch("jb_drf_auth.providers.aws_sns.get_setting")
    @patch("jb_drf_auth.providers.aws_sns.boto3.client")
    def test_send_sms_without_sender_id(self, boto_client, get_setting):
        get_setting.side_effect = lambda name: {
            "SMS_TYPE": "Transactional",
            "SMS_SENDER_ID": None,
        }.get(name)
        client = MagicMock()
        boto_client.return_value = client
        provider = AwsSnsSmsProvider()

        provider.send_sms("+15551112222", "hello")
        kwargs = client.publish.call_args.kwargs
        self.assertNotIn("AWS.SNS.SMS.SenderID", kwargs["MessageAttributes"])


class ConsoleSmsProviderTests(unittest.TestCase):
    @patch("builtins.print")
    def test_send_sms_prints_and_returns_payload(self, print_mock):
        provider = ConsoleSmsProvider()
        response = provider.send_sms("+15551112222", "code 123")
        print_mock.assert_called_once()
        self.assertEqual(response["provider"], "console")
        self.assertEqual(response["phone_number"], "+15551112222")


class DjangoEmailProviderTests(unittest.TestCase):
    @patch("jb_drf_auth.providers.django_email.get_setting")
    @patch("jb_drf_auth.providers.django_email.EmailMultiAlternatives")
    def test_send_email_with_html(self, mail_cls, get_setting):
        get_setting.return_value = "no-reply@example.com"
        message = MagicMock()
        mail_cls.return_value = message

        provider = DjangoEmailProvider()
        provider.send_email("user@example.com", "Hi", "text body", "<p>html body</p>")

        mail_cls.assert_called_once_with(
            subject="Hi",
            body="text body",
            from_email="no-reply@example.com",
            to=["user@example.com"],
        )
        message.attach_alternative.assert_called_once_with("<p>html body</p>", "text/html")
        message.send.assert_called_once_with(fail_silently=False)

    @patch("jb_drf_auth.providers.django_email.get_setting")
    @patch("jb_drf_auth.providers.django_email.EmailMultiAlternatives")
    def test_send_email_without_html(self, mail_cls, get_setting):
        get_setting.return_value = "no-reply@example.com"
        message = MagicMock()
        mail_cls.return_value = message

        provider = DjangoEmailProvider()
        provider.send_email("user@example.com", "Hi", "text body", None)

        message.attach_alternative.assert_not_called()
        message.send.assert_called_once_with(fail_silently=False)
