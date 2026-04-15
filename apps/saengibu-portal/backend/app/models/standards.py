"""성취기준·활동 태그·학생 특성·즐겨찾기 템플릿·업로드 파일."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class AchievementStandard(Base, TimestampMixin):
    """2022 개정 교육과정 성취기준. 학교 공용 (글로벌)."""

    __tablename__ = "achievement_standards"
    __table_args__ = (UniqueConstraint("curriculum", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    curriculum: Mapped[str] = mapped_column(String(30), nullable=False, default="2022_revised")
    school_level: Mapped[str] = mapped_column(String(10), nullable=False)  # elem/middle/high
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    subject_code: Mapped[str] = mapped_column(String(20), nullable=False)  # 국어/수학/...
    domain: Mapped[str | None] = mapped_column(String(80))  # 대영역 (예: "수와 연산")
    domain_code: Mapped[str | None] = mapped_column(String(20))  # 정규화 영역 코드 ("01" 등)
    unit_code: Mapped[str | None] = mapped_column(String(30))  # "1단원"
    unit_title: Mapped[str | None] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(30), nullable=False)  # "[9수01-01]"
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    eval_scale: Mapped[str] = mapped_column(String(10), nullable=False, default="5grade")
    min_achievement: Mapped[str | None] = mapped_column(String(1))  # 'C' or 'E'
    area_category: Mapped[str | None] = mapped_column(String(20))  # section_types soft link
    source_doc: Mapped[str | None] = mapped_column(String(200))
    source_page: Mapped[int | None] = mapped_column(SmallInteger)
    source_json: Mapped[dict | None] = mapped_column(JSONB)
    rules_version: Mapped[str] = mapped_column(String(20), nullable=False, default="2022-33")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    levels: Mapped[list[AchievementLevel]] = relationship(
        "AchievementLevel", back_populates="standard", cascade="all, delete-orphan",
        order_by="AchievementLevel.order_index.desc()",
    )


class AchievementLevel(Base, TimestampMixin):
    """성취기준별 성취수준 (A/B/C/D/E 또는 A/B/C 또는 P/F)."""

    __tablename__ = "achievement_levels"
    __table_args__ = (UniqueConstraint("standard_id", "level", name="uq_levels_standard_level"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    standard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("achievement_standards.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(1), nullable=False)
    scale: Mapped[str] = mapped_column(String(10), nullable=False)
    descriptor: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cutline_hint: Mapped[str | None] = mapped_column(String(80))
    source_doc: Mapped[str | None] = mapped_column(String(200))
    source_page: Mapped[int | None] = mapped_column(SmallInteger)

    standard: Mapped[AchievementStandard] = relationship(back_populates="levels")


class DomainLevel(Base, TimestampMixin):
    """영역별 성취수준 (성취기준 묶음 단위 종합 수준)."""

    __tablename__ = "domain_levels"
    __table_args__ = (
        UniqueConstraint(
            "curriculum", "school_level", "grade", "subject_code", "domain", "level",
            name="uq_domain_levels_lookup",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    curriculum: Mapped[str] = mapped_column(String(30), nullable=False, default="2022_revised")
    school_level: Mapped[str] = mapped_column(String(10), nullable=False)
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    subject_code: Mapped[str] = mapped_column(String(20), nullable=False)
    domain: Mapped[str] = mapped_column(String(80), nullable=False)
    level: Mapped[str] = mapped_column(String(1), nullable=False)
    descriptor: Mapped[str] = mapped_column(Text, nullable=False)
    source_doc: Mapped[str | None] = mapped_column(String(200))
    source_page: Mapped[int | None] = mapped_column(SmallInteger)


class ActivityTag(Base, TimestampMixin):
    """과목·영역별 활동 태그. 학교 커스터마이즈 가능."""

    __tablename__ = "activity_tags"
    __table_args__ = (UniqueConstraint("school_id", "category", "label"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id")
    )
    subject_code: Mapped[str | None] = mapped_column(String(20))
    section_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("section_types.id")
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    # categories: "수업활동" | "역할수행" | "학생특성" | "성장정도" | "도구활용"
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    synonyms: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    description: Mapped[str | None] = mapped_column(Text)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FavoriteTemplate(Base, TimestampMixin):
    """교사 개인 즐겨찾기 템플릿 (학생 실명은 {{name}} placeholder)."""

    __tablename__ = "favorite_templates"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    section_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("section_types.id"), nullable=False
    )
    subject_code: Mapped[str | None] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[dict | None] = mapped_column(JSONB)
    achievement_standard_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    pin_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class UploadedFile(Base, TimestampMixin):
    """업로드 파일 (hwp/doc/pdf)."""

    __tablename__ = "uploaded_files"
    __table_args__ = (UniqueConstraint("school_id", "sha256"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("records.id")
    )
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_magic_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    av_scan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    av_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")


class AiSuggestion(Base):
    """AI 피드백(= 태그/성취기준/파일 조합의 관점 제시). 문장 생성 아님."""

    __tablename__ = "ai_suggestions"

    id: Mapped[uuid.UUID] = uuid_pk()
    record_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("records.id"), nullable=False
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("record_versions.id")
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    input_tags_json: Mapped[dict | None] = mapped_column(JSONB)
    input_files_json: Mapped[dict | None] = mapped_column(JSONB)
    input_standards_json: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    provider: Mapped[str | None] = mapped_column(String(30))
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    response_json: Mapped[dict | None] = mapped_column(JSONB)
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NoticePost(Base, TimestampMixin):
    """공지·게시판 (학교 공용 or 전역)."""

    __tablename__ = "notice_posts"

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="announcement")
    # announcement | library | training | faq | release
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
