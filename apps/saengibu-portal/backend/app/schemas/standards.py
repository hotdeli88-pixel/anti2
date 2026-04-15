"""성취기준·성취수준·영역수준 Pydantic 스키마 (Sprint 1)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Scale = Literal["5grade", "3grade", "P/F"]
Level = Literal["A", "B", "C", "D", "E", "P", "F"]
SchoolLevel = Literal["elem", "middle", "high"]


class AchievementLevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: Level
    scale: Scale
    descriptor: str
    order_index: int = Field(..., description="A=5..E=1, P=2/F=1")
    cutline_hint: str | None = None


class AchievementStandardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    curriculum: str
    school_level: SchoolLevel
    grade: int
    subject_code: str
    domain: str | None = None
    domain_code: str | None = None
    unit_code: str | None = None
    unit_title: str | None = None
    code: str
    statement: str
    eval_scale: Scale
    min_achievement: Level | None = None
    rules_version: str
    levels: list[AchievementLevelOut] = Field(default_factory=list)


class StandardsListPage(BaseModel):
    items: list[AchievementStandardOut]
    next_cursor: str | None = None


class DomainLevelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    curriculum: str
    school_level: SchoolLevel
    grade: int
    subject_code: str
    domain: str
    level: Level
    descriptor: str


class CurriculumMatrixEntry(BaseModel):
    curriculum: str
    school_level: SchoolLevel
    grade: int
    subject_code: str
    standard_count: int
    level_count: int
