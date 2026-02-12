# Facebook OAuth Setup (Web + Mobile)

This guide explains how to create Facebook credentials for `jb-drf-auth` social login.

Use this together with `social-auth.md`.

## 1. Create Meta app

1. Go to Meta for Developers.
2. Create a new app (typically `Consumer` type).
3. Save the `App ID` and `App Secret`.

## 2. Add Facebook Login product

1. In your app dashboard, add the `Facebook Login` product.
2. Enable the platforms you need:
   - Web
   - iOS / Android (if applicable)

## 3. Configure app domains and callback URLs

In Facebook Login settings:

1. Add your frontend domains (example: `localhost`, `app.example.com`).
2. Configure `Valid OAuth Redirect URIs` for your frontend callback routes.
3. Keep callback URIs aligned with your frontend SDK flow.

Notes:

- For `jb-drf-auth`, backend login uses `access_token` from frontend.
- The backend does not require a backend redirect callback endpoint for Facebook.

## 4. Request scopes

For standard profile + email, request:

- `public_profile`
- `email`

## 5. Configure backend settings

```python
JB_DRF_AUTH = {
    "SOCIAL_ACCOUNT_MODEL": "authentication.SocialAccount",
    "SOCIAL": {
        "PROVIDERS": {
            "facebook": {
                "CLASS": "jb_drf_auth.providers.facebook_oauth.FacebookOAuthProvider",
                "APP_ID": env("FACEBOOK_APP_ID"),
                "APP_SECRET": env("FACEBOOK_APP_SECRET"),
                "GRAPH_API_VERSION": "v21.0",
                "ASSUME_EMAIL_VERIFIED": True,
            },
        },
    },
}
```

Do not use `default=""` for credentials. If you define defaults, prefer `None`.

## 6. Frontend payload to backend

After frontend login success, send:

```json
{
  "provider": "facebook",
  "access_token": "<facebook_user_access_token>",
  "client": "web"
}
```

Optional fields like `role` and `device` follow the same rules documented in `social-auth.md`.

## 7. Common failure checks

If backend returns `social_token_exchange_failed` or `social_identity_invalid`, verify:

1. App is in correct mode (development/live) and your test user has access.
2. `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` match the same Meta app.
3. Frontend token belongs to that same app.
4. Requested scopes include `email` when your flow expects email linking.
