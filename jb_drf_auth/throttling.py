from typing import Any

from rest_framework.throttling import SimpleRateThrottle

from jb_drf_auth.conf import get_setting


class JbAuthRateThrottle(SimpleRateThrottle):
    setting_key: str | None = None
    scope = "jb_auth"

    def get_rate(self):
        rates = get_setting("THROTTLE_RATES") or {}
        if not self.setting_key:
            return None
        return rates.get(self.setting_key)

    def is_throttling_enabled(self) -> bool:
        return bool(get_setting("THROTTLE_ENABLED"))

    def get_identity_key(self, request) -> str | None:
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            return f"user:{user.pk}"

        data: Any = getattr(request, "data", {}) or {}
        if not isinstance(data, dict):
            data = {}

        for field in ("email", "phone", "login", "username"):
            value = data.get(field)
            if value is not None:
                value = str(value).strip().lower()
                if value:
                    return f"{field}:{value}"

        return self.get_ident(request)


class JbAuthIPRateThrottle(JbAuthRateThrottle):
    def get_cache_key(self, request, view):
        if not self.is_throttling_enabled():
            return None
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class JbAuthIdentityRateThrottle(JbAuthRateThrottle):
    def get_cache_key(self, request, view):
        if not self.is_throttling_enabled():
            return None
        ident = self.get_identity_key(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}


class BasicLoginIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_login_ip"
    setting_key = "LOGIN_IP"


class BasicLoginIdentityThrottle(JbAuthIdentityRateThrottle):
    scope = "jb_auth_login_identity"
    setting_key = "LOGIN_IDENTITY"


class RegisterIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_register_ip"
    setting_key = "REGISTER_IP"


class RegisterIdentityThrottle(JbAuthIdentityRateThrottle):
    scope = "jb_auth_register_identity"
    setting_key = "REGISTER_IDENTITY"


class OtpRequestIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_otp_request_ip"
    setting_key = "OTP_REQUEST_IP"


class OtpRequestIdentityThrottle(JbAuthIdentityRateThrottle):
    scope = "jb_auth_otp_request_identity"
    setting_key = "OTP_REQUEST_IDENTITY"


class OtpVerifyIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_otp_verify_ip"
    setting_key = "OTP_VERIFY_IP"


class OtpVerifyIdentityThrottle(JbAuthIdentityRateThrottle):
    scope = "jb_auth_otp_verify_identity"
    setting_key = "OTP_VERIFY_IDENTITY"


class PasswordResetRequestIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_password_reset_request_ip"
    setting_key = "PASSWORD_RESET_REQUEST_IP"


class PasswordResetRequestIdentityThrottle(JbAuthIdentityRateThrottle):
    scope = "jb_auth_password_reset_request_identity"
    setting_key = "PASSWORD_RESET_REQUEST_IDENTITY"


class PasswordResetConfirmIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_password_reset_confirm_ip"
    setting_key = "PASSWORD_RESET_CONFIRM_IP"


class EmailConfirmationIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_email_confirmation_ip"
    setting_key = "EMAIL_CONFIRMATION_IP"


class ResendConfirmationEmailIPThrottle(JbAuthIPRateThrottle):
    scope = "jb_auth_email_confirmation_resend_ip"
    setting_key = "EMAIL_CONFIRMATION_RESEND_IP"


class ResendConfirmationEmailIdentityThrottle(JbAuthIdentityRateThrottle):
    scope = "jb_auth_email_confirmation_resend_identity"
    setting_key = "EMAIL_CONFIRMATION_RESEND_IDENTITY"
