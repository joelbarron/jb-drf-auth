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
JB_DRF_AUTH_OTP_LENGTH = 6
JB_DRF_AUTH_OTP_TTL_SECONDS = 300
JB_DRF_AUTH_OTP_MAX_ATTEMPTS = 5
JB_DRF_AUTH_OTP_RESEND_COOLDOWN_SECONDS = 60
JB_DRF_AUTH_PHONE_DEFAULT_COUNTRY_CODE = "52"  # required only if clients don't send E.164 (+countrycode)
```

You can also configure everything using a single dict:

```python
JB_DRF_AUTH = {
    "PROFILE_MODEL": "authentication.Profile",
    "DEVICE_MODEL": "authentication.Device",
    "OTP_MODEL": "authentication.OtpCode",
    "FRONTEND_URL": "https://your-frontend",
    "DEFAULT_FROM_EMAIL": "no-reply@your-domain.com",
    "SMS_PROVIDER": "jb_drf_auth.providers.aws_sns.AwsSnsSmsProvider",
    "OTP_TTL_SECONDS": 300,
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
