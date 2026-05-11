"""Pytest 설정. bug_audit 마커 등록."""
from __future__ import annotations

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "bug_audit: Sprint 0 버그 감사 회귀 방지 테스트 (Critical+Major 18건)",
    )
