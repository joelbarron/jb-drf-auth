# JB DRF Auth - API Contract v1

This document defines the request/response contract for `jb_drf_auth.urls`.
Recommended mount point in consumer projects:

- `/auth/` -> `include("jb_drf_auth.urls")`

Examples below assume that base path.

## Conventions

- `Content-Type: application/json`
- Authenticated endpoints require `Authorization: Bearer <access_token>`.
- Validation errors use DRF default format (`400` with field/non-field errors).
- Throttled endpoints return `429 Too Many Requests`.
- Payload examples in this document use `snake_case`.

## snake_case and camelCase payloads

`jb-drf-auth` serializers are defined in `snake_case` (for example: `password_confirm`,
`first_name`, `terms_and_conditions_accepted`).

If your integrator project enables camel-case DRF parsers/renderers (for example
`djangorestframework-camel-case`), you can send camelCase payloads instead
(`passwordConfirm`, `firstName`, `termsAndConditionsAccepted`).

Collections available in `docs/`:

- `API.postman_collection.json` (snake_case)
- `API.camel.postman_collection.json` (camelCase)

## Authentication

### POST `/auth/register/`

Create user + default profile.

Request:

```json
{
  "email": "user@example.com",
  "username": "user1",
  "password": "secret123",
  "password_confirm": "secret123",
  "first_name": "Joel",
  "last_name_1": "Barron",
  "last_name_2": "Lopez",
  "birthday": "1990-01-01",
  "gender": "MALE",
  "role": "USER",
  "terms_and_conditions_accepted": true
}
```

Success `201`:

```json
{
  "detail": "Usuario creado. Revisa tu correo para verificar tu cuenta."
}
```

Success (email send failed) `201`:

```json
{
  "detail": "Usuario creado, pero el correo no fue enviado.",
  "email_sent": false
}
```

Common errors:

- `400`: validation errors, passwords mismatch, T&C required.
- `409`: conflict while creating user.
- `429`: throttled.

### POST `/auth/login/basic/`

Request (web):

```json
{
  "login": "user@example.com",
  "password": "secret123",
  "client": "web"
}
```

`device` is ignored for `client = "web"` if it is sent.

Request (mobile):

```json
{
  "login": "user@example.com",
  "password": "secret123",
  "client": "mobile",
  "device": {
    "platform": "ios",
    "name": "iPhone",
    "token": "push_token_optional"
  }
}
```

Success `200`:

- Returns client-specific login payload with tokens.

Common errors:

- `400`: missing/invalid `device` when `client = "mobile"`.
- `401`: invalid credentials, inactive/unverified/deleted account.
- `429`: throttled.

### POST `/auth/profile/switch/`

Requires auth.

Request:

```json
{
  "profile": 10,
  "client": "mobile",
  "device": {
    "platform": "android",
    "name": "Pixel",
    "token": "device_token"
  }
}
```

Success `200`: client-specific payload with refreshed tokens.

Common errors:

- `401`: unauthenticated.
- `404`: profile not found / not owned by user.

### POST `/auth/token/refresh/`

SimpleJWT pass-through endpoint.

Request:

```json
{
  "refresh": "<refresh_token>"
}
```

Success `200`:

```json
{
  "access": "<new_access_token>"
}
```

## OTP

### POST `/auth/otp/request/`

Request (email):

```json
{
  "email": "user@example.com",
  "channel": "email"
}
```

Request (sms):

```json
{
  "phone": "+525512345678",
  "channel": "sms"
}
```

Success `201`:

```json
{
  "detail": "Código enviado exitosamente.",
  "channel": "sms"
}
```

Common errors:

- `400`: invalid payload or missing required channel field.
- `429`: resend cooldown or view throttling.
- `503`: SMS provider delivery failure.

### POST `/auth/otp/verify/`

Request:

```json
{
  "email": "user@example.com",
  "code": "123456",
  "client": "web",
  "device": {
    "platform": "ios",
    "name": "iPhone"
  }
}
```

`phone` can be used instead of `email`.

Success `200`: client-specific login payload with tokens.

Common errors:

- `401`: invalid/expired OTP.
- `429`: max attempts reached or endpoint throttled.

## Email confirmation

### POST `/auth/registration/account-confirmation-email/`

Request:

```json
{
  "uid": "<uidb64>",
  "token": "<token>"
}
```

Success `200`:

```json
{
  "detail": "Correo verificado con éxito."
}
```

Common errors:

- `400`: invalid link or token.
- `429`: throttled.

### POST `/auth/registration/account-confirmation-email/resend/`

Request:

```json
{
  "email": "user@example.com"
}
```

Success `200`:

```json
{
  "detail": "Correo de verificación reenviado.",
  "email_sent": true
}
```

Success (email failed) `200`:

```json
{
  "detail": "Solicitud recibida, pero el correo no fue enviado.",
  "email_sent": false
}
```

Common errors:

- `400`: user not found / already verified.
- `429`: throttled.

## Password reset

### POST `/auth/password-reset/request/`

Request:

```json
{
  "email": "user@example.com"
}
```

Success `200`:

```json
{
  "detail": "Si el correo existe, se ha enviado un enlace de restablecimiento.",
  "email_sent": true
}
```

Success (email failed) `200`:

```json
{
  "detail": "Solicitud recibida, pero el correo no fue enviado.",
  "email_sent": false
}
```

Common errors:

- `400`: validation errors.
- `429`: throttled.

### POST `/auth/password-reset/confirm/`

Request:

```json
{
  "uid": "<uidb64>",
  "token": "<token>",
  "new_password": "new-secret-123",
  "new_password_confirm": "new-secret-123"
}
```

Success `200`:

```json
{
  "detail": "Contrasena restablecida con exito."
}
```

Common errors:

- `400`: mismatch passwords, invalid/expired token.
- `429`: throttled.

### POST `/auth/password-reset/change/`

Requires auth.

Request:

```json
{
  "old_password": "old-secret",
  "new_password": "new-secret",
  "new_password_confirm": "new-secret"
}
```

Success `200`:

```json
{
  "detail": "Contrasena actualizada con exito."
}
```

Common errors:

- `400`: wrong current password or mismatch.
- `401`: unauthenticated.

## Account and me

### GET `/auth/me/?client=<web|mobile>&device_token=<optional>`

Requires auth and a token containing profile claim (`profile_id` by default).

Success `200`: user payload with active profile, settings and completion flags.

Common errors:

- `401`: invalid/inactive/deleted/non-verified user.
- `403`: missing profile claim in token.

### PATCH `/auth/account/update/`

Requires auth.

Updatable fields (if present in concrete user model):

- `email`
- `username`
- `phone`
- `terms_and_conditions`
- `language`
- `timezone`

Success `200`: serialized user.

Common errors:

- `400`: validation/uniqueness errors.
- `401`: unauthenticated.

### PUT `/auth/account/update/`

Same as PATCH but full update semantics.

### DELETE `/auth/account/delete/`

Requires auth.

Request:

```json
{
  "confirmation": true
}
```

Success `200`:

```json
"Cuenta eliminada correctamente."
```

Common errors:

- `400`: missing confirmation.
- `401`: unauthenticated.

## Profiles

### GET `/auth/profiles/`

Requires auth. Returns only current user profiles.

### POST `/auth/profiles/`

Requires auth. Creates profile owned by current user.

### GET `/auth/profiles/{id}/`

Requires auth.

### PATCH `/auth/profiles/{id}/`

Requires auth. Only owner can update.

### DELETE `/auth/profiles/{id}/`

Requires auth. Only owner can delete.

Common errors:

- `400`: validation errors.
- `401`: unauthenticated.
- `404`: profile not found (or not owned).

## Admin bootstrap endpoints

### POST `/auth/admin/create-superuser/`
### POST `/auth/admin/create-staff/`

Access policy:

- Allowed for authenticated superusers, or
- Allowed with header `X-Admin-Bootstrap-Token` only if there are no superusers yet.

Request:

```json
{
  "email": "admin@example.com",
  "password": "secret123"
}
```

Success `201` with created user metadata.

Common errors:

- `401`: unauthorized bootstrap/admin.
- `409`: user already exists.
