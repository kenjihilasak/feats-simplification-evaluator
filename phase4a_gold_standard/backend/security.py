"""Password hashing and signed session-cookie helpers using only stdlib."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from typing import Any


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, *, iterations: int = PASSWORD_ITERATIONS) -> str:
    if len(password) < 12:
        raise ValueError("passwords must contain at least 12 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{PASSWORD_ALGORITHM}${iterations}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, expected_text = encoded.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_text)
        if iterations < 100_000:
            return False
        salt = _b64decode(salt_text)
        expected = _b64decode(expected_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(24)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sign_cookie(session_token: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), session_token.encode("utf-8"), hashlib.sha256)
    return f"{session_token}.{_b64encode(signature.digest())}"


def unsign_cookie(cookie: str, secret: str) -> str | None:
    try:
        session_token, supplied = cookie.rsplit(".", 1)
        expected = hmac.new(
            secret.encode("utf-8"), session_token.encode("utf-8"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_b64decode(supplied), expected):
            return None
        return session_token
    except (AttributeError, ValueError):
        return None


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    username: str
    display_name: str
    role: str
    allowed_languages: tuple[str, ...] | None
    csrf_token: str
