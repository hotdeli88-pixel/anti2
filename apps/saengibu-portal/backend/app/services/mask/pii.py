"""학생/교직원 PII 마스킹 — 외부 LLM 호출 전 필수."""
from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.user import User

# 주민등록번호·전화번호 정규식
RRN = re.compile(r"\d{6}[-\s]?\d{7}")
PHONE = re.compile(r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}")


def mask_name_display(full_name: str) -> str:
    """UI용 가벼운 마스킹: 홍길동 → 홍**."""
    if len(full_name) <= 1:
        return full_name
    return full_name[0] + "*" * (len(full_name) - 1)


async def build_mask_dict(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    target_student_id: uuid.UUID | None = None,
) -> dict[str, str]:
    """학교·학년도 전체 학생·교직원 실명 → 토큰."""
    students = await db.scalars(select(Student).where(Student.school_id == school_id))
    users = await db.scalars(select(User).where(User.school_id == school_id))

    mapping: dict[str, str] = {}
    for s in students:
        tag = "<S_TARGET>" if s.id == target_student_id else f"<S_{s.student_no}>"
        mapping[s.name] = tag
    for u in users:
        mapping[u.name] = f"<T_{u.id.hex[:8]}>"
    return mapping


def mask_text(text: str, mapping: dict[str, str]) -> str:
    """순서: RRN → PHONE → 이름.

    이름 치환 토큰(`<S_…>`, `<T_…>`)이 숫자를 포함할 가능성을 차단하기 위해
    숫자 정규식 마스킹을 먼저 적용한다. 이름은 길이 내림차순으로 치환해 부분 매칭 방지.
    """
    masked = RRN.sub("<RRN>", text)
    masked = PHONE.sub("<PHONE>", masked)
    for name in sorted(mapping, key=len, reverse=True):
        masked = masked.replace(name, mapping[name])
    return masked


def unmask_text(masked_response: str, mapping: dict[str, str]) -> str:
    out = masked_response
    for name, tag in mapping.items():
        out = out.replace(tag, name)
    return out
