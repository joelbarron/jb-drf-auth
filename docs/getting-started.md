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

## Related Docs

- API contract: `API_CONTRACT.md`
- Social auth guide: `social-auth.md`
- Migration guide: `migration.md`
- Release guide: `release.md`

---

## API Contract

Formal endpoint contract is documented in `API_CONTRACT.md`.

---

## ✨ Features

- ✅ Abstract `User` base compatible with default or custom Django users
- ✅ Abstract `Profile` base (one user → many profiles)
- ✅ Built-in **soft delete** via `django-safedelete`
- ✅ Zero migrations inside the package (migrations live in consumer projects)
- ✅ Dynamic model resolution via Django settings
- ✅ Django 5 compatible
- i18n Compatible
- ✅ DRF serializers, services, and views based on `base_code`

---

## 📦 Installation

```bash
pip install jb-drf-auth
```

Add `jb_drf_auth` and `rest_framework` to `INSTALLED_APPS`.

---

## ⚙️ Settings

Minimal setup example (copy/paste into `settings.py`):

```python
JB_DRF_AUTH = {
    "PROFILE_MODEL": "authentication.Profile",
    "DEVICE_MODEL": "authentication.Device",
    "OTP_MODEL": "authentication.OtpCode",
    "SMS_LOG_MODEL": "authentication.SmsLog",
    "EMAIL_LOG_MODEL": "authentication.EmailLog",
    # Required if you enable social login:
    # "SOCIAL_ACCOUNT_MODEL": "authentication.SocialAccount",
    "FRONTEND_URL": env("FRONTEND_URL", default="http://localhost:3000"),
    "DEFAULT_FROM_EMAIL": "no-reply@your-domain.com",
    "AUTHENTICATION_TYPE": "both",  # "email", "username", "both"
    "AUTH_SINGLE_SESSION_ON_MOBILE": env.bool(
        "AUTH_SINGLE_SESSION_ON_MOBILE", default=False
    ),
    "ADMIN_BOOTSTRAP_TOKEN": env("ADMIN_BOOTSTRAP_TOKEN", default="super-secret-token"),
    "PROFILE_PICTURE_UPLOAD_TO": "uploads/users/profile-pictures",
    "PERSON_ID_DOCUMENTS_UPLOAD_TO": "uploads/people/id-documents",
    "PROFILE_ROLE_CHOICES": (
        ("PATIENT", "Patient"),
        ("DOCTOR", "Doctor"),
        ("ADMIN", "Admin"),
    ),
    "DEFAULT_PROFILE_ROLE": "PATIENT",
    "SMS_SENDER_ID": "YourBrand",
    "SMS_OTP_MESSAGE": "Tu codigo para acceder a Mentalysis es {code}. Expira en {minutes} minutos.",
}
```

If you use `env(...)`/`env.bool(...)`, ensure `environ.Env()` is configured in your settings module.

Optional:

```python
JB_DRF_AUTH_AUTHENTICATION_TYPE = "email"  # "email", "username", "both"
JB_DRF_AUTH_AUTH_SINGLE_SESSION_ON_MOBILE = False
JB_DRF_AUTH_ADMIN_BOOTSTRAP_TOKEN = "super-secret"
JB_DRF_AUTH_PROFILE_PICTURE_UPLOAD_TO = "uploads/users/profile-pictures"
JB_DRF_AUTH_PERSON_PICTURE_UPLOAD_TO = "uploads/users/profile-pictures"
JB_DRF_AUTH_PERSON_ID_DOCUMENTS_UPLOAD_TO = "uploads/people/id-documents"
JB_DRF_AUTH_PROFILE_PICTURE_OPTIMIZE = True
JB_DRF_AUTH_PROFILE_PICTURE_MAX_BYTES = 1024 * 1024
JB_DRF_AUTH_PROFILE_PICTURE_MAX_WIDTH = 1080
JB_DRF_AUTH_PROFILE_PICTURE_MAX_HEIGHT = 1080
JB_DRF_AUTH_PROFILE_PICTURE_JPEG_QUALITY = 85
JB_DRF_AUTH_PROFILE_PICTURE_MIN_JPEG_QUALITY = 65
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
JB_DRF_AUTH_THROTTLE_ENABLED = True
JB_DRF_AUTH_THROTTLE_RATES = {
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
}
```

Debug SMS provider (local development):

```python
JB_DRF_AUTH_SMS_PROVIDER = "jb_drf_auth.providers.console_sms.ConsoleSmsProvider"
```

Twilio SMS provider:

```python
JB_DRF_AUTH_SMS_PROVIDER = "jb_drf_auth.providers.twilio_sms.TwilioSmsProvider"
JB_DRF_AUTH_TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
JB_DRF_AUTH_TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
# Configure one of these:
JB_DRF_AUTH_TWILIO_FROM_NUMBER = env("TWILIO_FROM_NUMBER", default=None)
JB_DRF_AUTH_TWILIO_MESSAGING_SERVICE_SID = env("TWILIO_MESSAGING_SERVICE_SID", default=None)
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
    "TERMS_AND_CONDITIONS_REQUIRED": True,
    "AUTHENTICATION_TYPE": "email",  # "email", "username", "both"
    "CLIENT_CHOICES": ("web", "mobile"),
    "AUTH_SINGLE_SESSION_ON_MOBILE": False,
    "ADMIN_BOOTSTRAP_TOKEN": "super-secret",
    "PROFILE_PICTURE_UPLOAD_TO": "uploads/users/profile-pictures",
    "PROFILE_PICTURE_OPTIMIZE": True,
    "PROFILE_PICTURE_MAX_BYTES": 1024 * 1024,
    "PROFILE_PICTURE_MAX_WIDTH": 1080,
    "PROFILE_PICTURE_MAX_HEIGHT": 1080,
    "PROFILE_PICTURE_JPEG_QUALITY": 85,
    "PROFILE_PICTURE_MIN_JPEG_QUALITY": 65,
    "PERSON_PICTURE_UPLOAD_TO": "uploads/users/profile-pictures",
    "PERSON_ID_DOCUMENTS_UPLOAD_TO": "uploads/people/id-documents",
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
    AbstractJbSocialAccount,
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


class SocialAccount(AbstractJbSocialAccount):
    pass
```

`AbstractJbProfile` includes core person fields: `first_name`, `last_name_1`, `last_name_2`,
`birthday`, and `gender`.
For extended person data (`national_id`, `tax_id`, contact phones/emails, address fields,
emergency contact, identity document files), use `AbstractPersonCore` in your own models.
Phone fields in `AbstractPersonCore` are stored in E.164 format (for example: `+525512345678`).
Both `AbstractJbUser` and `AbstractJbProfile` include a `settings` JSON field for flexible app-level preferences.
`language` and `timezone` are stored inside `user.settings` and exposed as user-level properties.

Example for extended person models:

```python
from django.db import models
from jb_drf_auth.models import AbstractPersonCore


class Patient(AbstractPersonCore):
    profile = models.ForeignKey("authentication.Profile", on_delete=models.CASCADE)
```

Reusable ownership base models are also available:

```python
from django.db import models
from jb_drf_auth.models import AbstractProfileOwnedModel, AbstractUserOwnedModel


class UserNote(AbstractUserOwnedModel):
    title = models.CharField(max_length=100)


class ProfileAddress(AbstractProfileOwnedModel):
    line_1 = models.CharField(max_length=255)
```

## 🧑‍💼 Admin

Register your concrete models in your project admin:

```python
# authentication/admin.py
from django.contrib import admin

from authentication.models import Device, EmailLog, OtpCode, Profile, SmsLog, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "is_active", "is_verified", "is_staff")
    search_fields = ("email", "username", "phone")
    list_filter = ("is_active", "is_verified", "is_staff", "is_superuser")
    ordering = ("-id",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "is_default", "is_active")
    search_fields = ("user__email", "first_name", "last_name_1", "last_name_2")
    list_filter = ("role", "is_default", "is_active")
    ordering = ("-id",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "platform", "name", "linked_at")
    search_fields = ("user__email", "platform", "name", "token")
    list_filter = ("platform",)
    ordering = ("-id",)


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "channel", "is_used", "valid_until")
    search_fields = ("email", "phone", "code")
    list_filter = ("channel", "is_used")
    ordering = ("-id",)


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "provider", "status", "created")
    search_fields = ("phone", "provider", "message")
    list_filter = ("status", "provider")
    ordering = ("-id",)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("id", "to_email", "subject", "provider", "status", "created")
    search_fields = ("to_email", "subject")
    list_filter = ("status", "provider")
    ordering = ("-id",)
```

`GET /auth/me/` responses include `profile_completion_required` to signal when profile onboarding is still pending.
`GET /auth/me/` also returns `user_settings` and `profile_settings`.
When `TERMS_AND_CONDITIONS_REQUIRED` is enabled, signup requires
`terms_and_conditions_accepted = true`.

Update authenticated user account fields with:

`PATCH /auth/account/update/`

Complete onboarding using the existing profile endpoint:

`PATCH /auth/profiles/{id}/`

Required fields:
- `first_name`
- at least one of `last_name_1` or `last_name_2`

You can manage user settings and custom features from your integrator project commands:

```python
from django.contrib.auth import get_user_model
from jb_drf_auth.services import UserSettingsService

User = get_user_model()
user = User.objects.get(email="user@example.com")

# Single user
UserSettingsService.set_user_setting(user, "custom_theme", "dark")
UserSettingsService.remove_user_setting(user, "custom_theme")
UserSettingsService.set_user_feature(user, "reports_beta", True)
UserSettingsService.remove_user_feature(user, "reports_beta")

# All users
UserSettingsService.set_all_users_setting("release_channel", "stable")
UserSettingsService.remove_all_users_setting("release_channel")
UserSettingsService.set_all_users_feature("new_dashboard", True)
UserSettingsService.remove_all_users_feature("new_dashboard")
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

## 🧪 Tests

Initial tests are under `jb_drf_auth/tests/`.
Endpoint coverage lives in `jb_drf_auth/tests/test_endpoints.py`.
Run with:

```bash
python -m unittest discover -s jb_drf_auth/tests -p "test_*.py"
```

Note: your environment must have Django and package dependencies installed.

## 🌐 i18n Messages

User-facing messages in serializers/views/services are translation-ready via
`gettext` / `gettext_lazy`.

In integrator projects, generate and compile message catalogs as usual:

```bash
django-admin makemessages -l es
django-admin compilemessages
```

Then configure `LANGUAGE_CODE` / `LANGUAGES` in your project settings.
