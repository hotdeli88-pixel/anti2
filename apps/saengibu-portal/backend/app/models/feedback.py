"""AI 피드백 리포트·위반."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uuid_pk


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class FeedbackReport(Base):
    __tablename__ = "feedback_reports"

    id: Mapped[uuid.UUID] = uuid_pk()
    version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("record_versions.id"), nullable=False, unique=True
    )
    stage_byte: Mapped[dict | None] = mapped_column(JSONB)
    stage_banned: Mapped[dict | None] = mapped_column(JSONB)
    stage_style: Mapped[dict | None] = mapped_column(JSONB)
    stage_repeat: Mapped[dict | None] = mapped_column(JSONB)
    stage_llm: Mapped[dict | None] = mapped_column(JSONB)
    stage_llm_status: Mapped[str] = mapped_column(String(20), nullable=False, default="skipped")
    stage_checklist: Mapped[dict | None] = mapped_column(JSONB)
    total_violations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_warnings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        server_default=func.now(),
    )


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = uuid_pk()
    report_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("feedback_reports.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(80), nullable=False)
    span_start: Mapped[int | None] = mapped_column(Integer)
    span_end: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(200))
