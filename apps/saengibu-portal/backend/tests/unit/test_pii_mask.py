"""PII 마스킹 회귀 테스트 (C-5).

이름 토큰이 RRN/PHONE 정규식과 충돌하지 않도록 RRN/PHONE 우선 적용.
"""
from __future__ import annotations

import pytest

from app.services.mask.pii import mask_text, unmask_text


@pytest.mark.bug_audit
class TestPiiMaskOrder:
    def test_phone_masked_before_name(self) -> None:
        text = "010-1234-5678 홍길동 학생"
        mapping = {"홍길동": "<S_1030101>"}
        result = mask_text(text, mapping)
        assert "<PHONE>" in result
        assert "<S_1030101>" in result
        assert "010-1234-5678" not in result
        assert "홍길동" not in result

    def test_rrn_masked(self) -> None:
        text = "주민번호 991231-1234567 입니다."
        result = mask_text(text, {})
        assert "<RRN>" in result
        assert "991231-1234567" not in result

    def test_name_with_no_rrn_overlap(self) -> None:
        text = "홍길동의 작품"
        mapping = {"홍길동": "<S_1030101>"}
        result = mask_text(text, mapping)
        assert result == "<S_1030101>의 작품"

    def test_longer_name_replaced_first(self) -> None:
        """부분 매칭 방지: 긴 이름이 먼저 치환되어야 한다."""
        text = "홍길동수와 홍길동의 점수"
        mapping = {
            "홍길동수": "<S_LONG>",
            "홍길동": "<S_SHORT>",
        }
        result = mask_text(text, mapping)
        assert "<S_LONG>와" in result
        assert "<S_SHORT>의" in result

    def test_round_trip(self) -> None:
        text = "홍길동과 김철수가 발표했다."
        mapping = {"홍길동": "<S_1030101>", "김철수": "<S_1030102>"}
        masked = mask_text(text, mapping)
        restored = unmask_text(masked, mapping)
        assert restored == text


@pytest.mark.bug_audit
def test_phone_pattern_no_match_normal_numbers() -> None:
    """일반 숫자(예: 학번 10301)는 PHONE으로 매칭되지 않아야 한다."""
    text = "학번 1030101 홍길동"
    mapping = {"홍길동": "<S_1030101>"}
    result = mask_text(text, mapping)
    assert "1030101" in result  # 학번은 그대로
    assert "<PHONE>" not in result
