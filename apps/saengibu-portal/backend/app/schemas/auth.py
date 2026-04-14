from __future__ import annotations

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
    status: str
    roles: list[str]
    school: SchoolRef
    homeroom_of: list[HomeroomOf] = []
    teaches: list[TeachesOf] = []


class UserApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    role: str | None = None
    reason: str | None = None
