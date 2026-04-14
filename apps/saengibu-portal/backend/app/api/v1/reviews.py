"""검토(1/2/3검) API."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.deps import CurrentUser, current_user
from app.models.feedback import FeedbackReport
from app.models.record import Record, RecordVersion, SectionType
from app.models.review import Review, ReviewComment, ReviewStep
from app.models.school import AcademicYear, Class, Grade
from app.models.student import Enrollment, Student
from app.models.user import User
from app.schemas.record import (
    ApprovalItem,
    AuthorRef,
    DecideRequest,
    SectionInfo,
    StudentRef,
)
from app.services.audit.logger import write_audit
from app.services.mask.pii import mask_name_display
from app.services.workflow.fsm import Event, next_status, step_no_for

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/assigned", response_model=list[ApprovalItem])
async def assigned_to_me(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
) -> list[ApprovalItem]:
    """내가 결재해야 할 목록. 역할·scope 기반으로 결정."""
    # MVP: 진행 중 reviews 중 step.expected_role이 내 역할에 포함 + 스코프 매칭
    base = (
        select(Review, ReviewStep, Record, Student, Enrollment, Class, Grade, SectionType, User, FeedbackReport)
        .join(ReviewStep, ReviewStep.review_id == Review.id)
        .join(Record, Review.record_id == Record.id)
        .join(Student, Record.student_id == Student.id)
        .join(
            Enrollment,
            and_(Enrollment.student_id == Student.id, Enrollment.year_id == Record.year_id),
            isouter=True,
        )
        .join(Class, Enrollment.class_id == Class.id, isouter=True)
        .join(Grade, Class.grade_id == Grade.id, isouter=True)
        .join(SectionType, Record.section_type_id == SectionType.id)
        .join(User, Record.author_id == User.id)
        .join(FeedbackReport, FeedbackReport.version_id == Review.version_id, isouter=True)
        .where(
            Review.status == "in_progress",
            ReviewStep.decision.is_(None),
            ReviewStep.expected_role.in_(user.roles or ["homeroom"]),
            Record.school_id == user.school_id,
        )
        .order_by(Review.created_at.desc())
    )

    rows = await db.execute(base)
    items: list[ApprovalItem] = []
    seen: set[uuid.UUID] = set()
    for review, step, record, student, _enr, klass, grade, section, author, fb in rows:
        if review.id in seen:
            continue
        seen.add(review.id)
        status_val = "pending"
        if fb and fb.total_warnings > 0 and fb.total_violations == 0:
            status_val = "guide_correction"
        # status filter
        if status_filter and status_val != status_filter:
            continue
        items.append(
            ApprovalItem(
                review_id=review.id,
                record_id=record.id,
                step_no=step.step_no,
                student=StudentRef(
                    id=student.id,
                    name_masked=mask_name_display(student.name),
                    grade=grade.grade_num if grade else 0,
                    class_no=klass.class_num if klass else 0,
                ),
                section=SectionInfo(
                    code=section.code, name=section.name, byte_limit=section.byte_limit
                ),
                author=AuthorRef(id=author.id, name=author.name),
                submitted_at=review.created_at,
                status=status_val,
                ai_warn_count=fb.total_warnings if fb else 0,
            )
        )
    return items


@router.post("/{review_id}/steps/{step_no}/decide")
async def decide_step(
    review_id: uuid.UUID,
    step_no: int,
    payload: DecideRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    review = await db.scalar(
        select(Review).where(Review.id == review_id).options(selectinload(Review.steps))
    )
    if not review:
        raise HTTPException(status_code=404, detail={"type": "review.not_found"})

    record = await db.scalar(select(Record).where(Record.id == review.record_id))
    if not record or record.school_id != user.school_id:
        raise HTTPException(status_code=403, detail={"type": "rbac.forbidden"})

    step = next((s for s in review.steps if s.step_no == step_no), None)
    if not step:
        raise HTTPException(status_code=404, detail={"type": "review.step_not_found"})
    if step.decision is not None:
        raise HTTPException(
            status_code=409, detail={"type": "review.already_decided"}
        )

    # 현재 record.status 가 이 step에 해당해야
    expected_status = {1: "review_1", 2: "review_2", 3: "review_3"}.get(step_no)
    if record.status != expected_status:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "workflow.invalid_transition",
                "title": f"현재 상태({record.status})에서는 {step_no}검 결재가 불가합니다",
            },
        )

    if payload.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail={"type": "decision.invalid"})

    # RBAC: expected_role 매칭
    if step.expected_role not in user.roles and "admin" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail={"type": "rbac.wrong_role", "title": "이 단계의 검토자가 아닙니다"},
        )

    now = datetime.now(tz=timezone.utc)
    step.decision = payload.decision
    step.decided_at = now
    step.reviewer_id = user.id

    if payload.decision == "approved":
        event = Event.APPROVE
    else:
        event = Event.REJECT
        if not payload.comment:
            raise HTTPException(
                status_code=422,
                detail={"type": "review.comment_required", "title": "반려 시 사유 필수"},
            )

    try:
        record.status = next_status(record.status, event).value
    except Exception as e:
        raise HTTPException(status_code=409, detail={"type": "workflow.error", "title": str(e)}) from e

    if payload.decision == "rejected":
        # 하위 step 결과도 무효화 (재제출 시 1검부터)
        for s in review.steps:
            if s.step_no <= step_no:
                s.decision = None
                s.decided_at = None
        review.status = "rejected"
        review.closed_at = now
        db.add(
            ReviewComment(
                step_id=step.id, author_id=user.id, body=payload.comment or ""
            )
        )
    elif payload.decision == "approved" and step_no == 3:
        review.status = "approved"
        review.closed_at = now

    await write_audit(
        db,
        school_id=user.school_id,
        user_id=user.id,
        action=f"review.{payload.decision}",
        resource_type="review_step",
        resource_id=step.id,
        metadata={
            "record_id": str(record.id),
            "step_no": step_no,
            "has_comment": bool(payload.comment),
        },
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return {"status": record.status}
