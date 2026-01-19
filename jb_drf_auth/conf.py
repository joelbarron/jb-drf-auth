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
    "OTP_VALID_MINUTES": 10,
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
}

PREFIX = "JB_DRF_AUTH_"


def get_setting(name: str):
    prefixed_name = f"{PREFIX}{name}"
    if hasattr(settings, prefixed_name):
        return getattr(settings, prefixed_name)
    if hasattr(settings, name):
        return getattr(settings, name)
    return DEFAULTS.get(name)
