# Documentation

This folder contains the complete documentation for `jb-drf-auth`.

- `getting-started.md`: installation, settings, models, admin, URLs, tests.
- `social-auth.md`: social login setup (Google/Apple OIDC), backend config, frontend flow.
- `API_CONTRACT.md`: formal API contract with request/response/error codes.
- `API.postman_collection.json`: Postman collection using snake_case payloads.
- `API.camel.postman_collection.json`: Postman collection using camelCase payloads.
- `migration.md`: migration guide for existing projects and production-safe rollout.
- `i18n.md`: project integration guide for translated API messages.
- `release.md`: release process (TestPyPI/PyPI).

Postman URL pattern in both collections:

- `{{host}}{{basePath}}/register/`
- Set `basePath` to `/auth` (default) or `/` when endpoints are mounted at root.

Additional repo-level docs:

- `../roadmap.md`: planned and completed work.
