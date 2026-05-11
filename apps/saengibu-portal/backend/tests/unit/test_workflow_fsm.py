"""FSM 상태 머신 회귀 테스트.

Sprint 0 / Plan: tender-questing-sloth
- C-7 정책 주석 회귀
- M-4 CORRECTION_PENDING → REVIEW_1 전이 추가
"""
from __future__ import annotations

import pytest

from app.services.workflow.fsm import (
    Event,
    Status,
    TRANSITIONS,
    WorkflowError,
    next_status,
    step_no_for,
)


@pytest.mark.bug_audit
class TestFsmTransitions:
    def test_draft_to_review_1_on_submit(self) -> None:
        assert next_status("draft", Event.SUBMIT) == Status.REVIEW_1

    def test_review_1_approve_to_review_2(self) -> None:
        assert next_status("review_1", Event.APPROVE) == Status.REVIEW_2

    def test_review_3_approve_to_approved(self) -> None:
        assert next_status("review_3", Event.APPROVE) == Status.APPROVED

    @pytest.mark.parametrize("from_status", ["review_1", "review_2", "review_3"])
    def test_reject_returns_to_draft(self, from_status: str) -> None:
        assert next_status(from_status, Event.REJECT) == Status.DRAFT

    def test_correction_pending_principal_sign(self) -> None:
        assert next_status("correction_pending", Event.PRINCIPAL_SIGN) == Status.APPROVED

    def test_correction_pending_submit_to_review_1(self) -> None:
        # M-4: 정정 요청 후 수정본 재제출 경로
        assert next_status("correction_pending", Event.SUBMIT) == Status.REVIEW_1

    def test_invalid_transition_raises(self) -> None:
        with pytest.raises(WorkflowError):
            next_status("draft", Event.APPROVE)

    def test_unknown_status_raises(self) -> None:
        with pytest.raises(WorkflowError):
            next_status("nonexistent", Event.SUBMIT)

    def test_unknown_event_raises(self) -> None:
        with pytest.raises(WorkflowError):
            next_status("draft", "fly_to_moon")


@pytest.mark.bug_audit
class TestStepNoForStatus:
    def test_review_status_to_step_no(self) -> None:
        assert step_no_for("review_1") == 1
        assert step_no_for("review_2") == 2
        assert step_no_for("review_3") == 3

    def test_non_review_status_returns_none(self) -> None:
        assert step_no_for("draft") is None
        assert step_no_for("approved") is None


@pytest.mark.bug_audit
def test_transitions_table_includes_correction_submit() -> None:
    """M-4 회귀: 테이블에 (CORRECTION_PENDING, SUBMIT) 키가 있어야 한다."""
    assert (Status.CORRECTION_PENDING, Event.SUBMIT) in TRANSITIONS
