"""Achievement levels: achievement_standards 컬럼 확장 + achievement_levels + domain_levels.

Sprint 1 / Plan: tender-questing-sloth
- achievement_standards에 9개 컬럼 추가 + 기존 25건 백필
- achievement_levels (성취기준별 성취수준) 신설
- domain_levels (영역별 성취수준) 신설

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) achievement_standards 컬럼 확장
    op.add_column(
        "achievement_standards",
        sa.Column("eval_scale", sa.String(10), nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("min_achievement", sa.String(1), nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("domain_code", sa.String(20), nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("unit_title", sa.String(120), nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("area_category", sa.String(20), nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("source_doc", sa.String(200), nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("source_page", sa.SmallInteger, nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("source_json", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "achievement_standards",
        sa.Column("rules_version", sa.String(20), nullable=True, server_default="2022-33"),
    )

    # 백필: 기존 25건 모두 임시 시드 표시
    op.execute(
        """
        UPDATE achievement_standards
           SET eval_scale = COALESCE(eval_scale, '5grade'),
               min_achievement = COALESCE(min_achievement, 'E'),
               source_doc = COALESCE(source_doc, '임시 시드 (0005)'),
               rules_version = COALESCE(rules_version, '2022-33')
         WHERE TRUE
        """
    )

    # eval_scale은 NOT NULL 승격
    op.alter_column(
        "achievement_standards",
        "eval_scale",
        existing_type=sa.String(10),
        nullable=False,
        server_default="5grade",
    )
    op.alter_column(
        "achievement_standards",
        "rules_version",
        existing_type=sa.String(20),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_standards_eval_scale",
        "achievement_standards",
        "eval_scale IN ('5grade','3grade','P/F')",
    )

    # 2) achievement_levels 신설 (성취기준별 성취수준)
    op.create_table(
        "achievement_levels",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "standard_id",
            sa.Integer,
            sa.ForeignKey("achievement_standards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.String(1), nullable=False),
        sa.Column("scale", sa.String(10), nullable=False),
        sa.Column("descriptor", sa.Text, nullable=False),
        sa.Column("order_index", sa.SmallInteger, nullable=False),
        sa.Column("cutline_hint", sa.String(80), nullable=True),
        sa.Column("source_doc", sa.String(200), nullable=True),
        sa.Column("source_page", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("standard_id", "level", name="uq_levels_standard_level"),
        sa.CheckConstraint("scale IN ('5grade','3grade','P/F')", name="ck_levels_scale"),
        sa.CheckConstraint(
            "level IN ('A','B','C','D','E','P','F')", name="ck_levels_level_value"
        ),
    )
    op.create_index(
        "idx_levels_standard_order",
        "achievement_levels",
        ["standard_id", sa.text("order_index DESC")],
    )

    # 3) domain_levels 신설 (영역별 성취수준)
    op.create_table(
        "domain_levels",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("curriculum", sa.String(30), nullable=False, server_default="2022_revised"),
        sa.Column("school_level", sa.String(10), nullable=False),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("subject_code", sa.String(20), nullable=False),
        sa.Column("domain", sa.String(80), nullable=False),
        sa.Column("level", sa.String(1), nullable=False),
        sa.Column("descriptor", sa.Text, nullable=False),
        sa.Column("source_doc", sa.String(200), nullable=True),
        sa.Column("source_page", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "curriculum",
            "school_level",
            "grade",
            "subject_code",
            "domain",
            "level",
            name="uq_domain_levels_lookup",
        ),
        sa.CheckConstraint(
            "level IN ('A','B','C','D','E','P','F')", name="ck_domain_levels_level"
        ),
    )
    op.create_index(
        "idx_domain_levels_lookup",
        "domain_levels",
        ["subject_code", "grade", "domain"],
    )


def downgrade() -> None:
    op.drop_index("idx_domain_levels_lookup", table_name="domain_levels")
    op.drop_table("domain_levels")

    op.drop_index("idx_levels_standard_order", table_name="achievement_levels")
    op.drop_table("achievement_levels")

    op.drop_constraint("ck_standards_eval_scale", "achievement_standards", type_="check")
    for col in (
        "rules_version",
        "source_json",
        "source_page",
        "source_doc",
        "area_category",
        "unit_title",
        "domain_code",
        "min_achievement",
        "eval_scale",
    ):
        op.drop_column("achievement_standards", col)
