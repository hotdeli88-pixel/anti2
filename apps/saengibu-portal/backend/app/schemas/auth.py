from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token (JWT)")


class HomeroomOf(BaseModel):
    class_id: UUID
    label: str


class TeachesOf(BaseModel):
    class_id: UUID
    subject_id: UUID
    label: str


class SchoolRef(BaseModel):
    id: UUID
    name: str


class MeResponse(BaseModel):
    id: UUID
    email: str
    name: str
    status: Literal["pending", "active", "suspended"]
    roles: list[str]
    school: SchoolRef
    homeroom_of: list[HomeroomOf] = []
    teaches: list[TeachesOf] = []


class UserApprovalDecision(BaseModel):
    """M-8: pattern → Literal로 OpenAPI enum 자동 생성."""

    decision: Literal["approved", "rejected"]
    role: str | None = None
    reason: str | None = None
