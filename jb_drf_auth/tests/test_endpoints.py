import os
import unittest
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jb_drf_auth.tests.settings")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from jb_drf_auth.exceptions import SocialAuthError
from jb_drf_auth.views.account_management import AccountUpdateView, delete_account
from jb_drf_auth.views.email_confirmation import (
    AccountConfirmEmailView,
    ResendConfirmationEmailView,
)
from jb_drf_auth.views.login import BasicLoginView, SwitchProfileView
from jb_drf_auth.views.me import MeView
from jb_drf_auth.views.otp import RequestOtpCodeView, VerifyOtpCodeView
from jb_drf_auth.views.password_reset import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)
from jb_drf_auth.views.profile import ProfilePictureUpdateView, ProfileViewSet
from jb_drf_auth.views.register import RegisterView
from jb_drf_auth.views.social_auth import SocialLinkView, SocialLoginView, SocialUnlinkView
from jb_drf_auth.views.user_admin import CreateStaffUserView, CreateSuperUserView


class DummyUser:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.pk = self.id
        self.email = kwargs.get("email", "user@example.com")
        self.username = kwargs.get("username", "user")
        self.is_superuser = kwargs.get("is_superuser", False)
        self.is_staff = kwargs.get("is_staff", False)
        self.is_active = kwargs.get("is_active", True)
        self.is_authenticated = kwargs.get("is_authenticated", True)
        self.is_verified = kwargs.get("is_verified", True)
        self.deleted = kwargs.get("deleted", None)
        self.deleted_called = False

    def delete(self):
        self.deleted_called = True


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = DummyUser()

    @patch("jb_drf_auth.services.login.LoginService.basic_login")
    def test_basic_login_view_success(self, basic_login):
        basic_login.return_value = {"accessToken": "a", "refreshToken": "b"}

        request = self.factory.post(
            "/auth/login/basic/",
            {"login": "u", "password": "p", "client": "web"},
            format="json",
        )
        response = BasicLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.throttling.BasicLoginIPThrottle.wait", return_value=60)
    @patch("jb_drf_auth.throttling.BasicLoginIPThrottle.allow_request", return_value=False)
    def test_basic_login_view_throttled(self, _allow_request, _wait):
        request = self.factory.post("/auth/login/basic/", {"login": "u", "password": "p"}, format="json")
        response = BasicLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("jb_drf_auth.services.login.ClientService.response_for_client")
    @patch("jb_drf_auth.services.login.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.login.EmailOrUsernameModelBackend.authenticate")
    def test_basic_login_web_ignores_device(self, authenticate, get_tokens_for_user, response_for_client):
        user = DummyUser()
        user.get_default_profile = MagicMock(return_value=MagicMock())
        authenticate.return_value = user
        get_tokens_for_user.return_value = {"access": "x", "refresh": "y"}
        response_for_client.return_value = {"ok": True}

        request = self.factory.post(
            "/auth/login/basic/",
            {
                "login": "u",
                "password": "p",
                "client": "web",
                "device": {"platform": "ios", "name": "iPhone", "token": "t"},
            },
            format="json",
        )
        response = BasicLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        args, _kwargs = response_for_client.call_args
        self.assertEqual(args[0], "web")
        self.assertIsNone(args[4])

    @patch("jb_drf_auth.services.client.MeService.get_me_mobile")
    @patch("jb_drf_auth.services.client.get_device_model_cls")
    @patch("jb_drf_auth.services.login.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.login.EmailOrUsernameModelBackend.authenticate")
    def test_basic_login_mobile_requires_notification_token(
        self,
        authenticate,
        get_tokens_for_user,
        get_device_model_cls,
        get_me_mobile,
    ):
        user = DummyUser()
        user.get_default_profile = MagicMock(return_value=MagicMock())
        authenticate.return_value = user
        get_tokens_for_user.return_value = {"access": "x", "refresh": "y"}
        get_device_model_cls.return_value = MagicMock()
        get_me_mobile.return_value = {"ok": True}

        request = self.factory.post(
            "/auth/login/basic/",
            {
                "login": "u",
                "password": "p",
                "client": "mobile",
                "device": {"platform": "ios", "name": "iPhone", "token": "t"},
            },
            format="json",
        )
        response = BasicLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("device", response.data)

    @patch("jb_drf_auth.services.client.MeService.get_me_mobile")
    @patch("jb_drf_auth.services.client.get_device_model_cls")
    @patch("jb_drf_auth.services.login.TokensService.get_tokens_for_user")
    @patch("jb_drf_auth.services.login.EmailOrUsernameModelBackend.authenticate")
    def test_basic_login_mobile_registers_notification_token(
        self,
        authenticate,
        get_tokens_for_user,
        get_device_model_cls,
        get_me_mobile,
    ):
        user = DummyUser()
        user.get_default_profile = MagicMock(return_value=MagicMock())
        authenticate.return_value = user
        get_tokens_for_user.return_value = {"access": "x", "refresh": "y"}
        device_model = MagicMock()
        get_device_model_cls.return_value = device_model
        get_me_mobile.return_value = {"ok": True}

        request = self.factory.post(
            "/auth/login/basic/",
            {
                "login": "u",
                "password": "p",
                "client": "mobile",
                "device": {
                    "platform": "ios",
                    "name": "iPhone",
                    "token": "t",
                    "notification_token": "push-123",
                },
            },
            format="json",
        )
        response = BasicLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("device_registered"), True)
        device_model.objects.update_or_create.assert_called_once_with(
            user=user,
            token="t",
            defaults={
                "platform": "ios",
                "name": "iPhone",
                "notification_token": "push-123",
            },
        )

    @patch("jb_drf_auth.views.login.SwitchProfileSerializer")
    @patch("jb_drf_auth.views.login.LoginService.switch_profile")
    def test_switch_profile_view_success(self, switch_profile, serializer_cls):
        serializer = MagicMock()
        serializer.validated_data = {"profile": 2, "client": "web"}
        serializer_cls.return_value = serializer
        switch_profile.return_value = {"ok": True}

        request = self.factory.post("/auth/profile/switch/", {"profile": 2, "client": "web"}, format="json")
        force_authenticate(request, user=self.user)
        response = SwitchProfileView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.views.profile.ProfilePictureUpdateSerializer")
    def test_profile_picture_update_view_success(self, serializer_cls):
        serializer = MagicMock()
        serializer.save.return_value = MagicMock(id=11)
        serializer_cls.return_value = serializer

        request = self.factory.patch("/auth/profile/picture/", {"picture": "x"}, format="json")
        force_authenticate(request, user=self.user)
        response = ProfilePictureUpdateView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("profile_id"), 11)

    @patch("jb_drf_auth.services.social_auth.SocialAuthService.login_or_register")
    def test_social_login_view_success(self, login_or_register):
        login_or_register.return_value = {"accessToken": "a", "refreshToken": "b"}
        request = self.factory.post(
            "/auth/login/social/",
            {
                "provider": "google",
                "id_token": "token",
                "client": "web",
            },
            format="json",
        )
        response = SocialLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.services.social_auth.SocialAuthService.login_or_register")
    def test_social_login_view_forwards_role(self, login_or_register):
        login_or_register.return_value = {"accessToken": "a", "refreshToken": "b"}
        request = self.factory.post(
            "/auth/login/social/",
            {
                "provider": "google",
                "id_token": "token",
                "client": "web",
                "role": "DOCTOR",
            },
            format="json",
        )
        response = SocialLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_or_register.call_args.kwargs.get("role"), "DOCTOR")

    @patch("jb_drf_auth.services.social_auth.SocialAuthService.login_or_register")
    def test_social_login_view_returns_401_for_invalid_token(self, login_or_register):
        login_or_register.side_effect = SocialAuthError(
            "Social token is invalid or expired.",
            status_code=401,
            code="social_invalid_token",
        )
        request = self.factory.post(
            "/auth/login/social/",
            {
                "provider": "google",
                "id_token": "token",
                "client": "web",
            },
            format="json",
        )
        response = SocialLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("code"), "social_invalid_token")

    @patch("jb_drf_auth.services.social_auth.SocialAuthService.link_account")
    def test_social_link_view_success(self, link_account):
        link_account.return_value = {"detail": "ok", "provider": "google"}
        request = self.factory.post(
            "/auth/login/social/link/",
            {"provider": "google", "id_token": "token"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = SocialLinkView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.services.social_auth.SocialAuthService.unlink_account")
    def test_social_unlink_view_success(self, unlink_account):
        unlink_account.return_value = {"detail": "ok", "provider": "google"}
        request = self.factory.post(
            "/auth/login/social/unlink/",
            {"provider": "google"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = SocialUnlinkView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_social_login_view_unsupported_provider(self):
        request = self.factory.post(
            "/auth/login/social/",
            {
                "provider": "unknown",
                "id_token": "token",
                "client": "web",
            },
            format="json",
        )
        response = SocialLoginView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("jb_drf_auth.views.register.RegisterView.get_serializer")
    def test_register_view_created_email_sent(self, get_serializer):
        serializer = MagicMock()
        serializer.email_sent = True
        get_serializer.return_value = serializer

        request = self.factory.post("/auth/register/", {}, format="json")
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("jb_drf_auth.views.register.RegisterView.get_serializer")
    def test_register_view_created_email_not_sent(self, get_serializer):
        serializer = MagicMock()
        serializer.email_sent = False
        get_serializer.return_value = serializer

        request = self.factory.post("/auth/register/", {}, format="json")
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("email_sent"), False)

    @patch("jb_drf_auth.views.register.RegisterView.get_serializer")
    def test_register_view_value_error(self, get_serializer):
        get_serializer.side_effect = ValueError("bad input")
        request = self.factory.post("/auth/register/", {}, format="json")
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("jb_drf_auth.views.otp.OtpCodeRequestSerializer")
    @patch("jb_drf_auth.views.otp.OtpService.request_otp_code")
    def test_request_otp_code_view_success(self, request_otp_code, serializer_cls):
        serializer = MagicMock()
        serializer.validated_data = {"channel": "sms", "phone": "+525512345678"}
        serializer_cls.return_value = serializer
        request_otp_code.return_value = {"detail": "ok"}

        request = self.factory.post("/auth/otp/request/", {}, format="json")
        response = RequestOtpCodeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("jb_drf_auth.throttling.OtpRequestIPThrottle.wait", return_value=60)
    @patch("jb_drf_auth.throttling.OtpRequestIPThrottle.allow_request", return_value=False)
    def test_request_otp_code_view_throttled(self, _allow_request, _wait):
        request = self.factory.post("/auth/otp/request/", {}, format="json")
        response = RequestOtpCodeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("jb_drf_auth.views.otp.OtpCodeVerifySerializer")
    @patch("jb_drf_auth.views.otp.OtpService.verify_otp_code")
    def test_verify_otp_code_view_success(self, verify_otp_code, serializer_cls):
        serializer = MagicMock()
        serializer.validated_data = {"code": "123456", "client": "web"}
        serializer_cls.return_value = serializer
        verify_otp_code.return_value = {"detail": "ok"}

        request = self.factory.post("/auth/otp/verify/", {}, format="json")
        response = VerifyOtpCodeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.views.otp.OtpCodeVerifySerializer")
    @patch("jb_drf_auth.views.otp.OtpService.verify_otp_code")
    def test_verify_otp_code_view_forwards_role(self, verify_otp_code, serializer_cls):
        serializer = MagicMock()
        serializer.validated_data = {"code": "123456", "client": "web", "role": "DOCTOR"}
        serializer_cls.return_value = serializer
        verify_otp_code.return_value = {"detail": "ok"}

        request = self.factory.post("/auth/otp/verify/", {}, format="json")
        response = VerifyOtpCodeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        verify_otp_code.assert_called_once_with(serializer.validated_data)

    @patch("jb_drf_auth.views.password_reset.PasswordResetRequestSerializer")
    def test_password_reset_request_view_email_sent(self, serializer_cls):
        serializer = MagicMock()
        serializer.save.return_value = True
        serializer_cls.return_value = serializer

        request = self.factory.post("/auth/password-reset/request/", {}, format="json")
        response = PasswordResetRequestView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email_sent"), True)

    @patch("jb_drf_auth.views.password_reset.PasswordResetRequestSerializer")
    def test_password_reset_request_view_email_not_sent(self, serializer_cls):
        serializer = MagicMock()
        serializer.save.return_value = False
        serializer_cls.return_value = serializer

        request = self.factory.post("/auth/password-reset/request/", {}, format="json")
        response = PasswordResetRequestView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email_sent"), False)

    @patch("jb_drf_auth.views.password_reset.PasswordResetConfirmSerializer")
    def test_password_reset_confirm_view_success(self, serializer_cls):
        serializer = MagicMock()
        serializer_cls.return_value = serializer
        request = self.factory.post("/auth/password-reset/confirm/", {}, format="json")
        response = PasswordResetConfirmView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.views.password_reset.PasswordChangeSerializer")
    def test_password_change_view_success(self, serializer_cls):
        serializer = MagicMock()
        serializer_cls.return_value = serializer
        request = self.factory.post("/auth/password-reset/change/", {}, format="json")
        force_authenticate(request, user=self.user)
        response = PasswordChangeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.views.email_confirmation.EmailConfirmationSerializer")
    def test_account_confirm_email_view_success(self, serializer_cls):
        serializer = MagicMock()
        serializer.is_valid.return_value = True
        serializer_cls.return_value = serializer

        request = self.factory.post("/auth/registration/account-confirmation-email/", {}, format="json")
        response = AccountConfirmEmailView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("jb_drf_auth.views.email_confirmation.EmailConfirmationSerializer")
    def test_account_confirm_email_view_bad_request(self, serializer_cls):
        serializer = MagicMock()
        serializer.is_valid.return_value = False
        serializer.errors = {"token": ["invalid"]}
        serializer_cls.return_value = serializer

        request = self.factory.post("/auth/registration/account-confirmation-email/", {}, format="json")
        response = AccountConfirmEmailView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("jb_drf_auth.views.email_confirmation.ResendConfirmationEmailSerializer")
    def test_resend_confirmation_email_view_success(self, serializer_cls):
        serializer = MagicMock()
        serializer.is_valid.return_value = True
        serializer.save.return_value = True
        serializer_cls.return_value = serializer

        request = self.factory.post(
            "/auth/registration/account-confirmation-email/resend/",
            {},
            format="json",
        )
        response = ResendConfirmationEmailView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email_sent"), True)

    @patch("jb_drf_auth.views.email_confirmation.ResendConfirmationEmailSerializer")
    def test_resend_confirmation_email_view_not_sent(self, serializer_cls):
        serializer = MagicMock()
        serializer.is_valid.return_value = True
        serializer.save.return_value = False
        serializer_cls.return_value = serializer

        request = self.factory.post(
            "/auth/registration/account-confirmation-email/resend/",
            {},
            format="json",
        )
        response = ResendConfirmationEmailView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email_sent"), False)

    @patch("jb_drf_auth.views.me.MeService.get_me")
    def test_me_view_success(self, get_me):
        get_me.return_value = {"ok": True}
        request = self.factory.get("/auth/me/?client=web")
        force_authenticate(request, user=self.user, token={"profile_id": 1})
        response = MeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_me_view_missing_profile_id(self):
        request = self.factory.get("/auth/me/?client=web")
        force_authenticate(request, user=self.user, token={})
        response = MeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_view_user_invalid(self):
        user = DummyUser(is_active=False)
        request = self.factory.get("/auth/me/?client=web")
        force_authenticate(request, user=user, token={"profile_id": 1})
        response = MeView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("jb_drf_auth.views.account_management.UserUpdateSerializer")
    @patch("jb_drf_auth.views.account_management.UserSerializer")
    def test_account_update_patch_success(self, user_serializer_cls, update_serializer_cls):
        update_serializer = MagicMock()
        update_serializer_cls.return_value = update_serializer
        user_serializer = MagicMock()
        user_serializer.data = {"id": 1}
        user_serializer_cls.return_value = user_serializer

        request = self.factory.patch("/auth/account/update/", {"timezone": "UTC"}, format="json")
        force_authenticate(request, user=self.user)
        response = AccountUpdateView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_account_success(self):
        request = self.factory.delete("/auth/account/delete/", {"confirmation": True}, format="json")
        force_authenticate(request, user=self.user)
        response = delete_account(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.deleted_called)

    def test_delete_account_missing_confirmation(self):
        request = self.factory.delete("/auth/account/delete/", {}, format="json")
        force_authenticate(request, user=self.user)
        response = delete_account(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("jb_drf_auth.views.user_admin.UserAdminCreateSerializer")
    @patch("jb_drf_auth.views.user_admin.get_profile_model_cls")
    @patch("jb_drf_auth.views.user_admin.User")
    def test_create_superuser_view_success(self, user_model, get_profile_model_cls, serializer_cls):
        serializer = MagicMock()
        serializer.validated_data = {"email": "admin@example.com", "password": "secret"}
        serializer_cls.return_value = serializer
        user_model.objects.filter.return_value.exists.return_value = False
        user_model.objects.create_superuser.return_value = DummyUser(
            id=9, email="admin@example.com", is_superuser=True, is_staff=True
        )
        profile_model = MagicMock()
        get_profile_model_cls.return_value = profile_model

        request = self.factory.post("/auth/admin/create-superuser/", {}, format="json")
        force_authenticate(request, user=DummyUser(is_superuser=True))
        response = CreateSuperUserView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("jb_drf_auth.views.user_admin.UserAdminCreateSerializer")
    @patch("jb_drf_auth.views.user_admin.User")
    def test_create_staff_view_conflict(self, user_model, serializer_cls):
        serializer = MagicMock()
        serializer.validated_data = {"email": "exists@example.com", "password": "secret"}
        serializer_cls.return_value = serializer
        user_model.objects.filter.return_value.exists.return_value = True

        request = self.factory.post("/auth/admin/create-staff/", {}, format="json")
        force_authenticate(request, user=DummyUser(is_superuser=True))
        response = CreateStaffUserView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @patch("jb_drf_auth.views.profile.get_profile_model_cls")
    def test_profile_viewset_queryset_filtered_by_user(self, get_profile_model_cls):
        profile_model = MagicMock()
        get_profile_model_cls.return_value = profile_model
        request = self.factory.get("/auth/profiles/")
        view = ProfileViewSet()
        view.request = request
        view.request.user = self.user
        view.get_queryset()
        profile_model.objects.filter.assert_called_once_with(user=self.user)

    def test_profile_viewset_permissions_authenticated(self):
        view = ProfileViewSet()
        permissions = view.get_permissions()
        self.assertEqual(len(permissions), 1)
