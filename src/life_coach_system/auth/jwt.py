"""JWT token creation and verification."""

from datetime import datetime, timedelta, timezone

import jwt

from life_coach_system.config import settings
from life_coach_system.exceptions import AuthenticationError

__all__ = ["create_access_token", "decode_access_token"]


def create_access_token(
    *,
    user_id: str,
    email: str | None = None,
    name: str | None = None,
    provider: str | None = None,
) -> str:
    """Create a signed JWT containing user claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "provider": provider,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises AuthenticationError on failure."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid token: {exc}") from exc
