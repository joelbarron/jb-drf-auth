import importlib.util

from django.conf import settings
from django.core.checks import Error, Warning, register

from jb_drf_auth.conf import get_social_settings


@register()
def auth_password_hashers_check(app_configs, **kwargs):
    configured = getattr(settings, "PASSWORD_HASHERS", [])
    required_hashers = [
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    ]

    missing = [hasher for hasher in required_hashers if hasher not in configured]
    if missing:
        return [
            Warning(
                "Missing recommended PASSWORD_HASHERS entries for argon2/bcrypt.",
                hint=(
                    "Add Argon2PasswordHasher and BCryptSHA256PasswordHasher "
                    "to PASSWORD_HASHERS in settings.py."
                ),
                id="jb_drf_auth.W001",
            )
        ]

    missing_packages = []
    if importlib.util.find_spec("argon2") is None:
        missing_packages.append("argon2-cffi")
    if importlib.util.find_spec("bcrypt") is None:
        missing_packages.append("bcrypt")
    if missing_packages:
        return [
            Warning(
                "Password hasher dependencies are missing.",
                hint=f"Install: {', '.join(missing_packages)}",
                id="jb_drf_auth.W002",
            )
        ]

    return []


@register()
def social_auth_configuration_check(app_configs, **kwargs):
    social_account_model = getattr(settings, "JB_DRF_AUTH", {}).get("SOCIAL_ACCOUNT_MODEL")
    if not social_account_model:
        return []

    issues = []
    social_settings = get_social_settings()
    providers = social_settings.get("PROVIDERS", {})
    if not isinstance(providers, dict):
        return [
            Error(
                "JB_DRF_AUTH['SOCIAL']['PROVIDERS'] must be a dict.",
                id="jb_drf_auth.E001",
            )
        ]

    for provider_name in ("google", "apple"):
        provider_cfg = providers.get(provider_name, {})
        if not isinstance(provider_cfg, dict):
            continue
        client_ids = provider_cfg.get("CLIENT_IDS") or ()
        if not client_ids:
            issues.append(
                Error(
                    f"Missing CLIENT_IDS for social provider '{provider_name}'.",
                    hint=f"Set JB_DRF_AUTH['SOCIAL']['PROVIDERS']['{provider_name}']['CLIENT_IDS'].",
                    id="jb_drf_auth.E002",
                )
            )
        if provider_name == "apple" and not provider_cfg.get("CLIENT_SECRET"):
            issues.append(
                Warning(
                    "Apple CLIENT_SECRET is not configured.",
                    hint=(
                        "It is required for authorization_code exchange. "
                        "id_token-only flow can work without it."
                    ),
                    id="jb_drf_auth.W003",
                )
            )

    facebook_cfg = providers.get("facebook", {})
    if isinstance(facebook_cfg, dict):
        app_id = facebook_cfg.get("APP_ID")
        app_secret = facebook_cfg.get("APP_SECRET")
        if bool(app_id) != bool(app_secret):
            issues.append(
                Error(
                    "Facebook APP_ID and APP_SECRET must be configured together.",
                    hint="Set both or neither in JB_DRF_AUTH['SOCIAL']['PROVIDERS']['facebook'].",
                    id="jb_drf_auth.E003",
                )
            )

    return issues
