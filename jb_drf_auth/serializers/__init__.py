from jb_drf_auth.serializers.device import DevicePayloadSerializer, DeviceSerializer
from jb_drf_auth.serializers.email_confirmation import (
    EmailConfirmationSerializer,
    ResendConfirmationEmailSerializer,
)
from jb_drf_auth.serializers.login import BasicLoginSerializer, SwitchProfileSerializer
from jb_drf_auth.serializers.otp import OtpCodeRequestSerializer, OtpCodeVerifySerializer
from jb_drf_auth.serializers.password_reset import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from jb_drf_auth.serializers.profile import ProfilePictureUpdateSerializer, ProfileSerializer
from jb_drf_auth.serializers.register import RegisterSerializer
from jb_drf_auth.serializers.social_auth import (
    SocialLinkSerializer,
    SocialLoginSerializer,
    SocialUnlinkSerializer,
)
from jb_drf_auth.serializers.user import UserSerializer
from jb_drf_auth.serializers.user_admin import UserAdminCreateSerializer
from jb_drf_auth.serializers.user_update import UserUpdateSerializer

__all__ = [
    "DevicePayloadSerializer",
    "DeviceSerializer",
    "EmailConfirmationSerializer",
    "ResendConfirmationEmailSerializer",
    "BasicLoginSerializer",
    "SwitchProfileSerializer",
    "OtpCodeRequestSerializer",
    "OtpCodeVerifySerializer",
    "PasswordChangeSerializer",
    "PasswordResetConfirmSerializer",
    "PasswordResetRequestSerializer",
    "ProfileSerializer",
    "ProfilePictureUpdateSerializer",
    "RegisterSerializer",
    "SocialLoginSerializer",
    "SocialLinkSerializer",
    "SocialUnlinkSerializer",
    "UserSerializer",
    "UserUpdateSerializer",
    "UserAdminCreateSerializer",
]
