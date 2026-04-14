"""학교·학년도·학년·학급·교과."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_pk


class School(Base, TimestampMixin):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = uuid_pk()
    neis_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="middle")
    principal_name: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(300))


class AcademicYear(Base):
    __tablename__ = "academic_years"
    __table_args__ = (UniqueConstraint("school_id", "year"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("year_id", "grade_num"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    year_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    grade_num: Mapped[int] = mapped_column(Integer, nullable=False)


class Class(Base):
    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("grade_id", "class_num"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    grade_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False
    )
    class_num: Mapped[int] = mapped_column(Integer, nullable=False)


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("school_id", "code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
