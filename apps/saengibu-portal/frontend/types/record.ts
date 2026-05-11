export interface MeResponse {
  id: string;
  email: string;
  name: string;
  status: "pending" | "active" | "suspended";
  roles: string[];
  school: { id: string; name: string };
  homeroom_of: Array<{ class_id: string; label: string }>;
  teaches: Array<{ class_id: string; subject_id: string; label: string }>;
}

export interface DashboardStats {
  pending_approvals: number;
  approved_this_week: number;
  ai_corrections: number;
}

export interface ApprovalItem {
  review_id: string;
  record_id: string;
  step_no: number;
  student: { id: string; name_masked: string; grade: number; class_no: number };
  section: { code: string; name: string };
  author: { id: string; name: string };
  submitted_at: string;
  status: "pending" | "guide_correction" | "approved" | "rejected";
  ai_warn_count: number;
}

export interface Guideline {
  id: string;
  title: string;
  icon: string;
  body_markdown: string;
  reference: string;
}

export interface SchoolDecision {
  id: string;
  title: string;
  severity: "info" | "warn" | "block";
  body_markdown: string;
  effective_date: string;
  posted_by: string;
}
