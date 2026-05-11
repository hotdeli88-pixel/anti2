"""Seed guidelines (기재요령 안내) 전 학교 공용.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-14
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


GUIDELINES = [
    (
        "행동특성 및 종합의견 기재 주의사항",
        "pen",
        "1. 학생의 장점과 단점을 객관적으로 기술하되, 단점을 기술할 경우에는 "
        "==변화 가능성과 노력의 과정==을 함께 작성해야 합니다.\n\n"
        "2. 긍정적인 변화를 보여주는 구체적인 일화나 사례를 포함하는 것이 권장됩니다.\n\n"
        "3. 일상적인 학교생활 중 교사가 관찰한 학생의 특성을 반영하여 과장 없이 있는 그대로 기록합니다.\n\n"
        "4. ==2026학년도부터 글자수가 500자→300자로 축소==되었으므로 핵심 내용 중심으로 압축 기재하세요.",
        "훈령 제555호 제16조 · 2026 기재요령 p.24-25",
        10,
    ),
    (
        "창의적 체험활동 특기사항",
        "book",
        "정규 교육과정 내에서 이루어진 활동만 기재 가능하며, 학교 밖에서 이루어진 활동은 "
        "학교장의 승인을 받은 경우에 한해 부분적으로 기재할 수 있습니다. "
        "단순 참여 사실보다는 ==학생 본인의 역할과 활동 내용, 실질적으로 성장한 점==을 위주로 서술하세요.\n\n"
        "**자율동아리**: 동아리명 앞에 `(자율동아리)` 접두어 필수, 학년당 1개만 입력.\n"
        "**봉사활동**: `(학교)` / `(개인)`으로 주체 구분, 실적별 50자 이내.",
        "훈령 제555호 제13조",
        20,
    ),
    (
        "AI 활용 유의사항 (2026 신설)",
        "file",
        "**AI가 생성한 자료를 서술형 항목에 그대로 입력하는 것은 금지**입니다. "
        "윤문·교정 등 보조수단으로만 활용하며, 최종 입력 전 다음을 반드시 확인하세요.\n\n"
        "1. ==학생의 실제 수행과 무관한 허위 또는 과장 기재 여부==\n"
        "2. ==기재요령의 각종 유의사항 준수 여부==\n\n"
        "본 시스템은 교사 초안에 대한 **피드백 전용**이며, 문장을 대신 생성하지 않습니다.",
        "훈령 제555호 2026 신설 · p.24-25",
        30,
    ),
]


def upgrade() -> None:
    guidelines = sa.table(
        "guidelines",
        sa.column("title", sa.String),
        sa.column("icon", sa.String),
        sa.column("body_markdown", sa.Text),
        sa.column("reference", sa.String),
        sa.column("order_index", sa.Integer),
        sa.column("active", sa.Boolean),
        sa.column("rules_version", sa.String),
    )
    op.bulk_insert(
        guidelines,
        [
            dict(
                title=t,
                icon=i,
                body_markdown=b,
                reference=r,
                order_index=o,
                active=True,
                rules_version="2026-03",
            )
            for (t, i, b, r, o) in GUIDELINES
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM guidelines")
