"""CP949 Byte 카운터 단위 테스트 (Stage 1)."""
from __future__ import annotations

import pytest

from app.services.byte.cp949_counter import (
    byte_count_cp949,
    byte_limit_for,
    normalize_for_neis,
)


@pytest.mark.bug_audit
class TestCp949Counter:
    def test_empty(self) -> None:
        bytes_, incompat = byte_count_cp949("")
        assert bytes_ == 0
        assert incompat == []

    def test_korean_2_bytes(self) -> None:
        # 한글 1자 = 2 byte (CP949)
        bytes_, _ = byte_count_cp949("한")
        assert bytes_ == 2

    def test_ascii_1_byte(self) -> None:
        bytes_, _ = byte_count_cp949("A")
        assert bytes_ == 1

    def test_crlf_counted_as_2(self) -> None:
        # \n → \r\n 으로 정규화 후 2바이트
        bytes_, _ = byte_count_cp949("\n")
        assert bytes_ == 2

    def test_emoji_incompatible(self) -> None:
        bytes_, incompat = byte_count_cp949("좋아요🎉")
        # 이모지는 CP949 미지원
        assert "🎉" in incompat
        assert bytes_ == 6  # 한글 3자 × 2

    def test_byte_limit_lookup(self) -> None:
        assert byte_limit_for("haengjongjeui") == 900
        assert byte_limit_for("setuk_subject") == 1500
        assert byte_limit_for("chang_bongsa") == 150
