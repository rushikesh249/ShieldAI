"""
ShieldAI Backend — Pure Python JWT Utilities

Provides encoding and decoding of HS256 JWT access tokens.
Requires no external library dependencies.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def base64url_encode(data: bytes) -> str:
    """Encode bytes to a base64url string without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def base64url_decode(s: str) -> bytes:
    """Decode a base64url string, adding required padding."""
    rem = len(s) % 4
    if rem > 0:
        s += "=" * (4 - rem)
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def create_access_token(data: dict, expires_delta: float | None = None) -> str:
    """
    Generate an HS256-signed JWT access token.

    Args:
        data: The payload dictionary containing claims.
        expires_delta: Optional expiration time delta in seconds.
                       If not provided, uses jwt_expiration_minutes from settings.
    """
    settings = get_settings()
    secret = settings.jwt_secret or "development-jwt-secret-key-for-shieldai-hackathon"

    to_encode = data.copy()
    if expires_delta is not None:
        expire = time.time() + expires_delta
    else:
        expire = time.time() + (settings.jwt_expiration_minutes or 30) * 60

    to_encode.update({"exp": int(expire)})

    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    header_b64 = base64url_encode(header_json)
    payload_b64 = base64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict | None:
    """
    Verify the signature, algorithm, and expiration of a JWT access token.

    Returns:
        The decoded payload dictionary if valid, or None if validation fails.
    """
    settings = get_settings()
    secret = settings.jwt_secret or "development-jwt-secret-key-for-shieldai-hackathon"

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = hmac.new(
            secret.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()
        expected_signature_b64 = base64url_encode(expected_signature)

        if not hmac.compare_digest(
            expected_signature_b64.encode("utf-8"), signature_b64.encode("utf-8")
        ):
            logger.warning("JWT signature mismatch")
            return None

        # Verify algorithm
        header = json.loads(base64url_decode(header_b64).decode("utf-8"))
        if header.get("alg") != "HS256":
            logger.warning("Unsupported JWT algorithm: %s", header.get("alg"))
            return None

        # Parse and return payload
        payload = json.loads(base64url_decode(payload_b64).decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp is not None and exp < time.time():
            logger.warning("JWT token has expired")
            return None

        return payload
    except Exception as e:
        logger.error("Error decoding JWT token: %s", str(e))
        return None
