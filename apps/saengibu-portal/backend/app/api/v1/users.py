"""사용자 관리 — 승인·역할 부여 (관리자 전용)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import CurrentUser, require_roles
from app.models.user import RoleAssignment, User, UserApproval
from app.schemas.auth import UserApprovalDecision
from app.services.audit.logger import write_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/pending")
async def list_pending(
    admin: Annotated[CurrentUser, Depends(require_roles("admin", "principal", "vice_principal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    users = await db.scalars(
        select(User).where(
            User.school_id == admin.school_id, User.status == "pending"
        )
    )
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "employee_no": u.employee_no,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/{user_id}/approval")
async def decide_approval(
    user_id: uuid.UUID,
    payload: UserApprovalDecision,
    request: Request,
    admin: Annotated[CurrentUser, Depends(require_roles("admin", "principal", "vice_principal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    target = await db.scalar(select(User).where(User.id == user_id))
    if not target or target.school_id != admin.school_id:
        raise HTTPException(status_code=404, detail={"type": "user.not_found"})
    if target.status != "pending":
        raise HTTPException(
            status_code=409,
            detail={"type": "user.already_decided", "title": f"이미 {target.status} 상태"},
        )

    approval = await db.scalar(
        select(UserApproval).where(UserApproval.user_id == user_id)
    )
    now = datetime.now(tz=timezone.utc)

    if payload.decision == "approved":
        target.status = "active"
        if approval:
            approval.approver_id = admin.id
            approval.approved_at = now
            approval.reason = payload.reason
        if payload.role:
            db.add(
                RoleAssignment(
                    user_id=target.id,
                    role=payload.role,
                    started_at=now,
                )
            )
    else:
        target.status = "suspended"
        if approval:
            approval.approver_id = admin.id
            approval.rejected_at = now
            approval.reason = payload.reason

    await write_audit(
        db,
        school_id=admin.school_id,
        user_id=admin.id,
        action=f"user.{payload.decision}",
        resource_type="user",
        resource_id=target.id,
        metadata={"role": payload.role, "reason": payload.reason},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return {"status": target.status}
