"""Auth urls."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from jb_drf_auth.views import (
    AccountConfirmEmailView,
    AccountUpdateView,
    BasicLoginView,
    CreateStaffUserView,
    CreateSuperUserView,
    MeView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileViewSet,
    RegisterView,
    RequestOtpCodeView,
    ResendConfirmationEmailView,
    SwitchProfileView,
    VerifyOtpCodeView,
    delete_account,
)

router = DefaultRouter()
router.register(r"profiles", ProfileViewSet, basename="profiles")

urlpatterns = [
    path("admin/create-superuser/", CreateSuperUserView.as_view(), name="create_superuser"),
    path("admin/create-staff/", CreateStaffUserView.as_view(), name="create_staff"),
    path("register/", RegisterView.as_view()),
    path("registration/account-confirmation-email/", AccountConfirmEmailView.as_view()),
    path(
        "registration/account-confirmation-email/resend/",
        ResendConfirmationEmailView.as_view(),
    ),
    path("password-reset/request/", PasswordResetRequestView.as_view()),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view()),
    path("password-reset/change/", PasswordChangeView.as_view()),
    path("login/basic/", BasicLoginView.as_view()),
    path("otp/request/", RequestOtpCodeView.as_view()),
    path("otp/verify/", VerifyOtpCodeView.as_view()),
    path("profile/switch/", SwitchProfileView.as_view()),
    path("me/", MeView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("account/update/", AccountUpdateView.as_view()),
    path("account/delete/", delete_account),
    path("", include(router.urls)),
]
