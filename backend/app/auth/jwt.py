from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

from app.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(username: str) -> str:
    payload = {
        "sub": username,
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: Literal["access", "refresh"] = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")

    if payload.get("type") != expected_type:
        raise ValueError(f"Expected token type '{expected_type}'")
    return payload
