from importlib import import_module

from jb_drf_auth.conf import get_setting

CLIENT_CHOICES = get_setting("CLIENT_CHOICES")

_SERVICE_EXPORTS = {
    "ClientService": "jb_drf_auth.services.client",
    "ContactVerificationService": "jb_drf_auth.services.contact_verification",
    "EmailConfirmationService": "jb_drf_auth.services.email_confirmation",
    "LoginService": "jb_drf_auth.services.login",
    "MagicLinkService": "jb_drf_auth.services.magic_link",
    "MeService": "jb_drf_auth.services.me",
    "NotificationService": "jb_drf_auth.services.notification",
    "NotificationDispatchService": "jb_drf_auth.services.notification_dispatch",
    "OtpService": "jb_drf_auth.services.otp",
    "PasswordResetService": "jb_drf_auth.services.password_reset",
    "ProfileRoleMirrorService": "jb_drf_auth.services.profile_mirror",
    "RegisterService": "jb_drf_auth.services.register",
    "SocialAuthService": "jb_drf_auth.services.social_auth",
    "TokensService": "jb_drf_auth.services.tokens",
    "UserSettingsService": "jb_drf_auth.services.user_settings",
}

__all__ = [
    "CLIENT_CHOICES",
    *_SERVICE_EXPORTS.keys(),
]


def __getattr__(name):
    module_path = _SERVICE_EXPORTS.get(name)
    if not module_path:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_path)
    value = getattr(module, name)
    globals()[name] = value
    return value
