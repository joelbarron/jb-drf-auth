# jb-drf-auth

Reusable authentication module for Django + Django REST Framework.

`jb-drf-auth` is a reusable foundation for authentication flows across projects, including:

- User/profile base models (extensible)
- OTP flows (email/SMS)
- Login, registration, password reset, email confirmation
- Multi-profile support
- Provider-based SMS/email architecture
- Configurable behavior via Django settings

## Installation

```bash
pip install jb-drf-auth
```

Add `jb_drf_auth` and `rest_framework` to `INSTALLED_APPS`.

## Documentation

- Main docs index: `docs/README.md`
- Getting started and configuration: `docs/getting-started.md`
- API contract (endpoint by endpoint): `docs/API_CONTRACT.md`
- Social authentication guide: `docs/social-auth.md`
- Migration guide: `docs/migration.md`
- i18n integration guide: `docs/i18n.md`
- Release guide: `docs/release.md`
- Roadmap: `roadmap.md`

## Quick Start

1. Configure concrete models in your project (`User`, `Profile`, `Device`, `OtpCode`, logs).
2. Configure `JB_DRF_AUTH` settings (minimal real-world example):

```python
JB_DRF_AUTH = {
    "PROFILE_MODEL": "authentication.Profile",
    "DEVICE_MODEL": "authentication.Device",
    "OTP_MODEL": "authentication.OtpCode",
    "SMS_LOG_MODEL": "authentication.SmsLog",
    "EMAIL_LOG_MODEL": "authentication.EmailLog",
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
3. Mount URLs:

```python
from django.urls import include, path

urlpatterns = [
    path("auth/", include("jb_drf_auth.urls")),
]
```

4. Run migrations in the integrator project.

For complete setup examples (including full `JB_DRF_AUTH` dict), see `docs/getting-started.md`.
