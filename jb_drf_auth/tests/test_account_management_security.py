import os
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from rest_framework import serializers, status
from rest_framework.test import APIRequestFactory, force_authenticate

from jb_drf_auth.serializers.user_update import validate_contact_change_proofs
from jb_drf_auth.views.account_management import AccountSocialAccountsView


class DummyUser:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.pk = self.id
        self.email = kwargs.get("email", "user@example.com")
        self.phone = kwargs.get("phone", "+5215512345678")
        self.is_authenticated = kwargs.get("is_authenticated", True)


class AccountManagementSecurityTests(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = DummyUser()

    @patch("jb_drf_auth.serializers.user_update.ContactVerificationService.verify_proof_token")
    def test_validate_contact_change_proofs_requires_email_token(self, verify_proof_token):
        with self.assertRaises(serializers.ValidationError) as ctx:
            validate_contact_change_proofs(
                self.user,
                {
                    "email": "new@example.com",
                },
            )

        self.assertIn("email_verification_proof_token", ctx.exception.detail)
        verify_proof_token.assert_not_called()

    @patch("jb_drf_auth.serializers.user_update.ContactVerificationService.verify_proof_token")
    def test_validate_contact_change_proofs_requires_phone_token(self, verify_proof_token):
        with self.assertRaises(serializers.ValidationError) as ctx:
            validate_contact_change_proofs(
                self.user,
                {
                    "phone": "+5215544444444",
                },
            )

        self.assertIn("phone_verification_proof_token", ctx.exception.detail)
        verify_proof_token.assert_not_called()

    @patch("jb_drf_auth.serializers.user_update.ContactVerificationService.verify_proof_token")
    def test_validate_contact_change_proofs_calls_verify_for_changed_values(self, verify_proof_token):
        validate_contact_change_proofs(
            self.user,
            {
                "email": "new@example.com",
                "phone": "+5215544444444",
                "email_verification_proof_token": "email-token",
                "phone_verification_proof_token": "phone-token",
            },
        )

        self.assertEqual(verify_proof_token.call_count, 2)
        verify_proof_token.assert_any_call(
            "email-token",
            user_id=self.user.pk,
            channel="email",
            email="new@example.com",
        )
        verify_proof_token.assert_any_call(
            "phone-token",
            user_id=self.user.pk,
            channel="sms",
            phone="+5215544444444",
        )

    @patch("jb_drf_auth.serializers.user_update.ContactVerificationService.verify_proof_token")
    def test_validate_contact_change_proofs_skips_when_values_unchanged(self, verify_proof_token):
        validate_contact_change_proofs(
            self.user,
            {
                "email": self.user.email,
                "phone": self.user.phone,
            },
        )
        verify_proof_token.assert_not_called()

    @patch("jb_drf_auth.views.account_management.get_social_account_model_cls")
    def test_account_social_accounts_view_returns_user_accounts(self, get_social_account_model_cls):
        first = SimpleNamespace(
            provider="google",
            email="user@example.com",
            email_verified=True,
            created=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc),
            last_login_at=None,
            picture_url="https://example.com/avatar.png",
        )
        second = SimpleNamespace(
            provider="facebook",
            email="user@example.com",
            email_verified=False,
            created=datetime(2026, 3, 9, 10, 0, tzinfo=timezone.utc),
            last_login_at=datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
            picture_url=None,
        )

        model_cls = MagicMock()
        queryset = MagicMock()
        queryset.order_by.return_value = [first, second]
        model_cls.objects.filter.return_value = queryset
        get_social_account_model_cls.return_value = model_cls

        request = self.factory.get("/auth/account/social-accounts/")
        force_authenticate(request, user=self.user)
        response = AccountSocialAccountsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["provider"], "google")
        self.assertIn("linked_at", response.data[0])
        model_cls.objects.filter.assert_called_once_with(user=self.user)


if __name__ == "__main__":
    unittest.main()
