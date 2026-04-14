"""FastAPI dependencies: current_user, rbac guards, tenancy."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db, set_tenant
from app.core.security import decode_session_token
from app.models.user import User
from sqlalchemy import select


class CurrentUser:
    def __init__(self, user: User, roles: list[str], csrf: str) -> None:
        self.user = user
        self.roles = roles
        self.csrf = csrf

    @property
    def id(self) -> uuid.UUID:
        return self.user.id

    @property
    def school_id(self) -> uuid.UUID:
        return self.user.school_id

    def has_any(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)


async def _load_session(
    request: Request,
    settings: Settings,
    db: AsyncSession,
) -> CurrentUser:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "auth.unauthenticated", "title": "로그인이 필요합니다"},
        )
    try:
        claims = decode_session_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "auth.invalid_token", "title": str(e)},
        ) from e

    # CSRF: non-safe methods must match cookie
    method = request.method.upper()
    if method not in ("GET", "HEAD", "OPTIONS"):
        header_csrf = request.headers.get("x-csrf-token")
        if not header_csrf or header_csrf != claims.get("csrf"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"type": "auth.csrf_mismatch", "title": "CSRF 토큰 불일치"},
            )

    user_id = uuid.UUID(claims["sub"])
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user or user.status not in ("active", "pending"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "auth.user_gone", "title": "계정을 찾을 수 없습니다"},
        )

    # Tenancy: Postgres RLS scope
    await set_tenant(db, user.school_id)

    return CurrentUser(user=user, roles=list(claims.get("roles", [])), csrf=claims["csrf"])


async def current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    cu = await _load_session(request, settings, db)
    if cu.user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"type": "auth.account_pending", "title": "관리자 승인 대기 중"},
        )
    return cu


async def current_user_any_status(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    """For /auth/me, /auth/logout — allow pending status."""
    return await _load_session(request, settings, db)


def require_roles(*roles: str):
    async def _dep(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
        if not user.has_any(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"type": "rbac.forbidden", "title": "권한이 없습니다"},
            )
        return user

    return _dep
