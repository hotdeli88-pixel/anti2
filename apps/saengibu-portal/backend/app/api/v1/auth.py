"""Google OAuth + 세션 + 승인제."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import clear_session_cookies, set_session_cookies
from app.core.db import get_db, set_tenant
from app.core.deps import CurrentUser, current_user_any_status
from app.core.security import (
    check_email_domain,
    create_session_token,
    generate_csrf_token,
    verify_google_id_token,
)
from app.models.school import School
from app.models.user import RoleAssignment, User, UserApproval
from app.schemas.auth import GoogleLoginRequest, MeResponse, SchoolRef
from app.services.audit.logger import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


async def _active_roles(db: AsyncSession, user_id) -> list[str]:
    rows = await db.scalars(
        select(RoleAssignment).where(
            RoleAssignment.user_id == user_id, RoleAssignment.ended_at.is_(None)
        )
    )
    return [r.role for r in rows]


async def _build_me(db: AsyncSession, user: User) -> MeResponse:
    school = await db.scalar(select(School).where(School.id == user.school_id))
    roles = await _active_roles(db, user.id)
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        status=user.status,
        roles=roles,
        school=SchoolRef(id=school.id, name=school.name) if school else SchoolRef(
            id=user.school_id, name="(미확인 학교)"
        ),
    )


@router.post("/google", response_model=MeResponse)
async def google_login(
    payload: GoogleLoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    """Google ID Token 검증 → 사용자 조회/생성 → 세션 발급."""
    try:
        info = verify_google_id_token(payload.credential)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "auth.google_invalid", "title": str(e)},
        ) from e

    email: str = info["email"].lower()
    google_sub: str = info["sub"]

    if not check_email_domain(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "auth.domain_forbidden",
                "title": "학교 도메인 이메일만 허용됩니다",
                "detail": f"허용되지 않는 도메인: {email}",
            },
        )

    # 기존 사용자 조회 (google_sub 우선, 이메일 fallback)
    user: User | None = await db.scalar(select(User).where(User.google_sub == google_sub))
    if not user:
        user = await db.scalar(select(User).where(User.email == email))

    if not user:
        # 첫 가입: pending 상태로 생성. 학교 매핑은 "기본 학교"에 귀속 (단일 학교 배포 전제).
        default_school = await db.scalar(select(School).limit(1))
        if not default_school:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"type": "setup.no_school", "title": "학교가 설정되지 않았습니다"},
            )
        user = User(
            school_id=default_school.id,
            email=email,
            name=info.get("name") or email.split("@")[0],
            google_sub=google_sub,
            picture_url=info.get("picture"),
            status="pending",
        )
        db.add(user)
        await db.flush()
        db.add(UserApproval(user_id=user.id))
    else:
        # 기존 사용자: google_sub 바인딩 갱신
        user.google_sub = google_sub
        if info.get("picture"):
            user.picture_url = info["picture"]

    user.last_login_at = datetime.now(tz=timezone.utc)

    await set_tenant(db, user.school_id)
    roles = await _active_roles(db, user.id)

    csrf = generate_csrf_token()
    token = create_session_token(
        user_id=str(user.id),
        school_id=str(user.school_id),
        roles=roles,
        status=user.status,
        csrf=csrf,
    )
    set_session_cookies(response, token, csrf)

    await write_audit(
        db,
        school_id=user.school_id,
        user_id=user.id,
        action="auth.google_login",
        resource_type="user",
        resource_id=user.id,
        metadata={"status": user.status, "email": email},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    return await _build_me(db, user)


@router.get("/me", response_model=MeResponse)
async def me(
    user: Annotated[CurrentUser, Depends(current_user_any_status)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    return await _build_me(db, user.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Clear cookies. Best-effort audit if valid session."""
    from app.core.config import get_settings
    from app.core.db import set_tenant
    from app.core.security import decode_session_token

    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        try:
            claims = decode_session_token(token)
            user_id = uuid.UUID(claims["sub"])
            school_id = uuid.UUID(claims["sid"]) if claims.get("sid") else None
            if school_id:
                await set_tenant(db, school_id)
                await write_audit(
                    db,
                    school_id=school_id,
                    user_id=user_id,
                    action="auth.logout",
                    resource_type="user",
                    resource_id=user_id,
                    ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                await db.commit()
        except Exception:  # noqa: S110 — best-effort
            pass
    clear_session_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
