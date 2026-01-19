from django.conf import settings

DEFAULTS = {
    "PROFILE_MODEL": None,  # required: "accounts.Profile"
    "DEVICE_MODEL": None,  # required for mobile flows: "accounts.Device"
    "OTP_MODEL": None,  # required for otp flows: "accounts.OtpCode"
    "AUTHENTICATION_TYPE": "email",  # "email", "username", "both"
    "CLIENT_CHOICES": ("web", "mobile"),
    "AUTH_SINGLE_SESSION_ON_MOBILE": False,
    "FRONTEND_URL": None,
    "DEFAULT_FROM_EMAIL": None,
    "ADMIN_BOOTSTRAP_TOKEN": None,
    "OTP_LENGTH": 6,
    "OTP_TTL_SECONDS": 300,
    "OTP_MAX_ATTEMPTS": 5,
    "OTP_RESEND_COOLDOWN_SECONDS": 60,
    "PROFILE_ROLE_CHOICES": (
        ("USER", "Usuario"),
        ("COMMERCE", "Comercio"),
        ("ADMIN", "Admin"),
    ),
    "PROFILE_GENDER_CHOICES": (
        ("MALE", "Masculino"),
        ("FEMALE", "Femenino"),
        ("OTHER", "Otro"),
        ("PREFER_NOT_TO_SAY", "Prefiero no decirlo"),
    ),
    "DEFAULT_PROFILE_ROLE": "USER",
    "PROFILE_ID_CLAIM": "profile_id",
    "PROFILE_PICTURE_UPLOAD_TO": "uploads/users/profile-pictures",
    "SMS_PROVIDER": "jb_drf_auth.providers.aws_sns.AwsSnsSmsProvider",
    "SMS_SENDER_ID": None,
    "SMS_TYPE": "Transactional",
    "SMS_OTP_MESSAGE": "Tu codigo es {code}. Expira en {minutes} minutos.",
    "SMS_LOG_MODEL": None,  # optional: "accounts.SmsLog"
    "PHONE_DEFAULT_COUNTRY_CODE": None,
    "PHONE_MIN_LENGTH": 10,
    "PHONE_MAX_LENGTH": 15,
}

PREFIX = "JB_DRF_AUTH_"
ROOT_SETTING = "JB_DRF_AUTH"


def get_setting(name: str):
    root = getattr(settings, ROOT_SETTING, None)
    if isinstance(root, dict) and name in root:
        return root[name]
    prefixed_name = f"{PREFIX}{name}"
    if hasattr(settings, prefixed_name):
        return getattr(settings, prefixed_name)
    if hasattr(settings, name):
        return getattr(settings, name)
    return DEFAULTS.get(name)
