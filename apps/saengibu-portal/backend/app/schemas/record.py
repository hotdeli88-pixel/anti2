from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SectionInfo(BaseModel):
    code: str
    name: str
    byte_limit: int


class StudentRef(BaseModel):
    id: UUID
    name_masked: str
    grade: int
    class_no: int


class AuthorRef(BaseModel):
    id: UUID
    name: str


class ApprovalItem(BaseModel):
    review_id: UUID
    record_id: UUID
    step_no: int
    student: StudentRef
    section: SectionInfo
    author: AuthorRef
    submitted_at: datetime
    status: str
    ai_warn_count: int


class RecordDraftRequest(BaseModel):
    text: str


class RecordDraftResponse(BaseModel):
    version_id: UUID
    byte_count: int
    violations: list[dict]
    llm_feedback_status: str


class DecideRequest(BaseModel):
    decision: str  # 'approved' | 'rejected'
    comment: str | None = None
