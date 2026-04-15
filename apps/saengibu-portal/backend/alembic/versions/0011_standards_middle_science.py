"""Seed 중학교 과학 성취기준·성취수준 (2022 개정 임시 시드).

Revision ID: 0011
Revises: 0010
Create Date: 2026-04-15
"""
from __future__ import annotations

from alembic._seed_loader import load_subject, unload_subject

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

SOURCE_DOC = "교육부고시 2022-33 별책9 중학교 과학 (임시 시드, 정본 검증 필요)"


def upgrade() -> None:
    load_subject(
        subject_code="과학",
        jsonl_filename="middle_science.jsonl",
        source_doc_label=SOURCE_DOC,
    )


def downgrade() -> None:
    unload_subject(subject_code="과학", school_level="middle")
