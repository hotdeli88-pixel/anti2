"""Baseline schema.

Revision ID: 0001
Revises:
Create Date: 2026-04-14
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("neis_code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default="middle"),
        sa.Column("principal_name", sa.String(50)),
        sa.Column("address", sa.String(300)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "academic_years",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("school_id", "year"),
    )

    op.create_table(
        "grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_years.id"), nullable=False),
        sa.Column("grade_num", sa.SmallInteger, nullable=False),
        sa.UniqueConstraint("year_id", "grade_num"),
    )

    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("class_num", sa.SmallInteger, nullable=False),
        sa.UniqueConstraint("grade_id", "class_num"),
    )

    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("school_id", "code"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("employee_no", sa.String(20)),
        sa.Column("phone", sa.String(20)),
        sa.Column("google_sub", sa.String(128), unique=True, index=True),
        sa.Column("picture_url", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("school_id", "email"),
    )

    op.create_table(
        "user_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "role_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("scope_type", sa.String(20)),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True)),
        sa.Column("year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_years.id")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_role_active", "role_assignments", ["user_id"], postgresql_where=sa.text("ended_at IS NULL"))

    op.create_table(
        "teacher_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_years.id"), nullable=False),
        sa.UniqueConstraint("user_id", "class_id", "subject_id", "year_id"),
    )

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("student_no", sa.String(20), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("gender", sa.String(10)),
        sa.Column("birth_date", sa.Date),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("school_id", "student_no"),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_years.id"), nullable=False),
        sa.Column("started_at", sa.Date, nullable=False),
        sa.Column("ended_at", sa.Date),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.UniqueConstraint("student_id", "year_id"),
    )

    op.create_table(
        "homeroom_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_years.id"), nullable=False),
        sa.Column("started_at", sa.Date, nullable=False),
        sa.Column("ended_at", sa.Date),
    )

    op.create_table(
        "section_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(30), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("neis_area", sa.String(30), nullable=False),
        sa.Column("byte_limit", sa.Integer, nullable=False),
        sa.Column("byte_limit_basis", sa.String(20), nullable=False),
        sa.Column("input_role", sa.String(30), nullable=False),
        sa.Column("style_rule_set", sa.String(30), nullable=False, server_default="nouning_end"),
        sa.Column("neis_prefix_rule", postgresql.JSONB),
        sa.Column("retention_policy", sa.String(30), nullable=False, server_default="permanent"),
        sa.Column("updated_in_2026", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_years.id"), nullable=False),
        sa.Column("section_type_id", sa.Integer, sa.ForeignKey("section_types.id"), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id")),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("retention_until", sa.Date),
        sa.Column("retention_reason", sa.String(50)),
        sa.Column("neis_prefix", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "year_id", "section_type_id", "subject_id"),
    )
    op.create_index("idx_records_status", "records", ["status"])
    op.create_index("idx_records_author_status", "records", ["author_id", "status"])

    op.create_table(
        "record_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("byte_count", sa.Integer, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("record_id", "version_no"),
    )
    op.create_index("idx_versions_record", "record_versions", ["record_id", sa.text("version_no DESC")])

    # 순환 FK: records.current_version_id → record_versions.id (deferrable)
    op.execute(
        "ALTER TABLE records "
        "ADD CONSTRAINT fk_records_current_version "
        "FOREIGN KEY (current_version_id) REFERENCES record_versions(id) "
        "DEFERRABLE INITIALLY DEFERRED"
    )

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records.id"), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_versions.id"), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_reviews_in_progress", "reviews", ["status"], postgresql_where=sa.text("status = 'in_progress'"))

    op.create_table(
        "review_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_no", sa.SmallInteger, nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("expected_role", sa.String(30), nullable=False),
        sa.Column("decision", sa.String(20)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("review_id", "step_no"),
    )

    op.create_table(
        "review_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_steps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("span_start", sa.Integer),
        sa.Column("span_end", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "feedback_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_versions.id"), nullable=False, unique=True),
        sa.Column("stage_byte", postgresql.JSONB),
        sa.Column("stage_banned", postgresql.JSONB),
        sa.Column("stage_style", postgresql.JSONB),
        sa.Column("stage_repeat", postgresql.JSONB),
        sa.Column("stage_llm", postgresql.JSONB),
        sa.Column("stage_llm_status", sa.String(20), nullable=False, server_default="skipped"),
        sa.Column("stage_checklist", postgresql.JSONB),
        sa.Column("total_violations", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_warnings", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feedback_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("rule_code", sa.String(80), nullable=False),
        sa.Column("span_start", sa.Integer),
        sa.Column("span_end", sa.Integer),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("suggestion", sa.Text),
        sa.Column("reference", sa.String(200)),
    )

    op.create_table(
        "guidelines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("icon", sa.String(20), nullable=False, server_default="pen"),
        sa.Column("body_markdown", sa.Text, nullable=False),
        sa.Column("reference", sa.String(200), nullable=False, server_default=""),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("rules_version", sa.String(20), nullable=False, server_default="2026-03"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "school_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False, server_default="info"),
        sa.Column("body_markdown", sa.Text, nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("posted_by", sa.String(100), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(30), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("ip", postgresql.INET),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("content_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("prev_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_actor", "audit_logs", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_audit_chain", "audit_logs", ["school_id", sa.text("created_at DESC")])


def downgrade() -> None:
    for t in [
        "audit_logs",
        "school_decisions",
        "guidelines",
        "violations",
        "feedback_reports",
        "review_comments",
        "review_steps",
        "reviews",
        "record_versions",
        "records",
        "section_types",
        "homeroom_assignments",
        "enrollments",
        "students",
        "teacher_assignments",
        "role_assignments",
        "user_approvals",
        "users",
        "subjects",
        "classes",
        "grades",
        "academic_years",
        "schools",
    ]:
        op.drop_table(t)
