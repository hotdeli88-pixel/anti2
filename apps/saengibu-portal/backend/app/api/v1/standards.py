"""2022 개정 교육과정 성취기준·성취수준 읽기 전용 API.

Sprint 1 / Plan: tender-questing-sloth
- GET /standards         (필터 + 검색 + cursor)
- GET /standards/{id}    (성취수준 포함)
- GET /standards/{id}/levels
- GET /domain-levels
- GET /curricula         (학교급×학년×과목 매트릭스)
"""
from __future__ import annotations

import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.deps import CurrentUser, current_user
from app.models.standards import AchievementLevel, AchievementStandard, DomainLevel
from app.schemas.standards import (
    AchievementLevelOut,
    AchievementStandardOut,
    CurriculumMatrixEntry,
    DomainLevelOut,
    StandardsListPage,
)

router = APIRouter(prefix="/standards", tags=["standards"])
domain_router = APIRouter(prefix="/domain-levels", tags=["standards"])
curricula_router = APIRouter(prefix="/curricula", tags=["standards"])


def _encode_cursor(last_id: int) -> str:
    return base64.urlsafe_b64encode(str(last_id).encode("ascii")).decode("ascii")


def _decode_cursor(cursor: str | None) -> int | None:
    if not cursor:
        return None
    try:
        return int(base64.urlsafe_b64decode(cursor.encode("ascii")).decode("ascii"))
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"type": "pagination.bad_cursor", "title": "잘못된 cursor"},
        ) from e


@router.get("", response_model=StandardsListPage)
async def list_standards(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    school_level: str | None = Query(None, regex="^(elem|middle|high)$"),
    grade: int | None = Query(None, ge=1, le=6),
    subject: str | None = Query(None, alias="subject", description="과목 코드 (예: 수학, 국어)"),
    search: str | None = Query(None, max_length=80),
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> StandardsListPage:
    last_id = _decode_cursor(cursor)
    stmt = select(AchievementStandard).where(AchievementStandard.active.is_(True))
    if school_level:
        stmt = stmt.where(AchievementStandard.school_level == school_level)
    if grade:
        stmt = stmt.where(AchievementStandard.grade == grade)
    if subject:
        stmt = stmt.where(AchievementStandard.subject_code == subject)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                AchievementStandard.code.ilike(like),
                AchievementStandard.statement.ilike(like),
                AchievementStandard.domain.ilike(like),
            )
        )
    if last_id is not None:
        stmt = stmt.where(AchievementStandard.id > last_id)
    stmt = stmt.order_by(AchievementStandard.id.asc()).limit(limit + 1)

    rows = list(await db.scalars(stmt))
    has_more = len(rows) > limit
    items = rows[:limit]

    out_items = [AchievementStandardOut.model_validate(r) for r in items]
    next_cursor = _encode_cursor(items[-1].id) if has_more and items else None
    return StandardsListPage(items=out_items, next_cursor=next_cursor)


@router.get("/{standard_id}", response_model=AchievementStandardOut)
async def get_standard(
    standard_id: int,
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AchievementStandardOut:
    obj = await db.scalar(
        select(AchievementStandard)
        .where(AchievementStandard.id == standard_id, AchievementStandard.active.is_(True))
        .options(selectinload(AchievementStandard.levels))
    )
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "standard.not_found", "title": "성취기준을 찾을 수 없습니다"},
        )
    return AchievementStandardOut.model_validate(obj)


@router.get("/{standard_id}/levels", response_model=list[AchievementLevelOut])
async def list_levels(
    standard_id: int,
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AchievementLevelOut]:
    rows = await db.scalars(
        select(AchievementLevel)
        .where(AchievementLevel.standard_id == standard_id)
        .order_by(AchievementLevel.order_index.desc())
    )
    return [AchievementLevelOut.model_validate(r) for r in rows]


@domain_router.get("", response_model=list[DomainLevelOut])
async def list_domain_levels(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    school_level: str | None = Query(None, regex="^(elem|middle|high)$"),
    grade: int | None = Query(None, ge=1, le=6),
    subject: str | None = None,
    domain: str | None = None,
) -> list[DomainLevelOut]:
    stmt = select(DomainLevel)
    if school_level:
        stmt = stmt.where(DomainLevel.school_level == school_level)
    if grade:
        stmt = stmt.where(DomainLevel.grade == grade)
    if subject:
        stmt = stmt.where(DomainLevel.subject_code == subject)
    if domain:
        stmt = stmt.where(DomainLevel.domain == domain)
    stmt = stmt.order_by(
        DomainLevel.subject_code,
        DomainLevel.grade,
        DomainLevel.domain,
        DomainLevel.level,
    )
    rows = await db.scalars(stmt)
    return [DomainLevelOut.model_validate(r) for r in rows]


@curricula_router.get("", response_model=list[CurriculumMatrixEntry])
async def curricula_matrix(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CurriculumMatrixEntry]:
    """학교급×학년×과목 매트릭스 (성취기준 수, 성취수준 수)."""
    standards_subq = (
        select(
            AchievementStandard.curriculum,
            AchievementStandard.school_level,
            AchievementStandard.grade,
            AchievementStandard.subject_code,
            func.count(AchievementStandard.id).label("standard_count"),
        )
        .where(AchievementStandard.active.is_(True))
        .group_by(
            AchievementStandard.curriculum,
            AchievementStandard.school_level,
            AchievementStandard.grade,
            AchievementStandard.subject_code,
        )
        .subquery()
    )
    levels_subq = (
        select(
            AchievementStandard.curriculum,
            AchievementStandard.school_level,
            AchievementStandard.grade,
            AchievementStandard.subject_code,
            func.count(AchievementLevel.id).label("level_count"),
        )
        .join(AchievementLevel, AchievementLevel.standard_id == AchievementStandard.id)
        .group_by(
            AchievementStandard.curriculum,
            AchievementStandard.school_level,
            AchievementStandard.grade,
            AchievementStandard.subject_code,
        )
        .subquery()
    )
    rows = await db.execute(
        select(
            standards_subq.c.curriculum,
            standards_subq.c.school_level,
            standards_subq.c.grade,
            standards_subq.c.subject_code,
            standards_subq.c.standard_count,
            func.coalesce(levels_subq.c.level_count, 0),
        ).join(
            levels_subq,
            (standards_subq.c.curriculum == levels_subq.c.curriculum)
            & (standards_subq.c.school_level == levels_subq.c.school_level)
            & (standards_subq.c.grade == levels_subq.c.grade)
            & (standards_subq.c.subject_code == levels_subq.c.subject_code),
            isouter=True,
        ).order_by(
            standards_subq.c.school_level,
            standards_subq.c.grade,
            standards_subq.c.subject_code,
        )
    )
    return [
        CurriculumMatrixEntry(
            curriculum=r[0],
            school_level=r[1],
            grade=r[2],
            subject_code=r[3],
            standard_count=int(r[4] or 0),
            level_count=int(r[5] or 0),
        )
        for r in rows
    ]
