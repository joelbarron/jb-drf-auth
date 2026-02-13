#!/usr/bin/env python3
"""Generate APPLE_CLIENT_SECRET JWT for Sign in with Apple."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

"""Usage:
  python generate_apple_client_secret.py \
    --team-id YOUR_TEAM_ID \
    --client-id YOUR_CLIENT_ID \
    --key-id YOUR_KEY_ID \
    --key-file /path/to/AuthKey_XXXXXX.p8 \
    --expires-in-seconds 15777000
"""

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate APPLE_CLIENT_SECRET (ES256 JWT) from an Apple .p8 key."
    )
    parser.add_argument("--team-id", required=True, help="Apple Team ID (iss)")
    parser.add_argument("--client-id", required=True, help="Services ID or Bundle ID (sub)")
    parser.add_argument("--key-id", required=True, help="Apple Key ID (kid)")
    parser.add_argument("--key-file", required=True, help="Path to AuthKey_XXXXXX.p8")
    parser.add_argument(
        "--expires-in-seconds",
        type=int,
        default=15777000,  # ~6 months
        help="JWT lifetime in seconds (Apple allows up to 15777000).",
    )
    return parser.parse_args()


def generate_client_secret(
    *,
    team_id: str,
    client_id: str,
    key_id: str,
    key_file: str,
    expires_in_seconds: int,
) -> str:
    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT is required. Install with: pip install 'PyJWT[crypto]>=2.7,<3'"
        ) from exc

    now = int(time.time())
    expiration = now + expires_in_seconds
    private_key = Path(key_file).read_text(encoding="utf-8")

    return jwt.encode(
        payload={
            "iss": team_id,
            "iat": now,
            "exp": expiration,
            "aud": "https://appleid.apple.com",
            "sub": client_id,
        },
        key=private_key,
        algorithm="ES256",
        headers={"kid": key_id},
    )


def main() -> None:
    args = parse_args()

    if args.expires_in_seconds <= 0:
        raise SystemExit("--expires-in-seconds must be greater than 0")
    if args.expires_in_seconds > 15777000:
        raise SystemExit("--expires-in-seconds must be <= 15777000 (~6 months)")

    token = generate_client_secret(
        team_id=args.team_id.strip(),
        client_id=args.client_id.strip(),
        key_id=args.key_id.strip(),
        key_file=args.key_file.strip(),
        expires_in_seconds=args.expires_in_seconds,
    )
    print(token)


if __name__ == "__main__":
    main()
