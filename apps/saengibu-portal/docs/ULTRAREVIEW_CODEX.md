**Executive Summary**
경로 기준: `/mnt/c/Users/sdm24/OneDrive/바탕 화면/03_개발프로젝트/anti2/apps/saengibu-portal`

1. 🟥 **Critical: 문서상 RLS와 실제 DB 격리가 불일치**  
   `docs/ERD.md:7`은 “모든 도메인 테이블 RLS 활성화”를 말하지만, Alembic에는 `ENABLE ROW LEVEL SECURITY`/`CREATE POLICY`가 없습니다. 현재는 앱 레벨 필터 의존입니다.

2. 🟥 **Critical: RBAC가 역할명만 보고 스코프를 거의 보지 않음**  
   `reviews.decide_step`은 `expected_role in user.roles`만 검증해 담임 학급, 교과 담당, 학년부장 스코프가 빠져 있습니다.

3. 🟥 **Critical: 대시보드 AI 교정 수가 학교 스코프로 필터링되지 않음**  
   `dashboard.py`의 `FeedbackReport` count에는 `Record.school_id == user.school_id` 조인이 없어 멀티 학교에서 집계 누출 위험이 있습니다.

4. 🟧 **High: `/records` 핵심 CRUD/초안 저장/제출 API가 문서와 프론트 계획에 있지만 실제 미구현**  
   `docs/API.md`는 `/records/{id}/draft`, `/records/{id}/reviews`를 명시하지만 라우터 include에는 `records.py`가 없습니다.

5. 🟧 **High: 프론트 작성 위저드는 데모 하드코딩이며 제출이 서버와 연결되지 않음**  
   학생, 성취기준, 피드백, 제출이 모두 클라이언트 상태/정적 배열 기반입니다.

6. 🟧 **High: OAuth 승인제는 기본 학교 `limit(1)` 귀속이라 멀티 테넌시/도메인 매핑에 취약**  
   신규 사용자가 이메일 도메인과 무관하게 첫 번째 학교로 들어갑니다.

7. 🟧 **High: 감사 해시체인 동시성 보호가 없음**  
   `write_audit()`이 마지막 로그를 읽고 새 hash를 쓰지만 advisory lock/row lock이 없어 동시 요청에서 체인이 갈라질 수 있습니다.

8. 🟨 **Medium: API 문서는 Bearer/password 기반인데 실제 구현은 Google ID Token + httpOnly cookie**  
   `docs/API.md`의 인증 규약과 실제 `lib/api.ts`/cookie 구현이 상충합니다.

9. 🟨 **Medium: 학생 개인정보 저장 암호화가 미구현**  
   모델 주석도 “실제 배포 시 컬럼 암호화”라고 남아 있고 `name`, `birth_date`가 평문 컬럼입니다.

10. 🟨 **Medium: 테스트는 단위 4개 축뿐이고 프론트/통합/RBAC/E2E가 없음**  
    `frontend/package.json`에는 `vitest` 스크립트가 있지만 테스트 파일은 0개였습니다.

**Critical & High 이슈 상세**

1. 🟥 **RLS가 문서와 실제 구현에서 불일치**
- 근거:
  - `docs/ERD.md:7`: `"모든 도메인 테이블에 school_id FK, RLS(Row-Level Security) 활성화."`
  - `backend/app/core/db.py:36-45`: `"SET LOCAL app.school_id = :sid"`만 수행합니다.
  - `README.md:107`: `"도메인 테이블 RLS 정책 활성화 (후속 마이그레이션)"`가 아직 미완료임을 인정합니다.
- 실제 코드 인용:
  ```py
  # backend/app/core/db.py:36-45
  async def set_tenant(session: AsyncSession, school_id: UUID | None) -> None:
      """Set row-level tenancy for this transaction (enforced by RLS)."""
      ...
      await session.execute(text("SET LOCAL app.school_id = :sid"), {"sid": str(school_id)})
  ```
- 영향: RLS가 없으면 라우터의 필터 누락 하나가 곧 테넌트 데이터 누출입니다. 실제로 `dashboard.py`에 누락이 존재합니다.
- 권장 수정: `00012_enable_rls.py` 추가, `records/students/users/audit_logs/...` 직접/간접 정책 생성, 테스트에서 타 학교 fixture로 접근 차단 검증.

2. 🟥 **RBAC 스코프 매칭 부재로 권한 우회 가능**
- 근거:
  - `docs/RBAC.md:7`: `"역할만으로는 부족. 자기 학급만, 자기 수업 반만"`
  - `backend/app/api/v1/reviews.py:157-162`: 역할명만 확인.
- 실제 코드 인용:
  ```py
  # backend/app/api/v1/reviews.py:157-162
  if step.expected_role not in user.roles and "admin" not in user.roles:
      raise HTTPException(
          status_code=403,
          detail={"type": "rbac.wrong_role", "title": "이 단계의 검토자가 아닙니다"},
      )
  ```
- 영향: 같은 학교의 `homeroom`, `subject_head`, `grade_head` 역할자는 자기 범위 밖 record step도 결재할 수 있습니다.
- 권장 수정: `TeacherAssignment`, `HomeroomAssignment`, `Enrollment/Class/Grade`, `SectionType.input_role`를 조합한 `require_record_scope(action)` 의존성 도입. `SELECT ... FOR UPDATE`와 함께 결재 전 검증.

3. 🟥 **대시보드 집계의 학교 필터 누락**
- 실제 코드 인용:
  ```py
  # backend/app/api/v1/dashboard.py:51-58
  ai_corr = await db.scalar(
      select(func.count())
      .select_from(FeedbackReport)
      .where(
          FeedbackReport.total_warnings > 0,
          FeedbackReport.created_at >= week_ago,
      )
  )
  ```
- 영향: RLS 미활성 상태에서는 모든 학교의 AI 경고 수가 합산됩니다. 숫자만이라도 학생 기록 품질/업무량 정보입니다.
- 권장 수정: `FeedbackReport -> RecordVersion -> Record` 조인 후 `Record.school_id == user.school_id` 조건 추가. 가능하면 `feedback_reports`도 RLS 간접 정책 적용.

4. 🟧 **핵심 Records API 미구현**
- 근거:
  - `docs/API.md:101`: `"POST /records/{id}/draft — 초안 저장"`
  - `docs/API.md:162`: `"POST /records/{id}/reviews"`
  - 실제 include:
    ```py
    # backend/app/api/__init__.py:13-20
    api_router.include_router(auth_v1.router)
    api_router.include_router(users_v1.router)
    api_router.include_router(reviews_v1.router)
    api_router.include_router(dashboard_v1.router)
    api_router.include_router(content_v1.router)
    api_router.include_router(standards_v1.router)
    ```
- 영향: 제품 핵심인 작성, 버전 저장, 피드백 생성, 1검 제출이 백엔드에 없습니다. 프론트 위저드가 실제 데이터를 만들 수 없습니다.
- 권장 수정: `/records` 라우터를 먼저 구현하고, 최소 `create`, `save_draft`, `submit_review`, `get_record`, `versions`를 트랜잭션 단위로 묶으십시오.

5. 🟧 **프론트 작성 위저드가 서버 계약과 분리된 데모**
- 실제 코드 인용:
  ```tsx
  // frontend/app/writer/new/subject/page.tsx:21-26
  const MATH_STANDARDS: Array<{ code: string; statement: string }> = [
    { code: "[9수01-01]", statement: "소인수분해의 뜻을 알고..." },
  ];

  // frontend/app/writer/new/subject/page.tsx:58-60
  const [targetStudent] = useState({ grade: 1, klass: 3, name: "홍**", no: "1030101" });
  const [subject] = useState("수학");
  ```
  ```tsx
  // frontend/app/writer/new/subject/page.tsx:311-317
  <Button variant="primary" disabled={!allChecked} className="mt-4 w-full">
    {allChecked ? "1검 제출하기" : "모든 항목을 확인해 주세요"}
  </Button>
  ```
- 영향: 제출 버튼에 mutation이 없고, 성취기준도 `useStandards()`가 아니라 정적 배열입니다. 데모와 운영 요구가 크게 갈라져 있습니다.
- 권장 수정: Step 1 학생/과목 API, Step 2 `useStandards`, Step 4 `POST /records/{id}/draft`, Step 6 `POST /records/{id}/reviews` 연결.

6. 🟧 **신규 OAuth 사용자의 학교 귀속이 `select(School).limit(1)`**
- 실제 코드 인용:
  ```py
  # backend/app/api/v1/auth.py:94-103
  if not user:
      # 첫 가입: pending 상태로 생성. 학교 매핑은 "기본 학교"에 귀속
      default_school = await db.scalar(select(School).limit(1))
      ...
      user = User(school_id=default_school.id, email=email, ...)
  ```
- 영향: 다학교 운영 또는 데이터가 꼬인 개발 DB에서 사용자가 잘못된 학교로 pending 생성됩니다.
- 권장 수정: `allowed_email_domains`를 `school_domains` 테이블로 정규화하거나, 초대 코드/NEIS school code 기반 가입으로 전환.

7. 🟧 **감사 해시체인 동시성 취약**
- 실제 코드 인용:
  ```py
  # backend/app/services/audit/logger.py:27-33
  last = await db.scalar(
      select(AuditLog)
      .where(AuditLog.school_id == school_id)
      .order_by(desc(AuditLog.id))
      .limit(1)
  )
  prev_hash = last.content_hash if last else None
  ```
- 영향: 두 요청이 같은 `prev_hash`를 보고 동시에 flush하면 체인 검증이 비결정적으로 깨집니다.
- 권장 수정: `pg_advisory_xact_lock(hash(school_id))` 또는 학교별 audit head row `FOR UPDATE` 사용. `order_by(desc(AuditLog.id))`보다 `created_at,id` 정책도 명시.

8. 🟧 **비밀/보안 기본값 fail-fast 부재**
- 실제 코드 인용:
  ```py
  # backend/app/core/config.py:22-24
  session_secret: str = Field(
      "change-me-to-a-long-random-secret-at-least-32-chars-for-jwt",
      min_length=32,
  )
  ```
  ```ini
  # backend/.env.example:20-22
  # 학교 이메일 도메인 화이트리스트 ... 비워두면 모든 도메인 허용
  ALLOWED_EMAIL_DOMAINS=
  ```
- 영향: 프로덕션에서 환경변수 누락 시 기본 JWT secret/전체 도메인 허용으로 뜰 수 있습니다.
- 권장 수정: `environment != development`일 때 기본 secret, 빈 `GOOGLE_CLIENT_ID`, 빈 `ALLOWED_EMAIL_DOMAINS`, `COOKIE_SECURE=false`면 startup fail.

**Medium 이슈**

| 영역 | 근거 코드 인용 | 판단 | 권장 |
|---|---|---|---|
| API 문서 drift | `docs/API.md:7` `"Authorization: Bearer <jwt>"` vs `frontend/lib/api.ts:37` `"credentials: \"include\""` | 문서가 실제 쿠키 세션과 다름 | API.md를 Google cookie 세션 기준으로 개정 |
| Problem+JSON 불완전 | `backend/app/main.py:90-99`가 `detail.get(...)` 가정 | `detail`이 dict면 OK지만 content-type `application/problem+json` 아님 | `media_type="application/problem+json"` |
| HTTPException title 누락 | `backend/app/api/v1/reviews.py:120` `detail={"type": "review.not_found"}` | 프론트 fallback 메시지 의존 | 모든 예외에 `title` 포함 |
| XSS 방어 취약한 패턴 | `GuidelinesPanel.tsx:34` `dangerouslySetInnerHTML` | 현재 escape는 하지만 DOMPurify 계획도 문서화됨 | DOMPurify 또는 React 노드 렌더러로 교체 |
| 학생 PII 평문 | `backend/app/models/student.py:23` `"name ... # 실제 배포 시 컬럼 암호화"` | 이름/생년월일 평문 저장 | pgcrypto/KMS 컬럼 암호화 설계 |
| 로그인 감사 PII | `auth.py:142` `metadata={"status": user.status, "email": email}` | 감사 로그에 이메일 저장 | 이메일 hash/마스킹 저장 |
| 에러에 이메일 노출 | `auth.py:81` `"허용되지 않는 도메인: {email}"` | 클라이언트/로그 노출 | 도메인만 노출 |
| N+1은 일부 개선 | `reviews.py:48-61` 조인으로 목록 구성 | 목록은 양호, 상세 API 없음 | 상세 구현 시 `selectinload`/joins 유지 |
| 동시 결재 race | `reviews.py:116-118` `select(Review)...` | `FOR UPDATE` 없음 | `with_for_update()` |
| 모델 제약 부족 | `models/record.py:64` `status: String(30)` | CHECK 없음 | 상태 enum/check constraint |
| 시간대 혼용 | `models/record.py:88` `default=datetime.utcnow` | timezone aware 컬럼에 naive | `datetime.now(timezone.utc)` |
| Frontend 오류 UX | `ApprovalTable.tsx:55` `const { data, isLoading }` | `isError` 처리 없음 | error state/toast |
| App Router 경계 | 대부분 페이지 `"use client"` | 서버 컴포넌트 이점 상실 | 데이터 조회 가능한 페이지는 서버/클라이언트 분리 |
| 모바일 레이아웃 | `Sidebar.tsx:45` `w-[260px]` 고정 | 모바일 drawer 없음 | md 이하 drawer |
| 타입 drift | `types/record.ts:23` section에 `byte_limit` 없음, 백엔드 `ApprovalItem.section.byte_limit` 존재 | 응답 필드 누락 | OpenAPI 타입 생성 |
| 테스트 부족 | `frontend/package.json:11` `"test": "vitest run"`이나 테스트 파일 0개 | 스크립트만 있음 | UI 단위/E2E 추가 |
| CI 없음 | `.github/workflows` 없음 | 회귀 차단 불가 | path filter CI |
| Docker prod 미흡 | `backend/Dockerfile:21` `-e .[dev]` | prod 이미지에 dev deps | prod extras 분리 |
| Compose secret 약함 | `docker-compose.dev.yml:7` `POSTGRES_PASSWORD: saengibu` | dev 한정 OK, prod 재사용 위험 | prod compose 분리 |
| 데이터 정본성 | `0008...py:16` `"임시 시드, 정본 검증 필요"` | seed 품질 미완 | 원문 manifest/sha256 채우기 |

**아키텍처 정합성**

- 모노레포 구조 자체는 `backend/`, `frontend/`, `schemas/`, `data/`, `docs/`가 분리되어 적절합니다. 다만 README 구조가 낡았습니다. `README.md:71`은 `api/v1`을 `"auth · users · reviews · dashboard · content"`까지만 말하고, 실제 include에는 standards도 있습니다.
- 프론트 ↔ 백엔드 매핑은 `docs/BACKEND_FRONTEND_INTEGRATION.md:239-254`에 실제 훅과 잘 맞는 편입니다. 단 `useApprovals(status?)`는 표에서 `status_filter`라고 되어 있고, 실제 `queries.ts:42-45`도 `?status=...`가 아니라 `?status=...`를 보냅니다. 백엔드 파라미터명은 `status_filter`입니다:
  ```py
  # backend/app/api/v1/reviews.py:39
  status_filter: str | None = None
  ```
  ```ts
  // frontend/lib/queries.ts:42
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  ```
  이건 실제 버그입니다. 프론트 필터가 백엔드에 전달되지 않습니다.

**보안 심각도 분류**

- Critical: RLS 미활성, RBAC 스코프 누락, 대시보드 테넌트 집계 누락.
- High: 기본 secret/domain fail-fast 부재, OAuth 신규 사용자 기본 학교 귀속, 감사체인 race, Records API 부재로 검증 없는 UI 흐름.
- Medium: 이메일/사유 감사 로그 저장, `dangerouslySetInnerHTML`, 학생 PII 평문, CORS/TrustedHost 설정이 `cors_origins_list`에 과도하게 의존.
- Low: CSP에 Google 때문에 `'unsafe-inline'` 존재, 로그 request_id context 부재, UI error boundary 없음.

**데이터 모델 & 스키마**

- `schemas/standard.schema.json:17`은 `"additionalProperties": false`로 엄격하고, `scripts/validate.py:71-73`에서 JSON Schema와 레벨 정합성을 검증합니다. 좋은 방향입니다.
- 모델은 성취수준 확장성이 있습니다:
  ```py
  # backend/app/models/standards.py:51-54
  levels: Mapped[list[AchievementLevel]] = relationship(
      "AchievementLevel", back_populates="standard", cascade="all, delete-orphan",
      order_by="AchievementLevel.order_index.desc()",
  )
  ```
- 하지만 데이터는 아직 표본 수준입니다. `middle_math.jsonl` 11건, 국어 8건, 영어 6건, 과학 6건뿐이며 모든 source가 `"임시 시드"`입니다.
- `data/raw/manifest.json:5`의 `"files": []` 때문에 원문 파일, sha256, retrieved_at이 비어 있습니다. 운영 seed로 쓰면 출처 감사가 약합니다.

**테스트**

- 백엔드 단위 테스트는 CP949, PII mask, CSRF rotation, FSM에 집중되어 있습니다. 예:
  ```py
  # backend/tests/unit/test_workflow_fsm.py:23-34
  assert next_status("draft", Event.SUBMIT) == Status.REVIEW_1
  assert next_status(from_status, Event.REJECT) == Status.DRAFT
  ```
- 하지만 API 통합 테스트, DB migration 테스트, RLS/RBAC matrix, OAuth flow, frontend test, Playwright E2E는 없습니다.
- `backend/tests/conftest.py:10`의 마커 설명은 `"Critical+Major 18건"`이라고 하지만 실제 테스트 범위는 4개 파일입니다.

**운영 준비도**

- `docker-compose.dev.yml`은 개발용으로 적절합니다. Postgres/Redis를 `127.0.0.1`에만 바인딩한 점은 좋습니다.
- `backend/Dockerfile`은 운영용으로는 미흡합니다. `backend/Dockerfile:21`:
  ```dockerfile
  RUN uv pip install --system -e .[dev]
  ```
  dev 의존성을 운영 이미지에 넣습니다.
- CI/CD는 현재 앱 경로 내 `.github/workflows`가 없습니다.
- `LOCAL_SETUP.md`는 꽤 재현 가능하지만, 관리자 승인을 DB 수동 UPDATE로 안내합니다. `LOCAL_SETUP.md:219-226`:
  ```sql
  UPDATE users SET status = 'active' WHERE email = '본인구글이메일@gmail.com';
  INSERT INTO role_assignments ...
  ```
  운영 전에는 bootstrap admin/초대 플로우가 필요합니다.

**문서 간 모순**

- `docs/API.md`는 password/Bearer auth를 말하지만 실제는 Google cookie입니다.
- `docs/ARCHITECTURE.md:94-97`은 pgvector, Redis, Celery, AI Pipeline을 컨테이너 책임으로 명시하지만 실제 서비스에는 `backend/app/services/ai/`, Celery worker가 없습니다.
- `docs/ERD.md:24-28`은 `violations`, `llm_audits`, `embeddings`, `similarity_matches`, `correction_logs`, `neis_copy_logs`를 말하지만 모델/마이그레이션에는 없습니다.
- `docs/IMPROVEMENT_PLAN_ADDENDUM.md:71-74`가 RLS/RBAC/테스트를 후속으로 명시해 현재 구현의 공백을 정확히 반영합니다.

**Quick Wins: 1일 내 개선 20선**

1. `frontend/lib/queries.ts`의 approvals query를 `?status_filter=`로 수정.
2. `dashboard.py`의 `ai_corr`에 `Record` 조인과 `school_id` 필터 추가.
3. `reviews.decide_step`에 `with_for_update()` 적용.
4. `environment != development`에서 기본 `SESSION_SECRET` 차단.
5. 프로덕션에서 빈 `ALLOWED_EMAIL_DOMAINS` 차단.
6. `auth.domain_forbidden` detail에서 전체 email 제거.
7. 감사 metadata의 email/reason을 hash 또는 길이 제한/마스킹.
8. 모든 `HTTPException` detail에 `title` 추가.
9. `JSONResponse(media_type="application/problem+json")` 적용.
10. `Record.status`, `Review.status`, `decision`, `role` CHECK constraint 추가 migration.
11. `datetime.utcnow`를 timezone-aware default로 교체.
12. `ApprovalItem.section` 프론트 타입에 `byte_limit` 추가.
13. `ApprovalTable`에 `isError` UI 추가.
14. `useReject()`를 버튼/다이얼로그에 연결.
15. `dangerouslySetInnerHTML`을 DOMPurify 또는 React renderer로 교체.
16. `backend/Dockerfile`에서 `[dev]` 제거한 prod stage 추가.
17. `.github/workflows/saengibu-ci.yml` 추가: backend lint/test, frontend typecheck.
18. `make validate-jsonl`을 CI에 연결.
19. `data/raw/manifest.json`에 실제 원문 파일 metadata 채우기.
20. `README.md` API/구조 섹션을 현재 라우터 기준으로 갱신.

**전략적 권장: 다음 스프린트 로드맵**

1. **Sprint A: 보안 기반 완성**  
   RLS migration, RBAC scope guard, dashboard 누출 수정, audit advisory lock, secret fail-fast, API 통합 테스트.

2. **Sprint B: Records 핵심 워크플로우**  
   `/records` CRUD, draft versioning, byte/금지어 deterministic feedback, submit review endpoint, 프론트 위저드 서버 연결.

3. **Sprint C: 운영 품질**  
   OpenAPI 타입 자동 생성, frontend tests, Playwright E2E, CI coverage gate, prod Dockerfile, bootstrap admin/초대 플로우.

4. **Sprint D: 데이터 정본화**  
   성취기준 원문 manifest/sha256, seed coverage report, 출처 감사 필드 API 노출, 임시 시드 제거.

**칭찬할 점**

- `httpOnly` 세션 쿠키와 JS-readable CSRF 이중 제출 구조는 방향이 좋습니다. `cookies.py:18-30`에서 세션은 `httponly=True`, CSRF는 `httponly=False`로 역할이 분리되어 있습니다.
- `main.py`의 보안 헤더와 dev-only OpenAPI 조건은 기본 보안 자세가 좋습니다.
- 성취기준 JSON Schema와 `scripts/validate.py`는 데이터 품질 자동화의 좋은 출발점입니다.
- `reviews.assigned_to_me`는 목록 조회에서 필요한 테이블을 조인해 N+1을 피하려는 의도가 보입니다.
- `cp949_counter.py`는 NEIS byte/CRLF/CP949 비호환 문자를 별도 처리해 도메인 요구를 잘 반영했습니다.