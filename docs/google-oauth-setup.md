# Google OAuth Setup (Web + Mobile)

This guide explains how to create Google OAuth credentials for `jb-drf-auth` social login.

Use this together with `social-auth.md`.

## 1. Create or select a Google Cloud project

1. Go to Google Cloud Console.
2. Select an existing project or create a new one.

## 2. Configure OAuth consent screen

1. Go to `APIs & Services` -> `OAuth consent screen`.
2. Select app type (`External` for most SaaS apps).
3. Fill required app info (name, support email, developer email).
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users if app is in testing mode.

## 3. Create OAuth client(s)

Go to `APIs & Services` -> `Credentials` -> `Create credentials` -> `OAuth client ID`.

### Web client

Create a client with type `Web application`.

- Authorized JavaScript origins:
  - Frontend origins only (not API domain), for example:
    - `http://localhost:3000`
    - `https://app.example.com`
- Authorized redirect URIs:
  - Frontend callback URL(s), for example:
    - `http://localhost:3000/auth/callback/google`
    - `https://app.example.com/auth/callback/google`

Save the generated Client ID.

### Mobile clients (optional)

If you support native sign-in, create additional clients:

- `iOS` client
- `Android` client

Save those Client IDs too.

## 4. Configure backend settings

Add allowed Google client IDs to `JB_DRF_AUTH`:

```python
JB_DRF_AUTH = {
    "SOCIAL_ACCOUNT_MODEL": "authentication.SocialAccount",
    "SOCIAL": {
        "PROVIDERS": {
            "google": {
                "CLASS": "jb_drf_auth.providers.google_oidc.GoogleOidcProvider",
                "CLIENT_ID_WEB": env("GOOGLE_WEB_CLIENT_ID"),
                "CLIENT_ID_IOS": env("GOOGLE_IOS_CLIENT_ID", default=None),
                "CLIENT_ID_ANDROID": env("GOOGLE_ANDROID_CLIENT_ID", default=None),
                "ISSUER": "https://accounts.google.com",
                "JWKS_URL": "https://www.googleapis.com/oauth2/v3/certs",
            },
        },
    },
}
```

Do not use `default=""` for IDs. Use `default=None` for optional IDs.
The library filters/normalizes empty values internally.

## 5. Frontend payloads and redirect_uri rules

`jb-drf-auth` supports two Google flows:

1. `id_token` flow
2. `authorization_code` flow (with optional PKCE)

When using `authorization_code`, send:

- `authorization_code`
- `redirect_uri`
- `client_id`
- `code_verifier` (if PKCE)

Important:

- `redirect_uri` sent to backend must exactly match one Authorized redirect URI configured in Google.
- JavaScript origin must be frontend origin, not your API base URL.

Why multiple keys are supported:

- OIDC validates token audience (`aud`) against allowed client IDs.
- One backend may accept tokens from multiple first-party clients (web/iOS/Android).
- You can set only the keys you use; the library normalizes them internally.

See request examples in:

- `docs/social-auth.md`
- `docs/API_CONTRACT.md`
