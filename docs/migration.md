# Migration Guide

This guide covers migration from an existing auth app to `jb-drf-auth` in projects that already have migrations and production data.

## Scope

Use this guide when your project already has:

- custom `authentication` app/models
- applied migrations in multiple environments
- active production traffic

## Migration strategy

Use an additive strategy:

1. Keep existing concrete models in your project (`authentication.User`, `authentication.Profile`, etc.).
2. Make them inherit from `jb_drf_auth` abstract models.
3. Generate project migrations in the integrator app.
4. Deploy safely across all environments before removing any compatibility shim.

Do not rewrite migration history in production.

## 1) Concrete models in integrator project

Example:

```python
# authentication/models.py
from django.db import models
from jb_drf_auth.models import (
    AbstractJbDevice,
    AbstractJbEmailLog,
    AbstractJbOtpCode,
    AbstractJbProfile,
    AbstractJbSmsLog,
    AbstractJbUser,
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

If your project needs extra fields (for example `stripe_customer_id`), add them only in your concrete models.

## 2) Settings alignment

At minimum, set:

```python
AUTH_USER_MODEL = "authentication.User"

JB_DRF_AUTH = {
    "PROFILE_MODEL": "authentication.Profile",
    "DEVICE_MODEL": "authentication.Device",
    "OTP_MODEL": "authentication.OtpCode",
    "SMS_LOG_MODEL": "authentication.SmsLog",
    "EMAIL_LOG_MODEL": "authentication.EmailLog",
}
```

Add additional keys based on your flows (frontend URL, providers, throttling, etc.).

## 3) Manager shim for existing migrations

If old project migrations import old paths like:

- `api.authentication.managers`

create a shim module at that old path that re-exports `UserManager` from `jb_drf_auth.managers`.

Example shim:

```python
# api/authentication/managers.py
from jb_drf_auth.managers import UserManager

__all__ = ["UserManager"]
```

Why: old migrations are historical artifacts; they must remain importable forever.

## 4) Migration files in production projects

Rules:

- Do not edit already-applied migrations in production.
- Do not break import paths referenced by historical migrations.
- Add new forward migrations only.

If a migration was already applied in prod, changing its imports later can break fresh setups and CI.

## 5) Rollout checklist

1. Add/adjust concrete models and settings.
2. Add manager shim for legacy migration imports (if needed).
3. Create new migrations: `python manage.py makemigrations`.
4. Apply migrations in dev/staging/prod: `python manage.py migrate`.
5. Verify critical endpoints: register, login, otp, password reset, `/auth/me`.
6. Verify admin model registration and queryset behavior.
7. Verify logs are being written to `SmsLog` and `EmailLog`.

## 6) Can I remove the shim later?

Only after all of the following are true:

- no migration in any app imports the old path
- no deployment target can run those migrations again
- no fresh environment depends on those historical files

In practice, keep the shim. It is low-cost and avoids bootstrap failures.

## 7) Common failures

### `ModuleNotFoundError` during migrate

Cause: historical migration imports a removed module (commonly old manager path).

Fix: restore compatibility shim at that old import path.

### Different behavior across environments

Cause: inconsistent migration states or modified historical migration files.

Fix: stop modifying historical migrations; add forward migrations only.

## 8) Data safety notes

- Backup database before structural changes.
- Run migration dry-runs in staging with production-like data.
- Treat auth table changes as high-risk and deploy with rollback plan.
