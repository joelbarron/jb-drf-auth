import importlib.util

from django.conf import settings
from django.core.checks import Warning, register


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
