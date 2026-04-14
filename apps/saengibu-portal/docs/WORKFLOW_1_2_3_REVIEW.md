# WORKFLOW — 1/2/3검 검토 상태 머신

> 교사 작성 → 1검 → 2검 → 3검 → 확정 → NEIS 복사 · 훈령 제555호·현장 관행 기반

## 0. 전체 플로우

```
 draft ──submit──▶ review_1 ──approve──▶ review_2 ──approve──▶ review_3 ──approve──▶ approved ──copy──▶ neis_copied
   ▲                 │                      │                      │
   │                 │ reject               │ reject               │ reject
   └─────────────────┴──────────────────────┴──────────────────────┘
                          (kickback with comment → draft)

 approved ──correction_request──▶ correction_pending ──principal_sign──▶ approved (재승인)
```

### 상태

| State | 의미 |
|---|---|
| `draft` | 교사 작성·수정 중 |
| `review_1` | 1검 진행 (담임 or 교과부장) |
| `review_2` | 2검 진행 (학년부장 or 교무부장) |
| `review_3` | 3검 진행 (교감 or 교장) |
| `approved` | 확정, NEIS 복사 가능 |
| `neis_copied` | NEIS에 실제 복사된 상태 (참고) |
| `correction_pending` | 정정 요청됨 (학교장 승인 대기) |

---

## 1. 단계별 검토자

| Step | 기본 담당 | 대체 |
|---|---|---|
| 1검 | 담임(행종·창체·출결·독서 등) / 교과부장(세특·교과 독서) | 학년부장이 대행 가능 |
| 2검 | 학년부장 | 교무부장 (교차 검토 or 대체) |
| 3검 | 교감 | 교장 (교감 부재 시 직접) |

### 자동 할당 규칙

- **1검 대상자 결정**:
  - section이 `setuk_subject` → 해당 교과의 교과부장
  - 그 외 → 해당 학생의 담임 (단, 작성자가 담임이면 1검은 교무부장 대체)
- **2검**: 해당 학년의 학년부장, 없으면 교무부장
- **3검**: 교감 → 없으면 교장

---

## 2. 전이 규칙

### 2.1 `draft → review_1` (submit)

**전제 조건** (모두 AND):

- 작성자가 쓰기 권한 보유 (RBAC)
- AI Stage 1: `byte_count ≤ byte_limit` (초과 block)
- AI Stage 2: `banned.matches where severity='block'` 가 0건 (그 외는 warn 허용)
- AI Stage 6: 체크리스트 3항목 모두 체크
- 본문이 비어있지 않음 (조건부 제외: "참여 못한 학생 사유 기재" 케이스)

**부작용**:
- `reviews` 행 생성, `review_steps` 3행 pending으로 생성
- 1검 대상자에게 알림 (대시보드 배지 + 선택적 이메일)

### 2.2 `review_N → review_(N+1)` (approve)

- `review_steps.step_no == N`의 `decision = 'approved'`, `decided_at = now()`
- N < 3 이면 다음 step 활성화, 해당 검토자에게 알림
- N == 3 이면 `records.status = 'approved'`, `review.status = 'approved'`

### 2.3 `review_N → draft` (reject, kickback)

- 현 step의 `decision = 'rejected'`, `review.status = 'rejected'`, `review.closed_at = now()`
- **하위 step들의 이전 결과는 모두 invalidate**: `review_steps.decision = NULL, decided_at = NULL` for step_no ≤ N
- 재제출 시 **새 `reviews` 행** 생성 (이전 이력 보존)
- 반려 코멘트 **필수** (본문 span 연결 가능)
- 작성자에게 알림
- 감사 로그: `review.invalidate_steps` 액션, 영향받은 step 수·이유 기록

**예외**: "경미한 오탈자 재확인" — `review.type = 'minor'`로 표시하면 같은 step에서 다시 decide 가능 (학교 설정)

### 2.4 `approved → correction_pending`

- 훈령 제19조 정정 절차. 정정요청자·사유·diff 필수.
- 이후 학교장 서명(`principal_sign`)으로만 재확정.

### 2.5 `approved → neis_copied`

- `POST /records/{id}/neis/copy-event` 호출 시.
- 조건: 본인 작성자 또는 담임.

---

## 3. 상태 머신 구현 (FSM)

```python
# backend/app/services/workflow/fsm.py
from enum import StrEnum

class Status(StrEnum):
    DRAFT = 'draft'
    REVIEW_1 = 'review_1'
    REVIEW_2 = 'review_2'
    REVIEW_3 = 'review_3'
    APPROVED = 'approved'
    NEIS_COPIED = 'neis_copied'
    CORRECTION_PENDING = 'correction_pending'

TRANSITIONS: dict[tuple[Status, str], Status] = {
    (Status.DRAFT, 'submit'):     Status.REVIEW_1,
    (Status.REVIEW_1, 'approve'): Status.REVIEW_2,
    (Status.REVIEW_2, 'approve'): Status.REVIEW_3,
    (Status.REVIEW_3, 'approve'): Status.APPROVED,
    (Status.REVIEW_1, 'reject'):  Status.DRAFT,
    (Status.REVIEW_2, 'reject'):  Status.DRAFT,
    (Status.REVIEW_3, 'reject'):  Status.DRAFT,
    (Status.APPROVED, 'copy'):    Status.NEIS_COPIED,
    (Status.NEIS_COPIED, 'copy'): Status.NEIS_COPIED,  # idempotent
    (Status.APPROVED, 'correction_request'): Status.CORRECTION_PENDING,
    (Status.CORRECTION_PENDING, 'principal_sign'): Status.APPROVED,
}

def transition(record, event: str, actor, **ctx) -> Status:
    nxt = TRANSITIONS.get((Status(record.status), event))
    if not nxt:
        raise WorkflowError(f"cannot {event} from {record.status}")
    _validate_guards(record, event, actor, ctx)
    record.status = nxt.value
    return nxt
```

### 3.1 가드 (guards)

```python
def _validate_guards(record, event, actor, ctx):
    if event == 'submit':
        _require_byte_under_limit(record)
        _require_no_block_violations(record)
        _require_checklist_complete(record)
    elif event == 'approve':
        step_no = {Status.REVIEW_1:1, Status.REVIEW_2:2, Status.REVIEW_3:3}[Status(record.status)]
        _require_reviewer_role(actor, record, step_no)
    elif event == 'reject':
        _require_rejection_comment(ctx)
    elif event == 'correction_request':
        _require_diff_and_reason(ctx)
    elif event == 'principal_sign':
        if 'principal' not in actor.roles: raise PermissionError
```

---

## 4. 반려(kickback) 처리 정책

| 반려 사유 | 권장 대응 |
|---|---|
| Byte 초과 (놓친 상태에서 승인된 경우) | 담임이 수정, 동일 영역 내 재작성 |
| 금지어 의심 | 작성자가 맥락 해명 또는 수정 |
| 개별성 부족 | 작성자가 구체 사례 보강 |
| 학생 확인사항 | 담임이 추가 관찰 후 보강 |
| 영역 부적합 | 다른 영역으로 이관 (새 record 생성) |

**코멘트 연결**: `review_comments.span_start/end`로 본문 범위 지정 → UI에서 하이라이트.

---

## 5. 알림(notification)

| 이벤트 | 알림 대상 | 채널 |
|---|---|---|
| 검토 요청 도착 | 해당 step 검토자 | 대시보드 배지 + 선택 이메일 |
| 반려 | 작성자 | 대시보드 + 이메일 (필수) |
| 승인 완료 | 작성자 | 대시보드 |
| 정정 승인 | 요청자 | 대시보드 + 이메일 |
| 긴급(편집 잠금) | 학년부장 + 관리자 | 대시보드 |

---

## 6. 감사 로그 연동

각 상태 전이는 `audit_logs`에 기록:

```jsonc
{
  "action": "review.decide",
  "user_id": "...",
  "resource_type": "review_step",
  "resource_id": "...",
  "metadata": {
    "record_id": "...",
    "step_no": 2,
    "decision": "approved",
    "comment_hash": "sha256:..."
  }
}
```

---

## 7. 대시보드 큐

### 작성자 대시보드

- **내 진행률**: 영역별 (draft/review/approved) 비율
- **반려 이력**: 최근 10건

### 검토자 대시보드

- **검토 대기 큐**: 내가 step-대상인 review 목록 (오래된 순)
- **오늘의 처리**: 승인/반려 건수
- **이슈 통계**: 반려 사유 빈도 (개별성 부족, Byte 초과 등)

### 관리자 대시보드

- **전교 진행률**: 기한 대비 완료율 (학년별, 영역별)
- **정정 요청 목록**: 학교장 결재 대기
- **품질 트렌드**: 월별 반려율, AI block 탐지율

---

## 8. 기한·일정 관리

- 각 영역별 **작성 기한** · **1검 기한** · **2검 기한** · **3검 기한** 을 학교장이 연초 설정
- `records.deadline_draft`, `.deadline_review_1` 등 (별도 테이블 `record_deadlines` 사용 가능)
- D-3, D-1, D-0 자동 알림
- 기한 초과 시 대시보드에 적색 경보 (단, 강제 잠금은 없음)

---

## 9. 정정(correction) 상세

### 훈령 제19조 근거

> "학교생활기록부의 자료는 졸업 후 정정할 수 없다. 단, 객관적 증빙자료가 있는 경우 학교장의 승인 아래 정정 가능."

### 시스템 처리

1. `approved` 기록의 diff 제안 → `correction_logs.from_version`, `.to_version` (새 버전 생성, 미승인)
2. 담임/관계자가 증빙자료 업로드 (선택 기능)
3. 학교장 결재 (`principal_sign` 이벤트)
4. `correction_logs.approved_at` 기록, `records.status = 'approved'` 복귀, `records.current_version = to_version`

---

## 9.5 `neis_copied` 이후 재편집 경로

`neis_copied` 상태에서 교사가 오탈자를 발견하면 두 경로로 분기:

| 변경 유형 | 경로 |
|---|---|
| 단순 오탈자·띄어쓰기 | 학교 정책에 따라 정정 요청 없이 새 `draft` 분기 허용 가능 (학교장 사전 허용 토글) → 새 버전 작성 → 1~3검 재진행 → `approved` → NEIS 재복사 |
| 사실관계 오류·추가 반영 | **정정(correction) 워크플로우 필수** → `correction_pending` → 학교장 결재 |

- 시스템 기본값: **정정 워크플로우 필수** (감사 안전)
- 학교장이 "경미한 오탈자 자체 수정 허용"을 ON 하면 앞 경로도 활성화. 감사로그에 명시적으로 기록.

---

## 9.6 학폭 조치상황 보존·자동 삭제

훈령 제16조의2에 따른 조치호별 삭제 규정(2024.3.1. 이후 신고 기준):

| 조치 | 삭제 시기 | `records.retention_reason` |
|---|---|---|
| 1호(서면 사과)·2호(접촉금지)·3호(교내 봉사) | 졸업과 동시 | `immediate_on_graduation` |
| 4호(사회봉사)·5호(특별교육) | 졸업 후 2년 | `post_grad_2y` |
| 6호(출석정지)·7호(학급교체)·8호(전학) | 졸업 후 4년 | `post_grad_4y` |
| 9호(퇴학) | 삭제 대상 아님 | `permanent` |

### 자동 처리

- 학폭 조치 기록 생성 시 `records.retention_until` 계산 (`graduation_date + interval`)
- Celery 스케줄러 `workers/retention_scheduler.py`가 매일 자정 실행:
  1. `retention_until <= today` 대상 record 조회
  2. 감사 로그 기록 (삭제 전 해시·내용 보존)
  3. `record_versions.text` NULL 처리 (content purge), `records`는 메타만 유지
  4. 학교장·관리자에게 삭제 리포트 전송
- 훈령 개정 시 룰 버전 갱신 (`rules_version`) → 소급 보존 여부 판단

---

## 10. 테스트 시나리오

| # | 시나리오 |
|---|---|
| 1 | 담임이 행종 작성 → 1검(본인 제외, 교무부장 대행) → 2검(학년부장) → 3검(교감) → 승인 |
| 2 | 교과교사가 세특 작성 → 1검(교과부장) → 2검(교무부장) → 3검(교장) → 승인 |
| 3 | 2검에서 반려 → 담임이 수정 → 다시 1검부터 |
| 4 | Byte 초과 상태로 submit 시도 → 거부 |
| 5 | 금지어(TOEIC) 포함 상태로 submit → 거부 |
| 6 | 승인 후 NEIS 복사 이벤트 → `neis_copied` 전이 |
| 7 | 승인 후 정정 요청 → 학교장 결재 후 `approved` 복귀 |
| 8 | 1검 대상자가 담임 본인과 일치 → 자동으로 교무부장 대행 배정 |
| 9 | 검토자 권한 없는 교사가 approve 시도 → 403 |
| 10 | 같은 record 동시 submit (충돌) → optimistic locking으로 한쪽만 성공 |
