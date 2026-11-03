"""Authentication primitives for DPY Core.

Secrets are environment-supplied and the module fails closed. The previous
version fell back to a literal string when SECRET_KEY was unset, which allowed
anyone reading the repository to mint valid tokens for a deployment that
forgot the variable.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 14
MIN_SECRET_LENGTH = 32


class SecurityConfigError(RuntimeError):
    """Raised when the deployment is missing required secret material."""


def _secret_key() -> str:
    secret = os.getenv("SECRET_KEY")
    if not secret or len(secret) < MIN_SECRET_LENGTH:
        raise SecurityConfigError(
            "SECRET_KEY is missing or shorter than "
            f"{MIN_SECRET_LENGTH} characters; set it via the environment "
            "(render.yaml generates one at deploy time)"
        )
    return secret


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def _encode(subject: str, minutes: int, token_type: str, extra: Optional[dict] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token from a claims dict containing 'sub'."""
    payload = dict(data)
    subject = payload.pop("sub", None)
    if subject is None:
        raise SecurityConfigError("access token requires a 'sub' claim")
    if expires_delta is not None:
        minutes = int(expires_delta.total_seconds() // 60)
    else:
        minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    return _encode(subject, minutes, "access", payload or None)


def create_refresh_token(subject: str) -> str:
    """Create a refresh token used to rotate short-lived access tokens."""
    return _encode(subject, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60, "refresh")


def decode_token_payload(token: str, expected_type: Optional[str] = "access") -> dict:
    """Decode and verify a token, returning its claims."""
    payload = jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise JWTError(f"expected {expected_type} token")
    return payload


def decode_token(token: str) -> Optional[str]:
    """Decode a JWT access token and return the subject email, or None."""
    try:
        payload = decode_token_payload(token, expected_type="access")
        return payload.get("sub")
    except JWTError:
        return None


def rotate_access_token(refresh_token: str) -> tuple:
    """Exchange a refresh token for a fresh access and refresh pair."""
    payload = decode_token_payload(refresh_token, expected_type="refresh")
    subject = payload.get("sub")
    if not subject:
        raise JWTError("refresh token missing subject")
    return create_access_token({"sub": subject}), create_refresh_token(subject)
