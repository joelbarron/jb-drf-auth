# Social Authentication Guide

This document explains how to integrate social login with `jb-drf-auth` and what frontend apps should implement.

For Google Cloud Console setup (OAuth consent screen, origins, redirect URIs), see:

- `google-oauth-setup.md`

For Meta/Facebook app setup (app credentials, login product, redirect URIs), see:

- `facebook-oauth-setup.md`

Current backend endpoint:

- `POST /auth/login/social/`
- `POST /auth/login/social/precheck/`
- `POST /auth/login/social/link/`
- `POST /auth/login/social/unlink/`

Current provider strategy:

- Google OIDC
- Apple OIDC
- Facebook Graph API

## Backend prerequisites

### 1. Add concrete `SocialAccount` model in your integrator project

```python
# authentication/models.py
from jb_drf_auth.models import AbstractJbSocialAccount


class SocialAccount(AbstractJbSocialAccount):
    pass
```

Create and apply migrations in the integrator project.

### 2. Configure settings

```python
JB_DRF_AUTH = {
    # Existing required models
    "PROFILE_MODEL": "authentication.Profile",
    "DEVICE_MODEL": "authentication.Device",
    "OTP_MODEL": "authentication.OtpCode",
    "SMS_LOG_MODEL": "authentication.SmsLog",
    "EMAIL_LOG_MODEL": "authentication.EmailLog",
    # New required model for social auth
    "SOCIAL_ACCOUNT_MODEL": "authentication.SocialAccount",
    # Social auth behavior
    "SOCIAL": {
        "DEBUG_ERRORS": env.bool("SOCIAL_ACCOUNT_DEBUG_ERRORS", default=False),  # True only for local debugging
        "AUTO_CREATE_USER": True,
        "LINK_BY_EMAIL": True,
        "REQUIRE_VERIFIED_EMAIL": True,
        "SYNC_PICTURE_ON_LOGIN": True,
        "PICTURE_DOWNLOAD_TIMEOUT_SECONDS": 5,
        "PICTURE_MAX_BYTES": 5242880,
        "PICTURE_ALLOWED_CONTENT_TYPES": ("image/jpeg", "image/png", "image/webp"),
        "PROVIDERS": {
            "google": {
                "CLASS": "jb_drf_auth.providers.google_oidc.GoogleOidcProvider",
                "CLIENT_ID_WEB": env("GOOGLE_WEB_CLIENT_ID"),
                "CLIENT_ID_IOS": env("GOOGLE_IOS_CLIENT_ID", default=None),
                "CLIENT_ID_ANDROID": env("GOOGLE_ANDROID_CLIENT_ID", default=None),
                "ISSUER": "https://accounts.google.com",
                "JWKS_URL": "https://www.googleapis.com/oauth2/v3/certs",
            },
            "apple": {
                "CLASS": "jb_drf_auth.providers.apple_oidc.AppleOidcProvider",
                "CLIENT_ID": env("APPLE_SERVICES_ID_OR_BUNDLE_ID"),
                "CLIENT_SECRET": env("APPLE_CLIENT_SECRET", default=None),
                "ISSUER": "https://appleid.apple.com",
                "JWKS_URL": "https://appleid.apple.com/auth/keys",
            },
            "facebook": {
                "CLASS": "jb_drf_auth.providers.facebook_oauth.FacebookOAuthProvider",
                "APP_ID": "<facebook-app-id>",
                "APP_SECRET": "<facebook-app-secret>",
                "GRAPH_API_VERSION": "v21.0",
                "ASSUME_EMAIL_VERIFIED": True,
            },
        },
    },
}
```

You can configure one or many client IDs using discrete keys (`CLIENT_ID`, `CLIENT_ID_WEB`,
`CLIENT_ID_IOS`, `CLIENT_ID_ANDROID`). The library normalizes them internally to `CLIENT_IDS`
for OIDC audience validation. You do not need all three:

- Web-only project: configure only web client ID.
- Mobile-only project: configure only iOS/Android IDs.
- Multi-platform project: configure all platform IDs.

## API contract (social login)

### Endpoint

- `POST /auth/login/social/`

### Request (web)

```json
{
  "provider": "google",
  "id_token": "<oidc_id_token>",
  "role": "DOCTOR",
  "client": "web",
  "terms_and_conditions_accepted": true
}
```

### Request (web with authorization code)

```json
{
  "provider": "google",
  "authorization_code": "<oauth_authorization_code>",
  "redirect_uri": "https://your-app.com/auth/callback/google",
  "code_verifier": "<pkce_code_verifier>",
  "client_id": "<google-web-client-id>",
  "role": "DOCTOR",
  "client": "web",
  "terms_and_conditions_accepted": true
}
```

### Request (mobile)

```json
{
  "provider": "google",
  "id_token": "<oidc_id_token>",
  "role": "DOCTOR",
  "client": "mobile",
  "terms_and_conditions_accepted": true,
  "device": {
    "platform": "ios",
    "name": "iPhone 15",
    "token": "device_identifier_optional",
    "notification_token": "fcm_or_apns_token"
  }
}
```

### Request (facebook web)

```json
{
  "provider": "facebook",
  "access_token": "<facebook_user_access_token>",
  "role": "DOCTOR",
  "client": "web",
  "terms_and_conditions_accepted": true
}
```

`role` is optional and only affects profile creation when social login creates a new user/profile.

### Success response (`200`)

Returns the same client-specific login payload as `/auth/login/basic/`, plus:

- `social_provider`
- `user_created` (`true` when a new user was created)
- `linked_existing_user` (`true` when existing user was linked by email)
- `social_account_id`

## API contract (social precheck)

### Endpoint

- `POST /auth/login/social/precheck/`

### Request

Uses the same payload as `POST /auth/login/social/`.

### Success response (`200`)

```json
{
  "provider": "google",
  "email": "user@example.com",
  "email_verified": true,
  "social_account_exists": false,
  "linked_existing_user": true,
  "user_exists": true,
  "would_create_user": false,
  "can_login": true
}
```

This endpoint validates provider token and returns account existence flags, but does not create/link accounts or issue JWTs.

### Common errors

- `400`: invalid provider, invalid token, missing social configuration, missing mobile device fields.
- `401`: token invalid/expired or provider claims do not validate.
- `429`: throttled.

## Frontend implementation (recommended)

## Provider token matrix

| Provider | Preferred frontend output | Backend accepted payload |
| --- | --- | --- |
| Google | `id_token` (or `authorization_code` + PKCE) | `id_token` or `authorization_code` |
| Apple | `id_token` (or `authorization_code`) | `id_token` or `authorization_code` |
| Facebook | `access_token` | `access_token` |

### Web flow

1. Start provider login (Google/Apple/Facebook SDK).
2. Request scopes for OIDC providers: `openid`, `email`, `profile`.
3. Request scopes for Facebook: `public_profile`, `email`.
4. Generate and persist `state` and `nonce` per login attempt.
5. Receive token from provider SDK:
6. Google/Apple: `id_token`.
7. Facebook: `access_token`.
8. Send token to backend `POST /auth/login/social/`.
9. Store backend JWT tokens only (do not trust provider token for API auth).

Alternative for Google/Apple web:

- Send `authorization_code` + `redirect_uri` (+ `code_verifier` for PKCE) to backend.
- Backend exchanges code server-side and validates resulting `id_token`.

### Mobile flow

1. Use native SDK (Google Sign-In / Sign in with Apple).
2. Obtain provider token.
3. Google/Apple: `id_token`.
4. Facebook: `access_token`.
5. Read push token (FCM/APNs).
6. Send token + `client=mobile` + `device.notification_token`.
7. Persist backend JWT tokens.

## Link and unlink flows

For already-authenticated users:

- `POST /auth/login/social/link/` to attach a provider account.
- `POST /auth/login/social/unlink/` to detach a provider account.

## What frontend must enforce

- Always send `client` (`web` or `mobile`).
- For `mobile`, always send `device.notification_token`.
- If your product requires T&C, send `terms_and_conditions_accepted=true` on first social signup.
- Handle `400/401` from backend and retry full provider login (do not loop on stale tokens).

## Security notes

- Keep provider credentials and verification on backend.
- Use HTTPS only.
- Do not use provider access token as session token for your API.
- Rotate/revoke your app sessions with backend JWT policies only.

## Logging and troubleshooting

The library now logs social auth events in these logger namespaces:

- `jb_drf_auth.views.social_auth`
- `jb_drf_auth.services.social_auth`
- `jb_drf_auth.providers.oidc`
- `jb_drf_auth.providers.facebook_oauth`

Recommended Django logging config (example):

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "jb_drf_auth": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
```

For local diagnostics only, you can also enable:

```python
JB_DRF_AUTH = {
    "SOCIAL": {
        "DEBUG_ERRORS": True,
    }
}
```

Keep `DEBUG_ERRORS=False` in production.

## Current scope and next steps

Current implementation:

- OIDC providers validate `id_token` against provider JWKS.
- OIDC providers can also exchange `authorization_code` server-side.
- Facebook reads profile from Graph API with `access_token`.

Possible extensions:

- Provider-specific enrichment fields.
