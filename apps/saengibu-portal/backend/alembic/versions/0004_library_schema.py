"""Library schema: achievement_standards, activity_tags, favorite_templates, uploaded_files, ai_suggestions, notice_posts.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-14
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "achievement_standards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("curriculum", sa.String(30), nullable=False, server_default="2022_revised"),
        sa.Column("school_level", sa.String(10), nullable=False),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("subject_code", sa.String(20), nullable=False),
        sa.Column("domain", sa.String(80)),
        sa.Column("unit_code", sa.String(30)),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("curriculum", "code"),
    )
    op.create_index("idx_standards_subject_grade", "achievement_standards", ["subject_code", "grade"])

    op.create_table(
        "activity_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id")),
        sa.Column("subject_code", sa.String(20)),
        sa.Column("section_type_id", sa.Integer, sa.ForeignKey("section_types.id")),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("synonyms", postgresql.ARRAY(sa.String)),
        sa.Column("description", sa.Text),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("school_id", "category", "label"),
    )
    op.create_index("idx_tags_subject_section", "activity_tags", ["subject_code", "section_type_id", "category"])

    op.create_table(
        "favorite_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("section_type_id", sa.Integer, sa.ForeignKey("section_types.id"), nullable=False),
        sa.Column("subject_code", sa.String(20)),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("tags_json", postgresql.JSONB),
        sa.Column("achievement_standard_ids", postgresql.ARRAY(sa.Integer)),
        sa.Column("pin_order", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_favorites_user", "favorite_templates", ["user_id", "section_type_id", "pin_order"])

    op.create_table(
        "uploaded_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records.id")),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.BigInteger, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("mime_magic_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("av_scan_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("av_scan_at", sa.DateTime(timezone=True)),
        sa.Column("extracted_text", sa.Text),
        sa.Column("extraction_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("school_id", "sha256"),
    )
    op.create_index("idx_uploads_uploader", "uploaded_files", ["school_id", "uploader_id", sa.text("created_at DESC")])
    op.create_index("idx_uploads_av_pending", "uploaded_files", ["av_scan_status"], postgresql_where=sa.text("av_scan_status = 'pending'"))

    op.create_table(
        "ai_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records.id"), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("record_versions.id")),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("input_tags_json", postgresql.JSONB),
        sa.Column("input_files_json", postgresql.JSONB),
        sa.Column("input_standards_json", postgresql.JSONB),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(30)),
        sa.Column("model", sa.String(100)),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column("response_json", postgresql.JSONB),
        sa.Column("tokens_input", sa.Integer),
        sa.Column("tokens_output", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_suggestions_record", "ai_suggestions", ["record_id", sa.text("created_at DESC")])

    op.create_table(
        "notice_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id")),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category", sa.String(30), nullable=False, server_default="announcement"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body_markdown", sa.Text, nullable=False),
        sa.Column("pinned", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_notices_feed", "notice_posts", ["school_id", "category", sa.text("published_at DESC")])


def downgrade() -> None:
    for t in [
        "notice_posts",
        "ai_suggestions",
        "uploaded_files",
        "favorite_templates",
        "activity_tags",
        "achievement_standards",
    ]:
        op.drop_table(t)
