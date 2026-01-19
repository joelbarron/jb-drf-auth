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
JB_DRF_AUTH_PROFILE_MODEL = "accounts.Profile"
JB_DRF_AUTH_DEVICE_MODEL = "accounts.Device"
JB_DRF_AUTH_OTP_MODEL = "accounts.OtpCode"

JB_DRF_AUTH_FRONTEND_URL = "https://your-frontend"
JB_DRF_AUTH_DEFAULT_FROM_EMAIL = "no-reply@your-domain.com"
```

Optional:

```python
JB_DRF_AUTH_AUTHENTICATION_TYPE = "email"  # "email", "username", "both"
JB_DRF_AUTH_AUTH_SINGLE_SESSION_ON_MOBILE = False
JB_DRF_AUTH_ADMIN_BOOTSTRAP_TOKEN = "super-secret"
JB_DRF_AUTH_PROFILE_PICTURE_UPLOAD_TO = "uploads/users/profile-pictures"
```

---

## 🧩 Models

Create concrete models in your project by extending the base classes.

```python
# accounts/models.py
from django.db import models
from jb_drf_auth.models import (
    AbstractJbUser,
    AbstractJbProfile,
    AbstractJbDevice,
    AbstractJbOtpCode,
)


class User(AbstractJbUser):
    pass


class Profile(AbstractJbProfile):
    pass


class Device(AbstractJbDevice):
    pass


class OtpCode(AbstractJbOtpCode):
    pass
```

Then set `AUTH_USER_MODEL = "accounts.User"` and run migrations in your project.

---

## 🛣️ URLs

```python
# project/urls.py
from django.urls import include, path

urlpatterns = [
    path("auth/", include("jb_drf_auth.urls")),
]
```
