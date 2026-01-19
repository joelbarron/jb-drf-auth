from jb_drf_auth.views.account_management import delete_account
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
from jb_drf_auth.views.profile import ProfileViewSet
from jb_drf_auth.views.register import RegisterView
from jb_drf_auth.views.user_admin import CreateStaffUserView, CreateSuperUserView

__all__ = [
    "delete_account",
    "AccountConfirmEmailView",
    "ResendConfirmationEmailView",
    "BasicLoginView",
    "SwitchProfileView",
    "MeView",
    "RequestOtpCodeView",
    "VerifyOtpCodeView",
    "PasswordChangeView",
    "PasswordResetConfirmView",
    "PasswordResetRequestView",
    "ProfileViewSet",
    "RegisterView",
    "CreateStaffUserView",
    "CreateSuperUserView",
]
