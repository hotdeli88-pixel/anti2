from pydantic import BaseModel


class DashboardStats(BaseModel):
    pending_approvals: int
    approved_this_week: int
    ai_corrections: int
