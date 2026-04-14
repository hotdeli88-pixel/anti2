"""Seed section_types (13개 영역 + NEIS 접두사 규칙).

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-14
"""
from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


SECTION_TYPES = [
    # code,              name,                          area,       byte_limit, basis,     input_role,        style, prefix_rule, retention, updated
    ("injeok_teuggi",    "인적·학적 특기사항",            "인적학적",   1500, "year",    "homeroom",        "nouning_end", None, "permanent", False),
    ("chulgyeol_teuggi", "출결 특기사항",                "출결",       1500, "year",    "homeroom",        "nouning_end", None, "permanent", True),
    ("susang",           "수상경력",                     "수상",       300,  "record",  "homeroom",        "raw",         None, "permanent", False),
    ("hakpok_jochi",     "학교폭력 조치상황",             "학교폭력",   500,  "record",  "homeroom",        "raw",         None, "hakpok_variable", False),
    ("chang_jayul",      "자율·자치활동",                "창의적체험", 1500, "year",    "homeroom",        "nouning_end", None, "permanent", True),
    ("chang_dongari",    "동아리활동",                   "창의적체험", 1500, "year",    "club_advisor",    "nouning_end",
     {"type": "choice", "options": ["(자율동아리)", "(청소년단체)", "(학교스포츠클럽)"]}, "permanent", True),
    ("chang_jinro",      "진로활동",                     "창의적체험", 1500, "year",    "homeroom",        "nouning_end", None, "permanent", True),
    ("chang_bongsa",     "봉사활동실적 활동내용",         "창의적체험", 150,  "record",  "homeroom",        "raw",
     {"type": "choice", "options": ["(학교)", "(개인)"]}, "permanent", True),
    ("ilsangsaenghwal",  "일상생활 활동상황",            "일상생활",   3000, "year",    "subject_teacher", "nouning_end", None, "permanent", False),
    ("jayuhakgi",        "자유학기활동",                 "자유학기",   3000, "year",    "subject_teacher", "nouning_end", None, "permanent", False),
    ("setuk_subject",    "과목별 세부능력 및 특기사항",   "교과학습",   1500, "subject", "subject_teacher", "nouning_end", None, "permanent", False),
    ("setuk_individual", "개인별 세부능력 및 특기사항",   "교과학습",   1500, "year",    "homeroom",        "nouning_end", None, "permanent", False),
    ("dokseo_common",    "독서활동 공통",                "독서",       1500, "year",    "homeroom",        "raw",         None, "permanent", True),
    ("dokseo_subject",   "독서활동 과목별",              "독서",       750,  "subject", "subject_teacher", "raw",         None, "permanent", True),
    ("haengjongjeui",    "행동특성 및 종합의견",          "행종의",     900,  "year",    "homeroom",        "nouning_end", None, "permanent", True),
]


def upgrade() -> None:
    section_types = sa.table(
        "section_types",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("neis_area", sa.String),
        sa.column("byte_limit", sa.Integer),
        sa.column("byte_limit_basis", sa.String),
        sa.column("input_role", sa.String),
        sa.column("style_rule_set", sa.String),
        sa.column("neis_prefix_rule", sa.JSON),
        sa.column("retention_policy", sa.String),
        sa.column("updated_in_2026", sa.Boolean),
    )
    op.bulk_insert(
        section_types,
        [
            dict(
                code=c,
                name=n,
                neis_area=a,
                byte_limit=bl,
                byte_limit_basis=bb,
                input_role=ir,
                style_rule_set=ss,
                neis_prefix_rule=json.dumps(pr) if pr else None,
                retention_policy=rp,
                updated_in_2026=u,
            )
            for (c, n, a, bl, bb, ir, ss, pr, rp, u) in SECTION_TYPES
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM section_types")
