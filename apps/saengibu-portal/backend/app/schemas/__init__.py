from app.schemas.auth import GoogleLoginRequest, MeResponse, UserApprovalDecision
from app.schemas.record import (
    ApprovalItem,
    RecordDraftRequest,
    RecordDraftResponse,
    SectionInfo,
)
from app.schemas.guideline import GuidelineOut, SchoolDecisionOut
from app.schemas.dashboard import DashboardStats

__all__ = [
    "GoogleLoginRequest",
    "MeResponse",
    "UserApprovalDecision",
    "RecordDraftRequest",
    "RecordDraftResponse",
    "ApprovalItem",
    "SectionInfo",
    "GuidelineOut",
    "SchoolDecisionOut",
    "DashboardStats",
]
