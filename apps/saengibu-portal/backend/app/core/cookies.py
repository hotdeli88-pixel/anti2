"""httpOnly 쿠키 셋업 유틸."""
from __future__ import annotations

from fastapi import Response

from app.core.config import get_settings


def set_session_cookies(response: Response, token: str, csrf: str) -> None:
    settings = get_settings()
    common: dict = {
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "domain": settings.cookie_domain,
        "path": "/",
    }
    # 세션: httpOnly
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        max_age=settings.refresh_token_expire_hours * 3600,
        **common,
    )
    # CSRF: JS에서 읽어 헤더에 실어야 하므로 httpOnly=False (이중 제출)
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf,
        httponly=False,
        max_age=settings.refresh_token_expire_hours * 3600,
        **common,
    )


def clear_session_cookies(response: Response) -> None:
    settings = get_settings()
    common: dict = {
        "domain": settings.cookie_domain,
        "path": "/",
    }
    response.delete_cookie(settings.session_cookie_name, **common)
    response.delete_cookie(settings.csrf_cookie_name, **common)
