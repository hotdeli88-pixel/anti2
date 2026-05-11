"""Seed achievement standards (중학교 수학 2022 개정) + activity tags (과목별 8+) + student traits.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-14
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


# ============ 성취기준 (최소 시드, 배포 시 전체 확장 필요) ============

STANDARDS_MIDDLE_MATH = [
    # (grade, domain, code, statement)
    (1, "수와 연산", "[9수01-01]", "소인수분해의 뜻을 알고, 자연수를 소인수분해 할 수 있다."),
    (1, "수와 연산", "[9수01-02]", "최대공약수와 최소공배수의 성질을 이해하고, 이를 구할 수 있다."),
    (1, "수와 연산", "[9수01-03]", "양수와 음수, 정수와 유리수의 개념을 이해한다."),
    (1, "문자와 식", "[9수02-01]", "다양한 상황을 문자를 사용한 식으로 나타낼 수 있다."),
    (1, "문자와 식", "[9수02-02]", "식의 값을 구할 수 있다."),
    (1, "함수", "[9수03-01]", "좌표평면을 이해하고, 순서쌍과 좌표를 표현할 수 있다."),
    (2, "수와 연산", "[9수01-04]", "유리수와 순환소수의 관계를 이해한다."),
    (2, "문자와 식", "[9수02-03]", "일차식의 덧셈과 뺄셈의 원리를 이해하고, 그 계산을 할 수 있다."),
    (2, "기하", "[9수04-01]", "점, 선, 면, 각을 이해하고, 관계를 설명할 수 있다."),
    (3, "함수", "[9수03-02]", "함수의 개념을 이해하고, 함숫값을 구할 수 있다."),
    (3, "확률과 통계", "[9수05-01]", "자료를 정리하고 적절한 방법으로 나타낼 수 있다."),
]

STANDARDS_MIDDLE_KOREAN = [
    (1, "듣기·말하기", "[9국01-01]", "듣기·말하기가 의미 공유의 과정임을 이해하고 듣기·말하기 활동을 한다."),
    (1, "읽기", "[9국02-01]", "읽기는 글에 나타난 정보와 독자의 배경지식을 활용하여 문제를 해결하는 과정임을 이해한다."),
    (1, "쓰기", "[9국03-01]", "쓰기는 주제, 목적, 독자, 매체 등을 고려한 문제 해결 과정임을 이해한다."),
    (1, "문법", "[9국04-01]", "음운의 체계를 알고 그 특성을 이해한다."),
    (1, "문학", "[9국05-01]", "문학은 심미적 체험을 바탕으로 하는 다양한 소통 활동임을 이해한다."),
    (2, "읽기", "[9국02-02]", "독자의 배경지식, 읽기 맥락 등을 활용하여 글의 내용을 예측한다."),
    (2, "쓰기", "[9국03-02]", "대상의 특성에 맞는 설명 방법을 사용하여 글을 쓴다."),
    (3, "문학", "[9국05-02]", "비유와 상징의 표현 효과를 바탕으로 작품을 수용하고 생산한다."),
]

STANDARDS_MIDDLE_ENGLISH = [
    (1, "듣기", "[9영01-01]", "어구나 문장을 듣고 연음, 축약된 소리를 식별할 수 있다."),
    (1, "말하기", "[9영02-01]", "주변의 사람, 사물, 또는 위치를 묘사할 수 있다."),
    (1, "읽기", "[9영03-01]", "문장을 의미 단위로 끊어 읽으면서 의미를 파악할 수 있다."),
    (1, "쓰기", "[9영04-01]", "일상생활에 관한 자신의 의견이나 감정을 표현하는 문장을 쓸 수 있다."),
    (2, "말하기", "[9영02-02]", "자신이나 주변 사람 및 일상생활에 관해 묻거나 답할 수 있다."),
    (3, "읽기", "[9영03-02]", "일상생활이나 친숙한 일반적 주제의 글을 읽고 줄거리를 파악할 수 있다."),
]


def _standards_rows() -> list[dict]:
    rows = []
    for grade, domain, code, stmt in STANDARDS_MIDDLE_MATH:
        rows.append(dict(curriculum="2022_revised", school_level="middle",
                         grade=grade, subject_code="수학",
                         domain=domain, code=code, statement=stmt, active=True))
    for grade, domain, code, stmt in STANDARDS_MIDDLE_KOREAN:
        rows.append(dict(curriculum="2022_revised", school_level="middle",
                         grade=grade, subject_code="국어",
                         domain=domain, code=code, statement=stmt, active=True))
    for grade, domain, code, stmt in STANDARDS_MIDDLE_ENGLISH:
        rows.append(dict(curriculum="2022_revised", school_level="middle",
                         grade=grade, subject_code="영어",
                         domain=domain, code=code, statement=stmt, active=True))
    return rows


# ============ 활동 태그 (과목·카테고리별, 하마룸 분석 반영) ============

TAGS = [
    # 수학 수업활동
    ("수학", "setuk_subject", "수업활동", "문제풀이 활동"),
    ("수학", "setuk_subject", "수업활동", "창의적 사고 활동"),
    ("수학", "setuk_subject", "수업활동", "교구 활용 활동"),
    ("수학", "setuk_subject", "수업활동", "개별 학습 활동"),
    ("수학", "setuk_subject", "수업활동", "탐구 보고서 작성 활동"),
    ("수학", "setuk_subject", "수업활동", "자료 해석 활동"),
    ("수학", "setuk_subject", "수업활동", "그래프 그리기 활동"),
    ("수학", "setuk_subject", "수업활동", "실생활 연계 활동"),
    # 수학 학생특성
    ("수학", "setuk_subject", "학생특성", "개념에 대한 이해가 빠름"),
    ("수학", "setuk_subject", "학생특성", "원리나 개념의 융합 능력이 좋음"),
    ("수학", "setuk_subject", "학생특성", "논리적 사고력이 우수함"),
    ("수학", "setuk_subject", "학생특성", "난이도 높은 개념을 쉽게 이해함"),
    ("수학", "setuk_subject", "학생특성", "도형 및 공간 감각이 뛰어남"),
    ("수학", "setuk_subject", "학생특성", "수리적 표현이 명료함"),
    # 국어 수업활동
    ("국어", "setuk_subject", "수업활동", "토론"),
    ("국어", "setuk_subject", "수업활동", "발표"),
    ("국어", "setuk_subject", "수업활동", "독서"),
    ("국어", "setuk_subject", "수업활동", "글쓰기"),
    ("국어", "setuk_subject", "수업활동", "문학 감상"),
    ("국어", "setuk_subject", "수업활동", "자료 조사 및 연구"),
    ("국어", "setuk_subject", "수업활동", "역할극"),
    ("국어", "setuk_subject", "수업활동", "창작"),
    ("국어", "setuk_subject", "수업활동", "비판적 사고"),
    ("국어", "setuk_subject", "수업활동", "모둠 활동"),
    # 국어 학생특성
    ("국어", "setuk_subject", "학생특성", "독해력이 우수함"),
    ("국어", "setuk_subject", "학생특성", "표현력이 풍부함"),
    ("국어", "setuk_subject", "학생특성", "어휘력이 탄탄함"),
    ("국어", "setuk_subject", "학생특성", "창의성이 돋보임"),
    ("국어", "setuk_subject", "학생특성", "필자 의도 파악이 정확함"),
    ("국어", "setuk_subject", "학생특성", "비판적 사고력이 우수함"),
    # 영어 수업활동
    ("영어", "setuk_subject", "수업활동", "듣기 활동"),
    ("영어", "setuk_subject", "수업활동", "말하기 발표"),
    ("영어", "setuk_subject", "수업활동", "원서 읽기"),
    ("영어", "setuk_subject", "수업활동", "글쓰기 과제"),
    ("영어", "setuk_subject", "수업활동", "모둠 프로젝트"),
    ("영어", "setuk_subject", "수업활동", "어휘 학습"),
    # 공통: 역할수행 (전 과목·영역)
    (None, None, "역할수행", "과목 부장을 맡음"),
    (None, None, "역할수행", "모둠장을 맡음"),
    (None, None, "역할수행", "모둠원으로 활동함"),
    (None, None, "역할수행", "봉사정신이 투철함"),
    (None, None, "역할수행", "교사 지원 역할을 함"),
    # 공통: 성장정도
    (None, None, "성장정도", "역량이 향상됨"),
    (None, None, "성장정도", "사고력이 발달함"),
    (None, None, "성장정도", "수준이 향상됨"),
    (None, None, "성장정도", "협력 능력이 성장함"),
    (None, None, "성장정도", "자기주도성이 높아짐"),
    # 창체 자율활동
    (None, "chang_jayul", "수업활동", "학급 자치 회의 주도"),
    (None, "chang_jayul", "수업활동", "학교 행사 기획·진행"),
    (None, "chang_jayul", "수업활동", "캠페인 참여"),
    (None, "chang_jayul", "수업활동", "공동체 의사결정"),
    # 창체 진로활동
    (None, "chang_jinro", "수업활동", "진로 탐색 보고서"),
    (None, "chang_jinro", "수업활동", "직업 체험"),
    (None, "chang_jinro", "수업활동", "진로 상담 참여"),
    (None, "chang_jinro", "수업활동", "커리어넷 검사 분석"),
]


# ============ 공지 (샘플) ============

NOTICES = [
    ("announcement", "2026학년도 1학기 생기부 마감 일정 안내",
     "- **1차 작성 마감**: 7월 10일 (금)\n- **1검 제출**: 7월 12일 (일)\n- **2검 제출**: 7월 14일 (화)\n- **최종 3검**: 7월 15일 (수)\n\n기한 준수를 부탁드립니다.", True),
    ("training", "훈령 제555호 2026 AI 활용 유의사항 연수 안내",
     "교육부 훈령 2026 신설 'AI 활용 유의사항' 해설 연수를 다음과 같이 진행합니다.\n\n- 일시: 2026-04-20 (월) 오후 3시\n- 장소: 시청각실\n- 자료: 교무부 공유폴더", False),
    ("library", "학교 자체 허용 도서 리스트 등록 안내",
     "올해 독서활동에 인정되는 도서 목록을 라이브러리에 등록했습니다.\n라이브러리 > 도서 섹션에서 확인 가능합니다.", False),
    ("faq", "자주 묻는 질문: Byte 수 계산 방식",
     "본 시스템은 NEIS와 동일하게 **CP949 기준**으로 Byte를 계산합니다.\n- 한글 1자 = 2 Byte\n- 영문/숫자 1자 = 1 Byte\n- 엔터(개행) = 2 Byte (CRLF)\n\n이모지·확장 한자는 NEIS가 거부하므로 입력 시 사전 경고됩니다.", False),
]


def upgrade() -> None:
    standards = sa.table(
        "achievement_standards",
        sa.column("curriculum", sa.String), sa.column("school_level", sa.String),
        sa.column("grade", sa.SmallInteger), sa.column("subject_code", sa.String),
        sa.column("domain", sa.String), sa.column("code", sa.String),
        sa.column("statement", sa.Text), sa.column("active", sa.Boolean),
    )
    op.bulk_insert(standards, _standards_rows())

    tags = sa.table(
        "activity_tags",
        sa.column("subject_code", sa.String),
        sa.column("section_type_id", sa.Integer),
        sa.column("category", sa.String),
        sa.column("label", sa.String),
        sa.column("active", sa.Boolean),
    )
    # section code → section_type_id 매핑을 실행시 쿼리
    conn = op.get_bind()
    section_map = {
        row[0]: row[1]
        for row in conn.execute(sa.text("SELECT code, id FROM section_types"))
    }

    tag_rows = []
    for subject, section_code, category, label in TAGS:
        tag_rows.append(dict(
            subject_code=subject,
            section_type_id=section_map.get(section_code) if section_code else None,
            category=category,
            label=label,
            active=True,
        ))
    op.bulk_insert(tags, tag_rows)

    # 공지: 학교·작성자는 실행 시점에 임의의 첫 학교/관리자 사용 (없으면 skip)
    result = conn.execute(sa.text(
        "SELECT s.id as school_id, u.id as author_id FROM schools s "
        "JOIN users u ON u.school_id = s.id "
        "JOIN role_assignments r ON r.user_id = u.id AND r.role IN ('admin','principal') "
        "LIMIT 1"
    )).first()
    if result:
        notices = sa.table(
            "notice_posts",
            sa.column("school_id", sa.String), sa.column("author_id", sa.String),
            sa.column("category", sa.String), sa.column("title", sa.String),
            sa.column("body_markdown", sa.Text), sa.column("pinned", sa.Boolean),
        )
        op.bulk_insert(notices, [
            dict(school_id=result.school_id, author_id=result.author_id,
                 category=cat, title=title, body_markdown=body, pinned=pinned)
            for cat, title, body, pinned in NOTICES
        ])


def downgrade() -> None:
    op.execute("DELETE FROM notice_posts")
    op.execute("DELETE FROM activity_tags")
    op.execute("DELETE FROM achievement_standards")
