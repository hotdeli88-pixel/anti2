# saengibu-portal TODO 로드맵

> Codex 울트라리뷰(`docs/ULTRAREVIEW_CODEX.md`) 결과를 우선순위별로 유목화한 실행 계획.
> 생성일: 2026-04-20

**권장 실행 순서**: P0(병렬) → P2 Quick Wins 병행 → P1 Records → P3 CI/테스트 → P4 데이터 → P5는 각 스프린트 끝에서 관련 문서만 갱신.

---

## 🟥 P0. 보안 기반 (Sprint A · 즉시 착수)

테넌트 누출과 권한 우회를 먼저 막지 않으면 이후 기능이 모두 리스크.

- [ ] **1. RLS 마이그레이션 활성화**
  - `alembic/versions/00012_enable_rls.py` 추가
  - `records / students / users / audit_logs / feedback_reports` 정책 생성
  - `docs/ERD.md:7` 명세와 실제 DB 상태 일치시키기
- [ ] **2. RBAC 스코프 가드 도입**
  - `require_record_scope(action)` 의존성 신설 (담임·교과·학년 매칭)
  - `reviews.decide_step`에 `SELECT ... FOR UPDATE` 결합
  - `backend/app/api/v1/reviews.py:157` 역할명만 체크하는 로직 대체
- [ ] **3. 대시보드 집계 학교 필터**
  - `backend/app/api/v1/dashboard.py:51` `FeedbackReport → RecordVersion → Record` 조인
  - `Record.school_id == user.school_id` 조건 추가
- [ ] **4. 감사 해시체인 동시성 락**
  - `backend/app/services/audit/logger.py:27` 에 `pg_advisory_xact_lock(hash(school_id))` 또는 head row `FOR UPDATE`
- [ ] **5. 프로덕션 fail-fast**
  - `environment != development`에서 기본 `SESSION_SECRET` 차단
  - 빈 `GOOGLE_CLIENT_ID` / 빈 `ALLOWED_EMAIL_DOMAINS` / `COOKIE_SECURE=false` 시 startup 중단
- [ ] **6. PII 노출 제거**
  - `auth.domain_forbidden` detail의 email 전체 제거 (도메인만 노출)
  - 감사 metadata email/reason → hash 또는 길이 제한/마스킹
- [ ] **7. 보안 회귀 테스트**
  - 타 학교 fixture로 RLS·RBAC matrix 통합 테스트 추가

---

## 🟧 P1. 핵심 제품 완성 (Sprint B)

프론트 위저드가 데모 하드코딩이라 제품이 실제로 돌아가지 않는 상태.

- [ ] **8. `/records` 라우터 구현**
  - `create` / `save_draft` / `submit_review` / `get_record` / `versions`
  - `docs/API.md:101`, `docs/API.md:162` 명세 기준
  - `backend/app/api/__init__.py`에 `records.py` include 추가
- [ ] **9. Deterministic 피드백 엔드포인트**
  - byte(CP949) 검증 (`cp949_counter` 재사용)
  - 금지어 / 중복 문장 서버 평가
- [ ] **10. 프론트 위저드 ↔ 서버 연결**
  - Step 1: 학생/과목 API 연동
  - Step 2: `useStandards` 훅 사용 (현재 정적 `MATH_STANDARDS` 제거)
  - Step 4: `POST /records/{id}/draft` mutation
  - Step 6: `POST /records/{id}/reviews` mutation
  - `frontend/app/writer/new/subject/page.tsx:21-26, 58-60, 311-317` 하드코딩 제거
- [ ] **11. OAuth 학교 귀속 정규화**
  - `school_domains` 테이블 신설 또는 초대 코드/NEIS school code 기반 가입
  - `backend/app/api/v1/auth.py:94-103` 의 `select(School).limit(1)` 제거

---

## ⚡ P2. Quick Wins (1일 내, 병행 가능)

값싸고 영향 큰 정리. P0·P1과 병행.

- [ ] **12. 실제 버그: approvals 필터 파라미터 불일치**
  - `frontend/lib/queries.ts:42` `?status=` → `?status_filter=`
  - 현재 프론트 필터가 백엔드에 전달되지 않음
- [ ] **13. 타입 drift 수정**
  - `frontend/types/record.ts:23` section에 `byte_limit` 추가
  - 추후 OpenAPI 타입 자동 생성으로 전환 (P3)
- [ ] **14. UX 누락**
  - `frontend/components/ApprovalTable.tsx:55` `isError` 처리 추가
  - `useReject()`를 버튼/다이얼로그에 연결
- [ ] **15. XSS 강화**
  - `frontend/components/GuidelinesPanel.tsx:34` `dangerouslySetInnerHTML` → DOMPurify 또는 React renderer
- [ ] **16. Problem+JSON 완성**
  - 모든 `HTTPException` detail에 `title` 포함
  - `JSONResponse(media_type="application/problem+json")` 적용
- [ ] **17. 시간대 정리**
  - `datetime.utcnow` → `datetime.now(timezone.utc)` 일괄 교체
  - `backend/app/models/record.py:88` 포함
- [ ] **18. 상태 무결성**
  - `Record.status` / `Review.status` / `decision` / `role` CHECK constraint 마이그레이션
- [ ] **19. 리뷰 동시성**
  - `reviews.decide_step`에 `with_for_update()` 적용

---

## 🛠 P3. 운영 품질 (Sprint C)

회귀 차단과 배포 안전성.

- [ ] **20. CI 구성**
  - `.github/workflows/saengibu-ci.yml` 신설
  - backend lint/test + frontend typecheck + `make validate-jsonl` 연동
  - path filter로 앱 단위 실행
- [ ] **21. Prod Dockerfile**
  - `backend/Dockerfile:21` `-e .[dev]` 제거한 prod 스테이지 분리
  - multi-stage로 dev/prod 의존성 분리
- [ ] **22. OpenAPI 타입 자동 생성**
  - 백엔드 스키마 → 프론트 타입 동기화 파이프라인
  - `types/record.ts` 등 수동 타입 드리프트 방지
- [ ] **23. 프론트 테스트 추가**
  - vitest 단위 테스트 (`frontend/package.json:11` 스크립트는 있으나 테스트 파일 0개)
  - Playwright E2E: OAuth → 초안 → 1검 → 결재 골든 패스
- [ ] **24. Bootstrap admin / 초대 플로우**
  - `docs/LOCAL_SETUP.md:219-226` 의 수동 SQL `UPDATE users` 제거
  - 최초 관리자 부트스트랩 스크립트 + 초대 API
- [ ] **25. 모바일 레이아웃**
  - `frontend/components/Sidebar.tsx:45` `w-[260px]` 고정 → md 이하 drawer 전환

---

## 📚 P4. 데이터 정본화 (Sprint D)

운영 투입 전에 seed 출처 감사.

- [ ] **26. 원문 manifest 채우기**
  - `data/raw/manifest.json:5` `files[]` · `sha256` · `retrieved_at` 실제 값 기입
- [ ] **27. 시드 확장 & 정본 검증**
  - 현재: middle_math 11건 / 국어 8건 / 영어 6건 / 과학 6건 → 전 성취기준 커버
  - 모든 source의 `"임시 시드"` 주석 제거, 정본 검증 완료
- [ ] **28. PII 컬럼 암호화**
  - `backend/app/models/student.py:23` `name`, `birth_date` 평문 → pgcrypto 또는 KMS 적용

---

## 📝 P5. 문서 정비 (상시)

Drift를 방치하면 설계가 거짓말이 된다.

- [ ] **29. `docs/API.md` 개정**
  - Bearer/password 기반 서술 → Google ID Token + httpOnly cookie 세션 기준으로 전면 개정
- [ ] **30. `docs/ARCHITECTURE.md` · `docs/ERD.md` 정리**
  - 미구현 컴포넌트 분리: pgvector / Celery / `violations` / `llm_audits` / `embeddings` / `similarity_matches` / `correction_logs` / `neis_copy_logs`
  - "현재 구현" vs "계획" 섹션으로 분리
- [ ] **31. `README.md` 갱신**
  - 라우터 목록에 `standards` 추가
  - RLS "후속 마이그레이션" 표기 최신화

---

## 📌 참고

- 원본 리뷰: `docs/ULTRAREVIEW_CODEX.md`
- 기존 개선계획: `docs/IMPROVEMENT_PLAN.md`, `docs/IMPROVEMENT_PLAN_ADDENDUM.md`
- 프론트-백엔드 통합 현황: `docs/BACKEND_FRONTEND_INTEGRATION.md`
