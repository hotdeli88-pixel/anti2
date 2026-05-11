"""성취기준 코드·문장 정규화 헬퍼."""
from __future__ import annotations

import re
import unicodedata

CODE_RE = re.compile(r"^\[\s*([0-9]+)\s*([가-힣]+)\s*([0-9]{2})\s*-\s*([0-9]{2})\s*\]$")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_code(code: str) -> str:
    """공백·전각 정리해 `[9수01-01]` 형식으로 통일."""
    if not code:
        return code
    cleaned = unicodedata.normalize("NFC", code).strip()
    m = CODE_RE.match(cleaned)
    if not m:
        return cleaned  # 호출자에서 validate.py로 검증
    grade_prefix, subject, area, item = m.groups()
    return f"[{grade_prefix}{subject}{area}-{item}]"


def normalize_statement(text: str) -> str:
    """전후 공백 제거 + 전각공백/non-breaking space 일반화 + 다중 공백 단일화."""
    if text is None:
        return text
    cleaned = unicodedata.normalize("NFC", text)
    cleaned = cleaned.replace("\u3000", " ").replace("\xa0", " ")
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def normalize_descriptor(text: str) -> str:
    """성취수준 descriptor 정규화 (긴 텍스트, 줄바꿈 보존)."""
    if text is None:
        return text
    cleaned = unicodedata.normalize("NFC", text)
    # 줄바꿈은 보존, 줄 안의 다중 공백만 정리
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in cleaned.splitlines()]
    return "\n".join(filter(None, lines))
