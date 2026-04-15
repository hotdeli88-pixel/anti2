"""CSRF 토큰 로테이션 단위 테스트 (C-4)."""
from __future__ import annotations

import time

import pytest

from app.core.security import should_rotate_session


@pytest.mark.bug_audit
class TestShouldRotateSession:
    def _claims(self, *, age_seconds: int, ttl_seconds: int = 24 * 3600) -> dict:
        now = int(time.time())
        return {
            "iat": now - age_seconds,
            "exp": now - age_seconds + ttl_seconds,
        }

    def test_fresh_session_no_rotation(self) -> None:
        # 발급 직후
        claims = self._claims(age_seconds=10)
        assert should_rotate_session(claims) is False

    def test_old_session_triggers_rotation(self) -> None:
        # 24h TTL 중 23h 경과 → 잔여 ~4% < 25%
        claims = self._claims(age_seconds=23 * 3600)
        assert should_rotate_session(claims) is True

    def test_threshold_boundary(self) -> None:
        # 잔여 정확히 25% → False (strict less-than)
        claims = self._claims(age_seconds=18 * 3600)  # 24h-18h=6h=25%
        assert should_rotate_session(claims, threshold_ratio=0.25) is False

    def test_missing_claims_no_rotation(self) -> None:
        assert should_rotate_session({}) is False
        assert should_rotate_session({"iat": 0}) is False
