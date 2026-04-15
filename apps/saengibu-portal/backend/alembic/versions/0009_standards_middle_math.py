"""Seed 중학교 수학 성취기준·성취수준 (0005 11건 정본 덮어쓰기).

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-15
"""
from __future__ import annotations

from alembic._seed_loader import load_subject, unload_subject

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

SOURCE_DOC = "교육부고시 2022-33 별책8 중학교 수학 (임시 시드, 정본 검증 필요)"


def upgrade() -> None:
    # 0005에서 11건 하드코딩되었던 항목을 ON CONFLICT DO UPDATE로 정본 덮어쓰기 + 성취수준 추가.
    load_subject(
        subject_code="수학",
        jsonl_filename="middle_math.jsonl",
        source_doc_label=SOURCE_DOC,
    )


def downgrade() -> None:
    unload_subject(subject_code="수학", school_level="middle")
