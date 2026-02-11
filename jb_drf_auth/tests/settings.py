SECRET_KEY = "test-secret-key"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "safedelete",
    "jb_drf_auth",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MIDDLEWARE = []

ROOT_URLCONF = "jb_drf_auth.urls"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

JB_DRF_AUTH = {
    "PROFILE_MODEL": "auth.User",
    "DEVICE_MODEL": "auth.User",
    "OTP_MODEL": "auth.User",
    "SMS_LOG_MODEL": "auth.User",
    "EMAIL_LOG_MODEL": "auth.User",
}
