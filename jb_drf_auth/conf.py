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
    "TERMS_AND_CONDITIONS_REQUIRED": True,
    "EMAIL_PROVIDER": "jb_drf_auth.providers.django_email.DjangoEmailProvider",
    "EMAIL_LOG_MODEL": None,  # required for email flows: "authentication.EmailLog"
    "EMAIL_TEMPLATES": None,
    "ADMIN_BOOTSTRAP_TOKEN": None,
    "OTP_LENGTH": 6,
    "OTP_TTL_SECONDS": 300,
    "OTP_MAX_ATTEMPTS": 5,
    "OTP_RESEND_COOLDOWN_SECONDS": 60,
    "OTP_PHONE_EMAIL_DOMAIN": "phone.local",
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
    "PROFILE_PICTURE_OPTIMIZE": True,
    "PROFILE_PICTURE_MAX_BYTES": 1024 * 1024,
    "PROFILE_PICTURE_MAX_WIDTH": 1080,
    "PROFILE_PICTURE_MAX_HEIGHT": 1080,
    "PROFILE_PICTURE_JPEG_QUALITY": 85,
    "PROFILE_PICTURE_MIN_JPEG_QUALITY": 65,
    "PERSON_PICTURE_UPLOAD_TO": None,
    "PERSON_ID_DOCUMENTS_UPLOAD_TO": "uploads/people/id-documents",
    "SMS_PROVIDER": "jb_drf_auth.providers.aws_sns.AwsSnsSmsProvider",
    "SMS_SENDER_ID": None,
    "SMS_TYPE": "Transactional",
    "SMS_OTP_MESSAGE": "Tu codigo es {code}. Expira en {minutes} minutos.",
    "TWILIO_ACCOUNT_SID": None,
    "TWILIO_AUTH_TOKEN": None,
    "TWILIO_FROM_NUMBER": None,
    "TWILIO_MESSAGING_SERVICE_SID": None,
    "SMS_LOG_MODEL": None,  # optional: "accounts.SmsLog"
    "PHONE_DEFAULT_COUNTRY_CODE": None,
    "PHONE_MIN_LENGTH": 10,
    "PHONE_MAX_LENGTH": 15,
    "THROTTLE_ENABLED": True,
    "THROTTLE_RATES": {
        "LOGIN_IP": "20/min",
        "LOGIN_IDENTITY": "10/min",
        "REGISTER_IP": "10/hour",
        "REGISTER_IDENTITY": "5/hour",
        "OTP_REQUEST_IP": "20/hour",
        "OTP_REQUEST_IDENTITY": "30/hour",
        "OTP_VERIFY_IP": "30/hour",
        "OTP_VERIFY_IDENTITY": "60/hour",
        "PASSWORD_RESET_REQUEST_IP": "15/hour",
        "PASSWORD_RESET_REQUEST_IDENTITY": "5/hour",
        "PASSWORD_RESET_CONFIRM_IP": "30/hour",
        "EMAIL_CONFIRMATION_IP": "30/hour",
        "EMAIL_CONFIRMATION_RESEND_IP": "10/hour",
        "EMAIL_CONFIRMATION_RESEND_IDENTITY": "5/hour",
    },
    "SOCIAL_ACCOUNT_MODEL": None,  # required for social login: "authentication.SocialAccount"
    "SOCIAL": {
        "AUTO_CREATE_USER": True,
        "LINK_BY_EMAIL": True,
        "REQUIRE_VERIFIED_EMAIL": True,
        "SYNC_PICTURE_ON_LOGIN": True,
        "PICTURE_DOWNLOAD_TIMEOUT_SECONDS": 5,
        "PICTURE_MAX_BYTES": 5 * 1024 * 1024,
        "PICTURE_ALLOWED_CONTENT_TYPES": ("image/jpeg", "image/png", "image/webp"),
        "PROVIDERS": {
            "google": {
                "CLASS": "jb_drf_auth.providers.google_oidc.GoogleOidcProvider",
                "CLIENT_IDS": (),
                "CLIENT_SECRET": None,
                "ISSUER": "https://accounts.google.com",
                "JWKS_URL": "https://www.googleapis.com/oauth2/v3/certs",
                "TOKEN_URL": "https://oauth2.googleapis.com/token",
            },
            "apple": {
                "CLASS": "jb_drf_auth.providers.apple_oidc.AppleOidcProvider",
                "CLIENT_IDS": (),
                "CLIENT_SECRET": None,
                "ISSUER": "https://appleid.apple.com",
                "JWKS_URL": "https://appleid.apple.com/auth/keys",
                "TOKEN_URL": "https://appleid.apple.com/auth/token",
            },
            "facebook": {
                "CLASS": "jb_drf_auth.providers.facebook_oauth.FacebookOAuthProvider",
                "APP_ID": None,
                "APP_SECRET": None,
                "GRAPH_API_VERSION": "v21.0",
                "ASSUME_EMAIL_VERIFIED": True,
            },
        },
    },
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


def get_social_settings():
    defaults = DEFAULTS["SOCIAL"]
    configured = get_setting("SOCIAL")
    if not isinstance(configured, dict):
        return defaults

    merged = {**defaults, **configured}
    default_providers = defaults.get("PROVIDERS", {})
    configured_providers = configured.get("PROVIDERS", {})

    providers = {}
    if isinstance(default_providers, dict):
        for provider_name, provider_cfg in default_providers.items():
            providers[provider_name] = (
                dict(provider_cfg) if isinstance(provider_cfg, dict) else provider_cfg
            )

    if isinstance(configured_providers, dict):
        for provider_name, provider_cfg in configured_providers.items():
            base_cfg = providers.get(provider_name, {})
            if isinstance(base_cfg, dict) and isinstance(provider_cfg, dict):
                providers[provider_name] = {**base_cfg, **provider_cfg}
            else:
                providers[provider_name] = provider_cfg

    merged["PROVIDERS"] = providers
    return merged
