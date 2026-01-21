# jb-drf-auth

Reusable authentication foundations for **Django + Django REST Framework** projects.

`jb-drf-auth` provides a clean, extensible base for authentication-related concerns, focused on:

- Abstract user and profile models
- Soft delete using `django-safedelete`
- Support for **multiple profiles per user**
- Project-level extensibility (different profile schemas per project)
- Integration with DRF viewsets/serializers

This package is designed to be installed via PyPI and reused across multiple Django projects without duplicating auth logic.

---

## ✨ Features

- ✅ Abstract `User` base compatible with default or custom Django users
- ✅ Abstract `Profile` base (one user → many profiles)
- ✅ Built-in **soft delete** via `django-safedelete`
- ✅ Zero migrations inside the package (migrations live in consumer projects)
- ✅ Dynamic model resolution via Django settings
- ✅ Django 5 compatible
- ✅ DRF serializers, services, and views based on `base_code`

---

## 📦 Installation

```bash
pip install jb-drf-auth
```

Add `jb_drf_auth` and `rest_framework` to `INSTALLED_APPS`.

---

## ⚙️ Settings

Minimal required settings (add to `settings.py`):

```python
JB_DRF_AUTH_PROFILE_MODEL = "authentication.Profile"
JB_DRF_AUTH_DEVICE_MODEL = "authentication.Device"
JB_DRF_AUTH_OTP_MODEL = "authentication.OtpCode"
JB_DRF_AUTH_EMAIL_LOG_MODEL = "authentication.EmailLog"

JB_DRF_AUTH_FRONTEND_URL = "https://your-frontend"
JB_DRF_AUTH_DEFAULT_FROM_EMAIL = "no-reply@your-domain.com"
```

Optional:

```python
JB_DRF_AUTH_AUTHENTICATION_TYPE = "email"  # "email", "username", "both"
JB_DRF_AUTH_AUTH_SINGLE_SESSION_ON_MOBILE = False
JB_DRF_AUTH_ADMIN_BOOTSTRAP_TOKEN = "super-secret"
JB_DRF_AUTH_PROFILE_PICTURE_UPLOAD_TO = "uploads/users/profile-pictures"
JB_DRF_AUTH_SMS_PROVIDER = "jb_drf_auth.providers.aws_sns.AwsSnsSmsProvider"
JB_DRF_AUTH_SMS_SENDER_ID = "YourBrand"
JB_DRF_AUTH_SMS_TYPE = "Transactional"
JB_DRF_AUTH_SMS_OTP_MESSAGE = "Tu codigo es {code}. Expira en {minutes} minutos." #OTP messages must use 160 GSM-7 characters only (no accents, emojis, or special symbols).
JB_DRF_AUTH_SMS_LOG_MODEL = "authentication.SmsLog"
JB_DRF_AUTH_EMAIL_PROVIDER = "jb_drf_auth.providers.django_email.DjangoEmailProvider"
JB_DRF_AUTH_EMAIL_TEMPLATES = {}
JB_DRF_AUTH_OTP_LENGTH = 6
JB_DRF_AUTH_OTP_TTL_SECONDS = 300
JB_DRF_AUTH_OTP_MAX_ATTEMPTS = 5
JB_DRF_AUTH_OTP_RESEND_COOLDOWN_SECONDS = 60
JB_DRF_AUTH_PHONE_DEFAULT_COUNTRY_CODE = "52"  # required only if clients don't send E.164 (+countrycode)
```

You can also configure everything using a single dict (copy/paste ready):

```python
AUTH_USER_MODEL = "authentication.User"

JB_DRF_AUTH = {
    "PROFILE_MODEL": "authentication.Profile",
    "DEVICE_MODEL": "authentication.Device",
    "OTP_MODEL": "authentication.OtpCode",
    "SMS_LOG_MODEL": "authentication.SmsLog",
    "EMAIL_LOG_MODEL": "authentication.EmailLog",
    "FRONTEND_URL": "https://your-frontend",
    "DEFAULT_FROM_EMAIL": "no-reply@your-domain.com",
    "AUTHENTICATION_TYPE": "email",  # "email", "username", "both"
    "CLIENT_CHOICES": ("web", "mobile"),
    "AUTH_SINGLE_SESSION_ON_MOBILE": False,
    "ADMIN_BOOTSTRAP_TOKEN": "super-secret",
    "PROFILE_PICTURE_UPLOAD_TO": "uploads/users/profile-pictures",
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
    "SMS_PROVIDER": "jb_drf_auth.providers.aws_sns.AwsSnsSmsProvider",
    "SMS_SENDER_ID": "YourBrand",
    "SMS_TYPE": "Transactional",
    "SMS_OTP_MESSAGE": "Tu codigo es {code}. Expira en {minutes} minutos.",
    "OTP_LENGTH": 6,
    "OTP_TTL_SECONDS": 300,
    "OTP_MAX_ATTEMPTS": 5,
    "OTP_RESEND_COOLDOWN_SECONDS": 60,
    "PHONE_DEFAULT_COUNTRY_CODE": "52",
    "PHONE_MIN_LENGTH": 10,
    "PHONE_MAX_LENGTH": 15,
    "EMAIL_PROVIDER": "jb_drf_auth.providers.django_email.DjangoEmailProvider",
    "EMAIL_TEMPLATES": {},
}
```

Email template example:

```python
JB_DRF_AUTH_EMAIL_TEMPLATES = {
    "email_confirmation": {
        "subject": "Verifica tu correo",
        "text": "Hola {user_email}, verifica tu correo aqui: {verify_url}",
        "html": "<p>Hola {user_email},</p><a href=\"{verify_url}\">Verificar</a>",
    },
    "password_reset": {
        "subject": "Restablece tu contrasena",
        "text": "Hola {user_email}, restablece tu contrasena: {reset_url}",
        "html": "<p>Hola {user_email},</p><a href=\"{reset_url}\">Restablecer</a>",
    },
}
```

---

## 🧩 Models

Create concrete models in your project by extending the base classes.

```python
# authentication/models.py
from django.db import models
from jb_drf_auth.models import (
    AbstractJbUser,
    AbstractJbProfile,
    AbstractJbDevice,
    AbstractJbEmailLog,
    AbstractJbOtpCode,
    AbstractJbSmsLog,
)


class User(AbstractJbUser):
    pass


class Profile(AbstractJbProfile):
    pass


class Device(AbstractJbDevice):
    pass


class OtpCode(AbstractJbOtpCode):
    pass


class SmsLog(AbstractJbSmsLog):
    pass


class EmailLog(AbstractJbEmailLog):
    pass
```

Then set `AUTH_USER_MODEL = "authentication.User"` and run migrations in your project.

---

## 🛣️ URLs

```python
# project/urls.py
from django.urls import include, path

urlpatterns = [
    path("auth/", include("jb_drf_auth.urls")),
]
```
