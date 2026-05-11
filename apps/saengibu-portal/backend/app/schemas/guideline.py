from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel


class GuidelineOut(BaseModel):
    id: UUID
    title: str
    icon: str
    body_markdown: str
    reference: str

    class Config:
        from_attributes = True


class SchoolDecisionOut(BaseModel):
    id: UUID
    title: str
    severity: str
    body_markdown: str
    effective_date: date
    posted_by: str

    class Config:
        from_attributes = True
