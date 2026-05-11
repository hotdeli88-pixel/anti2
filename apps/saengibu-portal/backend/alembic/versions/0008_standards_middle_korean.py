"""Seed 중학교 국어 성취기준·성취수준 (2022 개정 임시 시드).

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-15
"""
from __future__ import annotations

from alembic._seed_loader import load_subject, unload_subject

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

SOURCE_DOC = "교육부고시 2022-33 별책5 중학교 국어 (임시 시드, 정본 검증 필요)"


def upgrade() -> None:
    load_subject(
        subject_code="국어",
        jsonl_filename="middle_korean.jsonl",
        source_doc_label=SOURCE_DOC,
    )


def downgrade() -> None:
    unload_subject(subject_code="국어", school_level="middle")
