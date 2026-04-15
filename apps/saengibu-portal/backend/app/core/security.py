"""JWT session token + CSRF token + Google ID token verification."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import JWTError, jwt

from app.core.config import get_settings


ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_session_token(
    *,
    user_id: str,
    school_id: str | None,
    roles: list[str],
    status: str,
    csrf: str,
    lifetime: timedelta | None = None,
) -> str:
    settings = get_settings()
    ttl = lifetime or timedelta(hours=settings.refresh_token_expire_hours)
    claims: dict[str, Any] = {
        "sub": user_id,
        "sid": school_id,
        "roles": roles,
        "st": status,
        "csrf": csrf,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + ttl).timestamp()),
        "iss": settings.app_name,
    }
    return jwt.encode(claims, settings.session_secret, algorithm=ALGORITHM)


def decode_session_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.session_secret,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
            issuer=settings.app_name,
        )
    except JWTError as e:
        raise ValueError(f"invalid session token: {e}") from e


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def should_rotate_session(claims: dict[str, Any], threshold_ratio: float = 0.25) -> bool:
    """세션 잔여 수명이 전체의 `threshold_ratio` 미만이면 True.

    예: refresh_token_expire_hours=24, threshold_ratio=0.25 → 잔여 6시간 이하면 갱신.
    """
    iat = claims.get("iat")
    exp = claims.get("exp")
    if not iat or not exp:
        return False
    total = exp - iat
    if total <= 0:
        return False
    remaining = exp - int(_now().timestamp())
    return remaining > 0 and (remaining / total) < threshold_ratio


def verify_google_id_token(credential: str) -> dict[str, Any]:
    """Verify Google ID token and return payload. Raises ValueError on failure."""
    settings = get_settings()
    if not settings.google_client_id:
        raise ValueError("google_client_id is not configured")
    info = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        settings.google_client_id,
        clock_skew_in_seconds=10,
    )
    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("invalid issuer")
    if not info.get("email_verified"):
        raise ValueError("email not verified by Google")
    return info


def check_email_domain(email: str) -> bool:
    settings = get_settings()
    allowed = settings.allowed_domains_list
    if not allowed:
        return True  # dev: 모두 허용
    _, _, domain = email.rpartition("@")
    return domain.lower() in allowed
