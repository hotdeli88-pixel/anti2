"""검토 워크플로우 상태 머신."""
from __future__ import annotations

from enum import StrEnum


class Status(StrEnum):
    DRAFT = "draft"
    REVIEW_1 = "review_1"
    REVIEW_2 = "review_2"
    REVIEW_3 = "review_3"
    APPROVED = "approved"
    NEIS_COPIED = "neis_copied"
    CORRECTION_PENDING = "correction_pending"


class Event(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    COPY = "copy"
    CORRECTION_REQUEST = "correction_request"
    PRINCIPAL_SIGN = "principal_sign"


TRANSITIONS: dict[tuple[Status, Event], Status] = {
    (Status.DRAFT, Event.SUBMIT): Status.REVIEW_1,
    (Status.REVIEW_1, Event.APPROVE): Status.REVIEW_2,
    (Status.REVIEW_2, Event.APPROVE): Status.REVIEW_3,
    (Status.REVIEW_3, Event.APPROVE): Status.APPROVED,
    (Status.REVIEW_1, Event.REJECT): Status.DRAFT,
    (Status.REVIEW_2, Event.REJECT): Status.DRAFT,
    (Status.REVIEW_3, Event.REJECT): Status.DRAFT,
    (Status.APPROVED, Event.COPY): Status.NEIS_COPIED,
    (Status.NEIS_COPIED, Event.COPY): Status.NEIS_COPIED,
    (Status.APPROVED, Event.CORRECTION_REQUEST): Status.CORRECTION_PENDING,
    (Status.CORRECTION_PENDING, Event.PRINCIPAL_SIGN): Status.APPROVED,
    # M-4: 정정 요청 후 교사가 수정본을 다시 1검부터 받도록 SUBMIT 전이 허용.
    # 정책 (PO 합의 근거: 정정은 본문 수정 가능 → 새 1검부터 시작이 안전).
    (Status.CORRECTION_PENDING, Event.SUBMIT): Status.REVIEW_1,
}


class WorkflowError(Exception):
    pass


def next_status(current: str, event: Event | str) -> Status:
    try:
        cur = Status(current)
    except ValueError as e:
        raise WorkflowError(f"unknown status {current!r}") from e
    try:
        evt = Event(event)
    except ValueError as e:
        raise WorkflowError(f"unknown event {event!r}") from e
    nxt = TRANSITIONS.get((cur, evt))
    if nxt is None:
        raise WorkflowError(f"cannot {evt} from {cur}")
    return nxt


def step_no_for(status: str) -> int | None:
    return {
        Status.REVIEW_1.value: 1,
        Status.REVIEW_2.value: 2,
        Status.REVIEW_3.value: 3,
    }.get(status)
