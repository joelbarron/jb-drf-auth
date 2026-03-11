#!/usr/bin/env python3
"""
Basic guardrail to keep API docs and Postman collections in sync with public URLs.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "API_CONTRACT.md"
SNAKE_COLLECTION_PATH = ROOT / "docs" / "API.postman_collection.json"
CAMEL_COLLECTION_PATH = ROOT / "docs" / "API.camel.postman_collection.json"

# Keep this list aligned with jb_drf_auth/urls.py public endpoints.
EXPECTED_ENDPOINTS = [
    "admin/create-superuser/",
    "admin/create-staff/",
    "register/",
    "registration/account-confirmation-email/",
    "registration/account-confirmation-email/resend/",
    "password-reset/request/",
    "password-reset/confirm/",
    "password-reset/change/",
    "login/basic/",
    "login/social/",
    "login/social/link/",
    "login/social/unlink/",
    "otp/request/",
    "otp/verify/",
    "profile/switch/",
    "profile/picture/",
    "me/",
    "token/refresh/",
    "account/update/",
    "account/delete/",
    "profiles/",
]


def _flatten_items(items):
    for item in items:
        request = item.get("request")
        if request:
            yield item
        for nested in _flatten_items(item.get("item", [])):
            yield nested


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_collection_urls(collection_data):
    urls = []
    for item in _flatten_items(collection_data.get("item", [])):
        request = item.get("request", {})
        raw = request.get("url", {}).get("raw")
        if raw:
            urls.append(raw)
    return urls


def main():
    errors = []

    for path in (SNAKE_COLLECTION_PATH, CAMEL_COLLECTION_PATH):
        if not path.exists():
            errors.append(f"Missing file: {path}")

    if not CONTRACT_PATH.exists():
        errors.append(f"Missing file: {CONTRACT_PATH}")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
    snake_collection = _load_json(SNAKE_COLLECTION_PATH)
    camel_collection = _load_json(CAMEL_COLLECTION_PATH)

    snake_urls = _get_collection_urls(snake_collection)
    camel_urls = _get_collection_urls(camel_collection)

    for endpoint in EXPECTED_ENDPOINTS:
        contract_probe = f"/auth/{endpoint}"
        if contract_probe not in contract_text:
            errors.append(f"Contract is missing endpoint: {contract_probe}")

        if not any(f"/{endpoint}" in raw for raw in snake_urls):
            errors.append(f"Snake Postman collection is missing endpoint: /{endpoint}")

        if not any(f"/{endpoint}" in raw for raw in camel_urls):
            errors.append(f"Camel Postman collection is missing endpoint: /{endpoint}")

    snake_text = SNAKE_COLLECTION_PATH.read_text(encoding="utf-8")
    camel_text = CAMEL_COLLECTION_PATH.read_text(encoding="utf-8")
    if "notification_token" not in snake_text:
        errors.append("Snake collection should use snake_case keys (missing notification_token).")
    if "notificationToken" not in camel_text:
        errors.append("Camel collection should use camelCase keys (missing notificationToken).")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    print("API docs consistency check passed.")


if __name__ == "__main__":
    main()

