# ARCHITECTURE — saengibu-portal

> C4 Level 1~2. 시스템 컨텍스트 → 컨테이너 → 핵심 컴포넌트.

## 0. 아키텍처 원칙

1. **훈령 제555호가 시스템 정체성.** "AI가 대신 쓰지 않는다"를 코드/UX/프롬프트 3중 가드레일로.
2. **결정적(deterministic) 검증과 확률적(LLM) 판단 분리.** Byte·금지어·문체는 규칙, 개별성·과장은 LLM.
3. **학생 개인정보 외부 API 이탈 금지.** 실명·식별자 마스킹 → 외부 LLM → 치환 복원.
4. **영역(section) 단위 도메인 모델.** NEIS 화면 구조와 1:1 매핑되어야 복사·검증 두 문제가 동시에 풀린다.
5. **교사가 먼저 쓰고 → AI가 피드백.** 초안 저장 전에 AI 생성 코드 경로 없음.

---

## 1. C4 Level 1 — System Context

```
┌─────────────────────────────────────────────────────────────┐
│                       School Environment                       │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │ 교사      │   │ 부장/교감 │   │ 교장      │   │ 관리자    │   │
│  │ (작성자)  │──▶│ (검토자)  │──▶│ (승인자)  │   │ (시스템)  │   │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   │
│       │              │              │              │          │
│       ▼              ▼              ▼              ▼          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              saengibu-portal                            │  │
│  │   작성 · AI피드백 · 1~3검 워크플로우 · NEIS 복사 최적화   │  │
│  └────────────────┬───────────────┬───────────────┬───────┘  │
│                   │               │               │           │
└───────────────────┼───────────────┼───────────────┼───────────┘
                    │               │               │
                    ▼               ▼               ▼
          ┌──────────────┐  ┌─────────────┐ ┌──────────────┐
          │ Anthropic    │  │  NEIS       │ │ KERIS/커리어넷│
          │ /OpenAI API  │  │ (브라우저   │ │ (참고, 선택) │
          │ (마스킹 후)  │  │  수동 입력) │ └──────────────┘
          └──────────────┘  └─────────────┘
```

### 외부 의존

| 외부 시스템 | 통합 방식 | 데이터 방향 |
|---|---|---|
| NEIS (교육행정정보시스템) | **복사 전용**, 직접 API 연동 없음 | saengibu → 클립보드 → NEIS |
| Anthropic Claude / OpenAI | HTTPS, 마스킹된 텍스트만 | saengibu ↔ LLM |
| 학교 LDAP / SSO | OAuth2 / SAML (선택) | saengibu ← 학교 |

---

## 2. C4 Level 2 — Container

```
┌───────────────────────────────────────────────────────────────┐
│                      saengibu-portal                           │
│                                                                 │
│  ┌───────────────────┐     ┌──────────────────┐               │
│  │  Next.js 15       │     │  FastAPI         │               │
│  │  Frontend         │────▶│  Backend (sync)  │               │
│  │  (App Router)     │ API │                  │               │
│  │  - 영역별 에디터   │     │  - REST /api/v1  │               │
│  │  - 피드백 뷰       │     │  - RBAC guard    │               │
│  │  - NEIS 복사 버튼  │     │  - Workflow FSM  │               │
│  └───────────────────┘     └──────┬───────────┘               │
│                                   │                            │
│                     ┌─────────────┼─────────────┐              │
│                     ▼             ▼             ▼              │
│              ┌──────────┐  ┌────────────┐ ┌──────────┐        │
│              │Postgres16│  │  Redis     │ │ Celery   │        │
│              │+pgvector │  │ (Cache+Q)  │ │ Workers  │        │
│              └──────────┘  └────────────┘ └────┬─────┘        │
│                                                │               │
│                                                ▼               │
│                                        ┌──────────────┐        │
│                                        │  AI Pipeline │        │
│                                        │  (6 stages)  │        │
│                                        └──────┬───────┘        │
└───────────────────────────────────────────────┼───────────────┘
                                                │
                                                ▼
                                     ┌─────────────────┐
                                     │  External LLM   │
                                     │  (masked only)  │
                                     └─────────────────┘
```

### 컨테이너 책임

| 컨테이너 | 책임 | 배포 |
|---|---|---|
| **Next.js Frontend** | UI, 에디터, 피드백 렌더, 클립보드 최적화 | `apps/saengibu-portal/frontend/` |
| **FastAPI Backend** | REST API, RBAC guard, 상태 머신, 트랜잭션 경계 | `apps/saengibu-portal/backend/` |
| **PostgreSQL + pgvector** | 권위 저장소 + 실시간 벡터 검색 | 외부 관리 |
| **Redis** | 세션·캐시·Celery 브로커 | 외부 관리 |
| **Celery Workers** | 배치 유사도, 임베딩 갱신, 야간 리포트 | Backend와 동일 이미지 |
| **AI Pipeline** | Byte/금지어/문체/반복/LLM/체크리스트 6단계 | `backend/app/services/ai/` |

---

## 3. 핵심 컴포넌트 (Backend 기준)

```
backend/app/
├── api/
│   ├── v1/
│   │   ├── auth.py          로그인·관리자 승인
│   │   ├── schools.py       학교·조직도
│   │   ├── records.py       영역별 기록 CRUD
│   │   ├── reviews.py       1/2/3검 전이
│   │   ├── feedback.py      AI 피드백 요청
│   │   ├── duplicates.py    유사도 조회
│   │   ├── neis.py          NEIS 복사 최적화
│   │   └── dashboard.py     진행률·통계
│   └── deps.py              의존성 주입 (current_user, rbac_guard)
├── core/
│   ├── config.py            Pydantic Settings
│   ├── security.py          JWT·bcrypt
│   ├── rbac.py              Casbin 래퍼
│   └── logging.py           structlog
├── domain/
│   ├── school.py            School, Grade, Class, Department
│   ├── user.py              User, Role, Approval
│   ├── student.py           Student, Enrollment
│   ├── record.py            Record, Section, Version
│   ├── review.py            Review, ReviewStep, ReviewComment
│   ├── feedback.py          FeedbackReport, Violation
│   └── activity.py          ActivityPlan, ActivityShare
├── services/
│   ├── ai/
│   │   ├── pipeline.py      Pipeline Orchestrator
│   │   ├── byte_stage.py    Stage 1
│   │   ├── banned_stage.py  Stage 2 (금지어 사전)
│   │   ├── style_stage.py   Stage 3 (명사형 종결 등)
│   │   ├── repeat_stage.py  Stage 4 (임베딩+MinHash)
│   │   ├── llm_stage.py     Stage 5 (LLM JSON 스키마)
│   │   └── checklist_stage.py Stage 6
│   ├── byte/
│   │   └── cp949_counter.py NEIS 호환 Byte 카운터
│   ├── duplicate/
│   │   ├── embed.py         ko-sroberta
│   │   ├── ngram.py         kiwipiepy + MinHash LSH
│   │   └── individuality.py 학급 차별화 점수
│   ├── neis/
│   │   ├── normalize.py     CP949 호환 정규화
│   │   └── clipboard.py     영역별 복사 포맷
│   ├── mask/
│   │   └── pii.py           실명·학번 마스킹
│   └── workflow/
│       └── fsm.py           상태 머신 (draft→review_1→...→neis_copied)
└── workers/
    ├── nightly_similarity.py 야간 배치
    ├── embedding_backfill.py
    └── report_generator.py
```

---

## 4. 데이터 흐름 — "교사 초안 저장" 케이스

```
교사: [저장] 클릭
  │
  ▼
Frontend: POST /api/v1/records/{id}/draft (text)
  │
  ▼
Backend: rbac_guard(user, record, 'write') 통과
  │
  ▼
Domain: Record.new_version(text) — 이벤트 소싱
  │
  ├─▶ AI Pipeline (sync, <500ms 목표)
  │    ├─ Stage 1: Byte Counter (CP949)
  │    ├─ Stage 2: 금지어 regex 사전
  │    ├─ Stage 3: 문체 검사 (명사형 종결)
  │    ├─ Stage 4: 실시간 유사도 (pgvector top-10)
  │    └─ Stage 6: 체크리스트 (훈령 2개 질문)
  │
  ├─▶ Celery: enqueue_llm_feedback(version_id)
  │    └─ Stage 5: LLM 심층 분석 (비동기, ~5s)
  │
  └─▶ DB: feedback_reports INSERT (sync 결과)
  │
  ▼
Response: {violations: [...], byte_count, similar: [...]}
  │
  ▼
Frontend: 에디터 상단 인라인 배지·하이라이트
  │
  ▼
(몇 초 후 SSE/폴링으로 LLM 결과 합류)
```

---

## 5. 검토 워크플로우 — 상태 머신

상세: [WORKFLOW_1_2_3_REVIEW.md](./WORKFLOW_1_2_3_REVIEW.md)

```
draft ──submit──▶ review_1 ──approve──▶ review_2 ──approve──▶ review_3 ──approve──▶ approved ──copy──▶ neis_copied
  ▲                 │                      │                      │
  │                 │ reject               │ reject               │ reject
  └─────────────────┴──────────────────────┴──────────────────────┘
                           (kickback + comment)

approved ──correction_request──▶ correction_pending ──principal_sign──▶ approved
```

---

## 6. 배포 토폴로지

### MVP (단일 학교, ~500명)

- 단일 서버(4vCPU/16GB): Next.js + FastAPI + Postgres + Redis + Celery
- SSL: Let's Encrypt, Caddy reverse proxy
- 백업: pg_dump 일 1회 + 7일 보관

### 확장 (시·도 단위)

- Next.js: Vercel 또는 교육청 내부망 (NGINX + PM2)
- FastAPI: 컨테이너 3-way 수평 확장
- Postgres: primary + 2 read replica, pgvector는 primary에만
- Redis: Sentinel 3node
- Celery: 4 worker × 2 concurrency
- 임베딩 모델 서버: ONNX Runtime, 별도 컨테이너 (GPU 옵션)
- 로그: Loki + Grafana, 생기부 관련 감사로그는 별도 append-only 테이블 + S3 백업(준영구)

---

## 7. 관찰성·감사

- **구조화 로그**: structlog + JSON. `request_id`, `user_id`, `school_id`, `record_id` 필수 컨텍스트.
- **생기부 접근 감사**: `audit_log` 테이블 append-only, 로그인/열람/수정/복사/결재 모두 기록. 개인정보보호법 §15 "업무 관련성" 증빙.
- **AI 호출 감사**: LLM 프롬프트(마스킹 후)·응답·모델버전·토큰수 저장. 추후 재생성·책임추적 가능.
- **메트릭**: Prometheus. 파이프라인 단계별 레이턴시, LLM 비용, 금지어 탐지 건수, 중복 알림 건수.

---

## 8. 보안·프라이버시

| 항목 | 조치 |
|---|---|
| 전송 | HTTPS only, HSTS |
| 저장 | Postgres TDE 또는 컬럼 암호화 (성명·주민번호) |
| 인증 | JWT (15분 access + 24h refresh), 관리자 승인 후 활성화 |
| 권한 | Casbin RBAC + ABAC (학년·담임 관계) |
| LLM 마스킹 | 성명·학번 → `<S001>`·`<N001>` 치환, 응답에서 복원 |
| 감사로그 | 준영구 (졸업 후 5년+), append-only |
| 백업 | 암호화 후 보관, 복호화 키 분리 관리 |
| 브라우저 | CSP strict, 서비스워커 쿠키 분리 |

---

## 9. 주요 의사결정(ADR 후보)

| # | 결정 | 이유 |
|---|---|---|
| ADR-001 | pgvector 채택 (Chroma/FAISS 대신) | 메타데이터 JOIN 빈번, 단일 DB 엔진 운영 |
| ADR-002 | Casbin 채택 (OpenFGA 대신) | Python 생태계 호환, 학년/담임 조건 표현 충분 |
| ADR-003 | LLM은 Stage 5만 | 나머지 결정적, 비용·지연·할루시네이션 최소화 |
| ADR-004 | NEIS 직접 API 연동 없음 | 공식 API 부재, 규정 위반 리스크 |
| ADR-005 | 영역 단위 도메인 모델 | NEIS 1:1 매핑, 복사·검증 단순화 |
| ADR-006 | 이벤트 소싱 (Record.version) | 검토 이력·감사 요구 충족 |
| ADR-007 | 한국어 임베딩 `jhgan/ko-sroberta-multitask` | KLUE-STS 84.77, 생기부 문체 적합 |
| ADR-008 | Byte 계산은 CP949 | NEIS 실제 인코딩과 일치, EUC-KR보다 확장 한글 포함 |
| ADR-013 | 순환 FK는 DEFERRABLE | 이벤트 소싱 첫 버전 삽입 호환 |
| ADR-014 | RLS 전 테이블 + SET LOCAL | 테넌시 DB 레벨 격리, 권한 버그 방어 |
| ADR-015 | 감사 해시 체인 + S3 WORM | 준영구 무결성, superuser 변조 탐지 |
| ADR-016 | 실시간 유사도는 HNSW 단독 | MinHash는 야간 배치만, 복잡도 절감 |
| ADR-017 | 임베딩 쓰기 비동기 | HNSW 동시 저장 락 회피 |
| ADR-018 | PII 마스킹은 전교 학생 사전 | 본문 내 타 학생 실명 유출 방지 |
| ADR-019 | LLM 실패는 워크플로우 비차단 | 외부 API 장애가 결재 멈추지 않음 |
