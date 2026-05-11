"""대시보드 통계."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import CurrentUser, current_user
from app.models.feedback import FeedbackReport
from app.models.record import Record
from app.models.review import Review, ReviewStep
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/teacher", response_model=DashboardStats)
async def teacher_dashboard(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    # 승인 대기 중 — 내가 결재할 step
    pending = await db.scalar(
        select(func.count())
        .select_from(ReviewStep)
        .join(Review, ReviewStep.review_id == Review.id)
        .join(Record, Review.record_id == Record.id)
        .where(
            Review.status == "in_progress",
            ReviewStep.decision.is_(None),
            ReviewStep.expected_role.in_(user.roles or ["homeroom"]),
            Record.school_id == user.school_id,
        )
    )

    week_ago = datetime.now(tz=timezone.utc) - timedelta(days=7)
    approved_week = await db.scalar(
        select(func.count())
        .select_from(Record)
        .where(
            Record.school_id == user.school_id,
            Record.status == "approved",
            Record.updated_at >= week_ago,
        )
    )

    ai_corr = await db.scalar(
        select(func.count())
        .select_from(FeedbackReport)
        .where(
            FeedbackReport.total_warnings > 0,
            FeedbackReport.created_at >= week_ago,
        )
    )

    return DashboardStats(
        pending_approvals=int(pending or 0),
        approved_this_week=int(approved_week or 0),
        ai_corrections=int(ai_corr or 0),
    )
