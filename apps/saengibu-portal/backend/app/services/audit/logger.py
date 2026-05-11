"""감사 로그 해시 체인 작성기."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Append a log entry. Caller commits."""
    last = await db.scalar(
        select(AuditLog)
        .where(AuditLog.school_id == school_id)
        .order_by(desc(AuditLog.id))
        .limit(1)
    )
    prev_hash = last.content_hash if last else None

    entry = AuditLog(
        school_id=school_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata,
        ip=ip,
        user_agent=user_agent,
        created_at=datetime.now(tz=timezone.utc),
        prev_hash=prev_hash,
    )
    entry.content_hash = entry.compute_hash(prev_hash)
    db.add(entry)
    await db.flush()
    return entry
