"""기록·버전·영역 타입."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk


class SectionType(Base):
    __tablename__ = "section_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    neis_area: Mapped[str] = mapped_column(String(30), nullable=False)
    byte_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_limit_basis: Mapped[str] = mapped_column(String(20), nullable=False)
    input_role: Mapped[str] = mapped_column(String(30), nullable=False)
    style_rule_set: Mapped[str] = mapped_column(String(30), nullable=False, default="nouning_end")
    neis_prefix_rule: Mapped[dict | None] = mapped_column(JSONB)
    retention_policy: Mapped[str] = mapped_column(String(30), nullable=False, default="permanent")
    updated_in_2026: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Record(Base, TimestampMixin):
    __tablename__ = "records"
    __table_args__ = (
        UniqueConstraint("student_id", "year_id", "section_type_id", "subject_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    year_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    section_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("section_types.id"), nullable=False
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("subjects.id")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("record_versions.id", use_alter=True, deferrable=True, initially="DEFERRED"),
    )
    retention_until: Mapped[date | None] = mapped_column(Date)
    retention_reason: Mapped[str | None] = mapped_column(String(50))
    neis_prefix: Mapped[str | None] = mapped_column(String(50))


class RecordVersion(Base):
    __tablename__ = "record_versions"
    __table_args__ = (UniqueConstraint("record_id", "version_no"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    record_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("records.id", ondelete="CASCADE"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    byte_count: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
