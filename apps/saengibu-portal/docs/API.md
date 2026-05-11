# API — saengibu-portal Backend

> FastAPI 0.115+ · Pydantic v2 · JSON over HTTPS · 기본 prefix `/api/v1`

## 규약

- **인증**: `Authorization: Bearer <jwt>`. `/auth/*` 예외.
- **학교 스코프**: 모든 응답은 현재 사용자의 `school_id`로 자동 격리 (RLS).
- **에러**: [RFC 7807 Problem+JSON] `{type, title, status, detail, instance}`.
- **페이지네이션**: 커서 기반 `?cursor=...&limit=50`, 응답에 `next_cursor`.
- **ID**: 모든 리소스 ID는 UUID v4.
- **시간**: ISO 8601 + `Z` (UTC).

---

## 0. Auth

### POST `/auth/register`

```jsonc
// Request
{ "email": "...", "password": "...", "name": "...", "employee_no": "...", "school_neis_code": "..." }
// Response 202 (대기, 관리자 승인 필요)
{ "user_id": "...", "status": "pending" }
```

### POST `/auth/login`

```jsonc
// Request
{ "email": "...", "password": "..." }
// Response 200
{ "access_token": "...", "refresh_token": "...", "expires_in": 900 }
```

### POST `/auth/refresh`

### POST `/auth/logout`

### GET `/auth/me`
→ `{ id, email, name, roles: [...], school, homeroom_of: [...], teaches: [...] }`

---

## 1. 학교 관리 (admin)

- `GET  /schools/{id}` — 학교 정보
- `POST /schools/{id}/years` — 학년도 생성
- `POST /schools/{id}/grades` — 학년 생성
- `POST /schools/{id}/classes` — 학급 생성
- `POST /schools/{id}/departments` — 부서 생성
- `GET  /schools/{id}/users?status=pending` — 승인 대기 목록
- `POST /users/{id}/approvals` — 승인/반려
- `POST /users/{id}/roles` — 역할 부여(학교장/교감/부장/담임/교과)
- `POST /homeroom-assignments` — 담임 지정
- `POST /teacher-assignments` — 교과 배정

---

## 2. 학생

- `GET  /students?class_id=&year_id=&cursor=`
- `POST /students` — 학생 등록 (관리자)
- `GET  /students/{id}`
- `POST /students/{id}/enrollments` — 반편성/전입/전출
- `GET  /students/{id}/overview?year_id=` — 학생별 전체 기록 개요

---

## 3. 기록 (핵심)

### GET `/records?student_id=&year_id=&section=&status=`

필터: 학생, 학년도, 영역(`haengjongjeui`, `chang_jayul`, …), 상태.

### GET `/records/{id}`

```jsonc
{
  "id": "...",
  "section": { "code": "haengjongjeui", "name": "행동특성 및 종합의견", "byte_limit": 300 },
  "student": { "id": "...", "name_masked": "홍**" },
  "author_id": "...",
  "status": "draft",
  "current_version": {
    "id": "...", "version_no": 3,
    "text": "...",
    "byte_count": 287,
    "created_at": "2026-04-14T..."
  },
  "latest_feedback": { "report_id": "...", "total_violations": 0, "total_warnings": 2 }
}
```

### POST `/records` — 새 기록 생성

```jsonc
{ "student_id": "...", "section_code": "haengjongjeui", "year_id": "...", "subject_id": null }
```

### POST `/records/{id}/draft` — 초안 저장 (새 버전 생성 + AI Stage 1-4,6 실행)

```jsonc
{ "text": "..." }
// Response 200
{
  "version_id": "...",
  "byte_count": 287,
  "violations": [ /* Stage 1-4,6 즉시 결과 */ ],
  "llm_feedback_status": "pending"   // Stage 5 비동기
}
```

### GET `/records/{id}/versions`
→ 버전 이력 (페이지네이션)

### GET `/records/{id}/versions/{version_id}/diff`
→ 직전 버전과 diff

---

## 4. AI 피드백

### GET `/feedback/{report_id}`

```jsonc
{
  "id": "...",
  "version_id": "...",
  "stages": {
    "byte":     { "count": 287, "limit": 300, "over": false },
    "banned":   { "matches": [ { "rule": "exam.TOEIC", "span": [12,17], "text": "TOEIC" } ] },
    "style":    { "issues": [ { "rule": "nouning_end", "span": [..], "message": "명사형 어미 종결 아님" } ] },
    "repeat":   { "similar": [ { "target_version_id": "...", "cosine": 0.93, "match_type": "same_teacher_other_student" } ] },
    "llm":      { "violations": [ { "rule": "exaggeration", "span": [..], "suggestion": "..." } ] },
    "checklist": {
      "no_fabrication_confirmed": null,
      "guidelines_reviewed": null
    }
  },
  "total_violations": 1,
  "total_warnings": 2
}
```

### POST `/feedback/{report_id}/checklist`

```jsonc
{ "no_fabrication_confirmed": true, "guidelines_reviewed": true }
```

### POST `/records/{id}/feedback/regenerate?stages=llm,repeat`
→ 특정 단계 재실행 (LLM 실패 시 등)

### GET `/records/{id}/similar?threshold=0.85`
→ 유사 기록 조회 (배치 결과 포함)

---

## 5. 검토 (1/2/3검)

### POST `/records/{id}/reviews`
→ 현재 버전으로 검토 요청. 상태: `draft` → `review_1`.

### GET `/reviews?assigned_to_me=true&status=in_progress`
→ 내가 결재해야 할 대기 목록.

### POST `/reviews/{id}/steps/{step_no}/decide`

```jsonc
{ "decision": "approved" | "rejected", "comment": "..." }
```

- `approved`: 다음 단계 활성화 or `approved` 전이
- `rejected`: `draft` 복귀, 모든 step decision 무효화, 댓글 보존

### POST `/reviews/{id}/steps/{step_no}/comments`

```jsonc
{ "body": "...", "span_start": 12, "span_end": 34 }
```

---

## 6. NEIS 복사 최적화

### POST `/records/{id}/neis/render`

```jsonc
// Request (선택)
{ "format": "clipboard" | "preview" }
// Response 200
{
  "text": "…CP949 안전·CRLF 정규화된 최종 텍스트…",
  "byte_count": 287,
  "warnings": [ { "original": "—", "replaced_with": "-", "span": [45,46] } ]
}
```

### POST `/records/{id}/neis/copy-event`
→ 복사 버튼 누름 이벤트 기록 (`neis_copy_logs`).

### POST `/records/{id}/neis/summarize?target_bytes=290`
→ LLM 기반 초과분 요약 제안 (별도 비동기 엔드포인트).

---

## 7. 중복·유사도

### GET `/duplicates?class_id=&year_id=&threshold=0.85`
→ 야간 배치 결과를 관리자가 조회.

### GET `/duplicates/{match_id}`
→ 양측 본문 비교 (마스킹).

### POST `/duplicates/{match_id}/review`

```jsonc
{ "decision": "legit" | "needs_rewrite", "note": "..." }
```

---

## 8. 활동 공유

- `GET  /activity-plans?area=&scope_type=` 
- `POST /activity-plans` — 계획 생성
- `POST /activity-plans/{id}/shares` — 공유 대상 지정
- `POST /activity-plans/{id}/fork` — 템플릿 복제
- `POST /records/{id}/activity-links` — 기록에 계획 연결

---

## 9. 대시보드

- `GET /dashboard/teacher?year_id=` — 내 담당 진행률
- `GET /dashboard/class/{class_id}?year_id=` — 학급 진행률
- `GET /dashboard/school?year_id=` — 학교 전체 (관리자)
- `GET /dashboard/review-queue?assigned_to_me=true` — 검토 대기
- `GET /dashboard/quality-trend?year_from=&year_to=` — 품질 트렌드

---

## 10. 사전 관리 (관리자)

- `GET  /banned-dict?category=`
- `POST /banned-dict/entries`
- `PATCH /banned-dict/entries/{id}`
- `POST /banned-dict/entries/{id}/deactivate`
- `GET  /banned-whitelist`

---

## 11. 감사

- `GET /audit-logs?user_id=&action=&from=&to=` (관리자)
- `GET /audit-logs/verify-chain?from=&to=` (관리자) — 해시 체인 무결성 검증

---

## 11.5 자료제공 (훈령 제18조 6가지 예외)

- `POST /disclosure-requests` — 자료제공 요청 생성 (담임 또는 관리자)
  ```jsonc
  {
    "student_id": "...",
    "purpose": "advancement | employment | legal_order | statistics_research | principal_discretion | self_request",
    "legal_basis": "초·중등교육법 제25조 제2항",
    "recipient": "○○고등학교 입학관리실",
    "scope": { "sections": ["haengjongjeui","setuk_subject"], "year_range": [2024, 2026] },
    "consent_document_ref": "s3://...",
    "expires_at": "2026-12-31"
  }
  ```
- `POST /disclosure-requests/{id}/approve` — 학교장 결재
- `POST /disclosure-requests/{id}/disclose` — 실제 제공 (PDF/비식별 CSV)
- `GET  /disclosure-requests?student_id=&purpose=&status=` — 학생별 제공 이력

---

## 12. WebSocket / SSE

- `GET /sse/records/{id}/feedback` — LLM 피드백 완료 푸시
- `GET /sse/reviews/assigned` — 내 결재 큐 실시간

---

## 에러 코드 카탈로그

| code | status | 의미 |
|---|---|---|
| `auth.invalid_credentials` | 401 | 로그인 실패 |
| `auth.account_pending` | 403 | 관리자 승인 대기 |
| `rbac.forbidden` | 403 | 권한 부족 |
| `rbac.wrong_input_role` | 422 | 잘못된 영역 입력 주체 |
| `workflow.invalid_transition` | 409 | 상태 전이 불가 |
| `record.byte_over_limit` | 422 | Byte 초과 |
| `record.banned_term` | 422 | 금지어 탐지 (block) |
| `feedback.llm_unavailable` | 503 | LLM 일시 오류 |
| `neis.incompatible_char` | 422 | CP949 미지원 문자 |

---

## OpenAPI

- `GET /openapi.json` — 자동 생성
- `GET /docs` — Swagger UI (개발 환경만)
- `GET /redoc` — ReDoc
