"""Fix critical bugs: FK ondelete, default 통일, CHECK 제약.

Sprint 0 / Plan: tender-questing-sloth
- C-3: records.current_version_id ON DELETE SET NULL (DEFERRABLE 유지)
- C-6: role_assignments.started_at server_default 이미 있음 → 모델 측 default 통일은 코드에서 처리
- M-1: feedback_reports.created_at server_default=now() 추가
- M-9: academic_years CHECK (end_date > start_date)

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # C-3: 순환 FK ondelete SET NULL 재정의
    op.execute("ALTER TABLE records DROP CONSTRAINT IF EXISTS fk_records_current_version")
    op.execute(
        "ALTER TABLE records "
        "ADD CONSTRAINT fk_records_current_version "
        "FOREIGN KEY (current_version_id) REFERENCES record_versions(id) "
        "ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED"
    )

    # M-1: feedback_reports.created_at server_default 보강
    op.alter_column(
        "feedback_reports",
        "created_at",
        server_default=sa.func.now(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    # M-9: academic_years 기간 정합성 CHECK
    op.create_check_constraint(
        "ck_academic_years_dates",
        "academic_years",
        "end_date > start_date",
    )


def downgrade() -> None:
    op.drop_constraint("ck_academic_years_dates", "academic_years", type_="check")

    op.alter_column(
        "feedback_reports",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    op.execute("ALTER TABLE records DROP CONSTRAINT IF EXISTS fk_records_current_version")
    op.execute(
        "ALTER TABLE records "
        "ADD CONSTRAINT fk_records_current_version "
        "FOREIGN KEY (current_version_id) REFERENCES record_versions(id) "
        "DEFERRABLE INITIALLY DEFERRED"
    )
