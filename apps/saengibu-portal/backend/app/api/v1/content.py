"""기재요령 안내·학교 결정사항 (콘텐츠 API)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import CurrentUser, current_user
from app.models.guideline import Guideline, SchoolDecision
from app.schemas.guideline import GuidelineOut, SchoolDecisionOut

router = APIRouter(tags=["content"])


@router.get("/guidelines", response_model=list[GuidelineOut])
async def list_guidelines(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Guideline]:
    rows = await db.scalars(
        select(Guideline).where(Guideline.active.is_(True)).order_by(Guideline.order_index)
    )
    return list(rows)


@router.get("/school-decisions", response_model=list[SchoolDecisionOut])
async def list_decisions(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SchoolDecision]:
    rows = await db.scalars(
        select(SchoolDecision)
        .where(
            SchoolDecision.school_id == user.school_id,
            SchoolDecision.active.is_(True),
        )
        .order_by(SchoolDecision.effective_date.desc())
    )
    return list(rows)
