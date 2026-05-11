# ERD — saengibu-portal

> PostgreSQL 16 + pgvector 0.7 기준. 모든 테이블 `created_at`/`updated_at` timestamptz 기본.

## 0. 설계 원칙

1. **학교 단위 테넌시.** 모든 도메인 테이블에 `school_id` FK, RLS(Row-Level Security) 활성화.
2. **영역(section) 단위 기록.** NEIS 화면 구조(9개 영역)와 1:1 매핑.
3. **이벤트 소싱.** `records`는 논리 키, `record_versions`가 append-only 이력.
4. **소프트 삭제 금지.** 정정은 새 버전 + `correction_log`로 추적.
5. **임베딩은 별도 테이블.** 크기·갱신 주기가 달라 분리.

---

## 1. 엔티티 개요 (8개 도메인)

| 도메인 | 주요 테이블 |
|---|---|
| **학교·조직** | `schools`, `academic_years`, `grades`, `classes`, `departments`, `subjects` |
| **사용자·권한** | `users`, `user_approvals`, `role_assignments`, `teacher_assignments` |
| **학생** | `students`, `enrollments`, `homeroom_assignments` |
| **기록** | `records`, `record_versions`, `section_types` |
| **검토** | `reviews`, `review_steps`, `review_comments` |
| **AI 피드백** | `feedback_reports`, `violations`, `llm_audits` |
| **유사도·임베딩** | `embeddings`, `similarity_matches`, `minhash_index` |
| **활동 공유** | `activity_plans`, `activity_plan_shares`, `activity_links` |
| **정정·NEIS** | `correction_logs`, `neis_copy_logs` |
| **감사·메타** | `audit_logs`, `banned_dict_entries`, `banned_whitelist` |

---

## 2. 학교·조직

```sql
CREATE TABLE schools (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    neis_code       varchar(20) UNIQUE NOT NULL,
    name            varchar(100) NOT NULL,
    type            varchar(20) NOT NULL CHECK (type IN ('elementary','middle','high','special')),
    principal_name  varchar(50),
    address         varchar(300),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE academic_years (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id   uuid NOT NULL REFERENCES schools(id) ON DELETE RESTRICT,
    year        smallint NOT NULL,      -- 2026
    start_date  date NOT NULL,
    end_date    date NOT NULL,
    is_active   boolean NOT NULL DEFAULT false,
    UNIQUE (school_id, year)
);

CREATE TABLE grades (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    year_id     uuid NOT NULL REFERENCES academic_years(id),
    grade_num   smallint NOT NULL,      -- 1, 2, 3
    UNIQUE (year_id, grade_num)
);

CREATE TABLE classes (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    grade_id    uuid NOT NULL REFERENCES grades(id),
    class_num   smallint NOT NULL,      -- 1, 2, ...
    UNIQUE (grade_id, class_num)
);

CREATE TABLE departments (                  -- 부서 (교무부, 학년부, 교과부)
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id   uuid NOT NULL REFERENCES schools(id),
    type        varchar(30) NOT NULL CHECK (type IN ('academic','grade','subject','other')),
    name        varchar(100) NOT NULL,
    parent_id   uuid REFERENCES departments(id)
);

CREATE TABLE subjects (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id   uuid NOT NULL REFERENCES schools(id),
    code        varchar(20) NOT NULL,   -- 국어, 수학 ...
    name        varchar(50) NOT NULL,
    department_id uuid REFERENCES departments(id),
    UNIQUE (school_id, code)
);
```

---

## 3. 사용자·권한

```sql
CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id     uuid NOT NULL REFERENCES schools(id),
    email         citext NOT NULL,
    password_hash varchar(255) NOT NULL,
    name          varchar(50) NOT NULL,
    employee_no   varchar(20),           -- 교직원번호
    phone         varchar(20),
    status        varchar(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','active','suspended','deleted')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    last_login_at timestamptz,
    UNIQUE (school_id, email)
);

CREATE TABLE user_approvals (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id),
    approver_id uuid REFERENCES users(id),
    approved_at timestamptz,
    rejected_at timestamptz,
    reason      text
);

CREATE TABLE role_assignments (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id),
    role        varchar(30) NOT NULL
                CHECK (role IN ('principal','vice_principal','academic_head',
                                'grade_head','subject_head','homeroom',
                                'subject_teacher','club_advisor','admin')),
    scope_type  varchar(20),              -- 'school'|'grade'|'class'|'subject'|'department'
    scope_id    uuid,                     -- polymorphic
    year_id     uuid REFERENCES academic_years(id),
    started_at  timestamptz NOT NULL DEFAULT now(),
    ended_at    timestamptz
);

CREATE INDEX idx_role_active ON role_assignments (user_id) WHERE ended_at IS NULL;

-- 교과 교사가 어떤 반에서 어떤 과목을 가르치는가
CREATE TABLE teacher_assignments (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id),
    class_id    uuid NOT NULL REFERENCES classes(id),
    subject_id  uuid NOT NULL REFERENCES subjects(id),
    year_id     uuid NOT NULL REFERENCES academic_years(id),
    UNIQUE (user_id, class_id, subject_id, year_id)
);
```

---

## 4. 학생

```sql
CREATE TABLE students (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id   uuid NOT NULL REFERENCES schools(id),
    student_no  varchar(20) NOT NULL,       -- 학번 (학교 내 고유)
    name        varchar(50) NOT NULL,       -- **암호화 저장 권장**
    gender      varchar(10),
    birth_date  date,
    UNIQUE (school_id, student_no)
);

CREATE TABLE enrollments (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id  uuid NOT NULL REFERENCES students(id),
    class_id    uuid NOT NULL REFERENCES classes(id),
    year_id     uuid NOT NULL REFERENCES academic_years(id),
    started_at  date NOT NULL,
    ended_at    date,
    status      varchar(20) NOT NULL DEFAULT 'active'
                CHECK (status IN ('active','transferred_in','transferred_out',
                                  'leave','graduated','dropped')),
    UNIQUE (student_id, year_id)
);

CREATE TABLE homeroom_assignments (         -- 담임 지정
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id    uuid NOT NULL REFERENCES classes(id),
    user_id     uuid NOT NULL REFERENCES users(id),
    year_id     uuid NOT NULL REFERENCES academic_years(id),
    started_at  date NOT NULL,
    ended_at    date,
    UNIQUE (class_id, year_id, started_at)
);
```

---

## 5. 기록 (이벤트 소싱)

### 5.1 section_types (마스터)

```sql
CREATE TABLE section_types (
    id              serial PRIMARY KEY,
    code            varchar(30) UNIQUE NOT NULL,  -- 'haengjongjeui','chang_jayul',...
    name            varchar(100) NOT NULL,
    neis_area       varchar(30) NOT NULL,          -- NEIS 대분류
    byte_limit      integer NOT NULL,              -- CP949 Byte 기준
    byte_limit_basis varchar(20) NOT NULL          -- 'year'|'subject'|'record'
                    CHECK (byte_limit_basis IN ('year','subject','record','semester')),
    input_role      varchar(30) NOT NULL,          -- 'homeroom'|'subject_teacher'|'club_advisor'
    style_rule_set  varchar(30) NOT NULL DEFAULT 'nouning_end',
    neis_prefix_rule jsonb,                        -- NEIS 복사 시 접두사 규칙
                                                    -- 예: chang_dongari → {"type":"choice","options":["(자율동아리)","(청소년단체)","(학교스포츠클럽)"]}
                                                    -- 예: chang_bongsa → {"type":"choice","options":["(학교)","(개인)"]}
    retention_policy varchar(30) NOT NULL DEFAULT 'permanent'
                    CHECK (retention_policy IN ('permanent','post_grad_2y','post_grad_4y',
                                                'immediate_on_graduation','hakpok_variable')),
    updated_in_2026 boolean NOT NULL DEFAULT false
);

-- 시드 (훈령 제7~16조의2 기준, Byte = 한글기준 글자수 × 3)
INSERT INTO section_types (code, name, neis_area, byte_limit, byte_limit_basis, input_role, updated_in_2026) VALUES
  ('injeok_teuggi',    '인적·학적 특기사항',       '인적학적',      1500, 'year',    'homeroom',       false),
  ('chulgyeol_teuggi', '출결 특기사항',             '출결',          1500, 'year',    'homeroom',       true),
  ('susang',           '수상경력',                  '수상',          300,  'record',  'homeroom',       false),
  ('hakpok_jochi',     '학교폭력 조치상황',         '학교폭력',      500,  'record',  'homeroom',       false),
  ('chang_jayul',      '자율·자치활동',             '창의적체험',    1500, 'year',    'homeroom',       true),
  ('chang_dongari',    '동아리활동',                '창의적체험',    1500, 'year',    'club_advisor',   true),
  ('chang_jinro',      '진로활동',                  '창의적체험',    1500, 'year',    'homeroom',       true),
  ('chang_bongsa',     '봉사활동실적 활동내용',      '창의적체험',    150,  'record',  'homeroom',       true),
  ('ilsangsaenghwal',  '일상생활 활동상황',          '일상생활',      3000, 'year',    'subject_teacher',false),
  ('jayuhakgi',        '자유학기활동',              '자유학기',      3000, 'year',    'subject_teacher',false),
  ('setuk_subject',    '과목별 세부능력 및 특기사항','교과학습',      1500, 'subject', 'subject_teacher',false),
  ('setuk_individual', '개인별 세부능력 및 특기사항','교과학습',      1500, 'year',    'homeroom',       false),
  ('dokseo_common',    '독서활동 공통',             '독서',          1500, 'year',    'homeroom',       true),
  ('dokseo_subject',   '독서활동 과목별',           '독서',          750,  'subject', 'subject_teacher',true),
  ('haengjongjeui',    '행동특성 및 종합의견',       '행종의',        900,  'year',    'homeroom',       true);

-- byte_limit은 CP949/NEIS 실제 상한 (한글 1자=3B 기준으로 환산)
-- 행종의: 300자 × 3B = 900B
-- 창체 자율/동아리/진로: 500자 × 3B = 1,500B
-- 봉사 활동내용: 50자 × 3B = 150B (실적별)
-- 자유학기 각 영역: 1,000자 × 3B = 3,000B
-- 세특: 500자 × 3B = 1,500B
-- 수상명: 100자 × 3B = 300B
```

### 5.2 records

```sql
CREATE TABLE records (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       uuid NOT NULL REFERENCES schools(id),
    student_id      uuid NOT NULL REFERENCES students(id),
    year_id         uuid NOT NULL REFERENCES academic_years(id),
    section_type_id integer NOT NULL REFERENCES section_types(id),
    subject_id      uuid REFERENCES subjects(id),   -- 세특·독서에서만
    author_id       uuid NOT NULL REFERENCES users(id),
    status          varchar(30) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','review_1','review_2','review_3',
                                      'approved','neis_copied',
                                      'correction_pending')),
    current_version uuid,                            -- 순환 FK, DEFERRABLE (아래)
    retention_until date,                            -- 학폭 조치 등 삭제 예정일
    retention_reason varchar(50),                    -- 'post_grad_2y'|'post_grad_4y'|'permanent'
    neis_prefix     varchar(50),                     -- 실제 선택된 접두사 (동아리·봉사)
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (student_id, year_id, section_type_id, subject_id)
);

CREATE INDEX idx_records_status ON records (status);
CREATE INDEX idx_records_author ON records (author_id, status);
CREATE INDEX idx_records_retention ON records (retention_until) WHERE retention_until IS NOT NULL;

CREATE TABLE record_versions (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id   uuid NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    version_no  integer NOT NULL,
    text        text NOT NULL,
    byte_count  integer NOT NULL,                   -- CP949 계산
    author_id   uuid NOT NULL REFERENCES users(id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (record_id, version_no)
);

CREATE INDEX idx_versions_record ON record_versions (record_id, version_no DESC);

-- 순환 FK는 DEFERRABLE INITIALLY DEFERRED로 선언 → 트랜잭션 내 양방향 insert 허용
ALTER TABLE records
  ADD CONSTRAINT fk_records_current_version
  FOREIGN KEY (current_version) REFERENCES record_versions(id)
  DEFERRABLE INITIALLY DEFERRED;
```

---

## 6. 검토 (1/2/3검)

```sql
CREATE TABLE reviews (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       uuid NOT NULL REFERENCES records(id),
    version_id      uuid NOT NULL REFERENCES record_versions(id),
    requested_by    uuid NOT NULL REFERENCES users(id),
    status          varchar(20) NOT NULL DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress','approved','rejected','cancelled')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    closed_at       timestamptz
);

CREATE TABLE review_steps (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id       uuid NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    step_no         smallint NOT NULL CHECK (step_no IN (1,2,3)),
    reviewer_id     uuid REFERENCES users(id),
    expected_role   varchar(30) NOT NULL,           -- 'homeroom'|'grade_head'|...
    decision        varchar(20)
                    CHECK (decision IN ('approved','rejected','pending')),
    decided_at      timestamptz,
    UNIQUE (review_id, step_no)
);

CREATE TABLE review_comments (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    step_id     uuid NOT NULL REFERENCES review_steps(id) ON DELETE CASCADE,
    author_id   uuid NOT NULL REFERENCES users(id),
    body        text NOT NULL,
    span_start  integer,                            -- 본문 내 위치(선택)
    span_end    integer,
    created_at  timestamptz NOT NULL DEFAULT now()
);
```

---

## 7. AI 피드백

```sql
CREATE TABLE feedback_reports (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      uuid NOT NULL REFERENCES record_versions(id),
    stage_byte      jsonb,                          -- {byte_count, limit, over}
    stage_banned    jsonb,                          -- {matches: [...]}
    stage_style     jsonb,
    stage_repeat    jsonb,                          -- {similar: [...]}
    stage_llm       jsonb,                          -- {violations: [...], severity}
    stage_checklist jsonb,
    total_violations integer NOT NULL DEFAULT 0,
    total_warnings   integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE violations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       uuid NOT NULL REFERENCES feedback_reports(id) ON DELETE CASCADE,
    stage           varchar(20) NOT NULL,           -- 'byte'|'banned'|'style'|'repeat'|'llm'
    severity        varchar(10) NOT NULL CHECK (severity IN ('block','warn','info')),
    rule_code       varchar(50) NOT NULL,
    span_start      integer,
    span_end        integer,
    message         text NOT NULL,
    suggestion      text,
    reference       varchar(100)                    -- '훈령 제555호 제16조'
);

CREATE INDEX idx_violations_report ON violations (report_id, severity);

CREATE TABLE llm_audits (                           -- 외부 LLM 호출 로그
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      uuid NOT NULL REFERENCES record_versions(id),
    provider        varchar(30) NOT NULL,           -- 'anthropic'|'openai'
    model           varchar(100) NOT NULL,
    prompt_masked   text NOT NULL,
    response_raw    text NOT NULL,
    tokens_input    integer,
    tokens_output   integer,
    latency_ms      integer,
    created_at      timestamptz NOT NULL DEFAULT now()
);
```

---

## 8. 유사도·임베딩

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id  uuid NOT NULL REFERENCES record_versions(id) UNIQUE,
    model       varchar(100) NOT NULL,              -- 'jhgan/ko-sroberta-multitask'
    vec         vector(768) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- HNSW 인덱스 (실시간 top-k)
CREATE INDEX idx_embeddings_hnsw ON embeddings USING hnsw (vec vector_cosine_ops);

CREATE TABLE similarity_matches (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version  uuid NOT NULL REFERENCES record_versions(id),
    target_version  uuid NOT NULL REFERENCES record_versions(id),
    cosine          real NOT NULL,
    minhash_jaccard real,
    match_type      varchar(30) NOT NULL            -- 'within_class'|'cross_year'|'cross_teacher'
                    CHECK (match_type IN ('within_class','cross_year','cross_teacher',
                                          'same_teacher_other_student')),
    flagged_at      timestamptz NOT NULL DEFAULT now(),
    reviewed_by     uuid REFERENCES users(id),
    review_status   varchar(20) DEFAULT 'pending'
);

CREATE TABLE minhash_index (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id  uuid NOT NULL REFERENCES record_versions(id) UNIQUE,
    signature   bytea NOT NULL                     -- 128 perm MinHash
);
```

---

## 9. 활동 계획 공유

```sql
CREATE TABLE activity_plans (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       uuid NOT NULL REFERENCES schools(id),
    owner_id        uuid NOT NULL REFERENCES users(id),
    scope_type      varchar(20) NOT NULL            -- 'school'|'grade'|'class'|'club'
                    CHECK (scope_type IN ('school','grade','class','club')),
    scope_id        uuid,
    section_type_id integer NOT NULL REFERENCES section_types(id),  -- 단일 소스 오브 트루스
    title           varchar(200) NOT NULL,
    body            text,
    start_date      date,
    end_date        date,
    is_template     boolean NOT NULL DEFAULT false
);

CREATE TABLE activity_plan_shares (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         uuid NOT NULL REFERENCES activity_plans(id) ON DELETE CASCADE,
    shared_with     uuid NOT NULL REFERENCES users(id),
    permission      varchar(20) NOT NULL DEFAULT 'read'
                    CHECK (permission IN ('read','fork'))
);

-- 기록이 어떤 활동 계획에 연계되는지 (중복 탐지 컨텍스트)
CREATE TABLE activity_links (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id   uuid NOT NULL REFERENCES records(id) ON DELETE CASCADE,
    plan_id     uuid NOT NULL REFERENCES activity_plans(id),
    UNIQUE (record_id, plan_id)
);
```

---

## 10. 정정·NEIS 복사

```sql
CREATE TABLE correction_logs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id       uuid NOT NULL REFERENCES records(id),
    from_version    uuid NOT NULL REFERENCES record_versions(id),
    to_version      uuid NOT NULL REFERENCES record_versions(id),
    requested_by    uuid NOT NULL REFERENCES users(id),
    principal_id    uuid REFERENCES users(id),      -- 학교장 승인자
    approved_at     timestamptz,
    reason          text NOT NULL
);

CREATE TABLE neis_copy_logs (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id  uuid NOT NULL REFERENCES record_versions(id),
    user_id     uuid NOT NULL REFERENCES users(id),
    copied_at   timestamptz NOT NULL DEFAULT now(),
    client_info jsonb                               -- UA·IP 해시
);

-- 훈령 제18조 자료제공(제3자 제공) 6가지 예외 처리
CREATE TABLE disclosure_requests (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       uuid NOT NULL REFERENCES schools(id),
    student_id      uuid NOT NULL REFERENCES students(id),
    requested_by    uuid NOT NULL REFERENCES users(id),
    purpose         varchar(30) NOT NULL
                    CHECK (purpose IN ('legal_order','advancement','employment',
                                       'statistics_research','principal_discretion',
                                       'self_request')),
    legal_basis     varchar(200) NOT NULL,          -- 법령 근거 인용
    recipient       varchar(200) NOT NULL,          -- 제공받는 자
    scope           jsonb NOT NULL,                 -- 제공 범위 (영역·기간)
    consent_document_ref varchar(500),              -- 학생·보호자 동의서 ref
    principal_approver uuid REFERENCES users(id),
    approved_at     timestamptz,
    disclosed_at    timestamptz,
    disclosure_format varchar(30),                  -- 'pdf'|'deidentified_csv'
    expires_at      date,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_disclosure_student ON disclosure_requests (student_id, disclosed_at DESC);
```

---

## 11. 감사·사전

```sql
CREATE TABLE audit_logs (
    id          bigserial PRIMARY KEY,
    school_id   uuid NOT NULL REFERENCES schools(id),
    user_id     uuid REFERENCES users(id),
    action      varchar(50) NOT NULL,               -- 'record.view'|'record.write'|'review.decide'
    resource_type varchar(30) NOT NULL,
    resource_id uuid,
    metadata    jsonb,
    ip          inet,
    user_agent  text,
    content_hash char(64) NOT NULL,                 -- SHA-256(canonical_json(이 행))
    prev_hash   char(64),                           -- 직전 행 content_hash → 해시 체인
    created_at  timestamptz NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);
-- 월 단위 파티션, 준영구 보관
-- UPDATE/DELETE 권한은 RLS + 역할로 차단
-- 일 1회 S3 Object Lock(WORM)으로 외부 백업, 체인 head 해시 별도 보관 → 변조 탐지

CREATE TABLE banned_dict_entries (
    id          serial PRIMARY KEY,
    category    varchar(30) NOT NULL,               -- 'exam','award','univ','parent_status',...
    pattern     text NOT NULL,                      -- regex
    severity    varchar(10) NOT NULL DEFAULT 'block',
    reference   varchar(100),                       -- 훈령 근거
    active      boolean NOT NULL DEFAULT true,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE banned_whitelist (                     -- 교육관련기관 예외
    id          serial PRIMARY KEY,
    name        varchar(200) NOT NULL,
    note        text
);
```

---

## 12. 인덱스·RLS 요약

```sql
-- 모든 도메인 테이블에 RLS. school_id가 직접 있는 테이블은 컬럼 기반,
-- 없는 테이블(record_versions·feedback_reports·violations·embeddings·similarity_matches·
-- llm_audits·minhash_index·review_* 등)은 상위 FK(records/reviews) JOIN 기반.

-- 직접 소유
DO $$ DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'schools','academic_years','grades','classes','departments','subjects',
    'users','user_approvals','role_assignments','teacher_assignments',
    'students','enrollments','homeroom_assignments',
    'records','activity_plans','correction_logs','neis_copy_logs',
    'disclosure_requests','audit_logs','banned_dict_entries','banned_whitelist'
  ] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format(
      'CREATE POLICY school_isolation ON %I USING (school_id = current_setting(''app.school_id'')::uuid)',
      t
    );
  END LOOP;
END $$;

-- 간접 소유 (예: record_versions)
CREATE POLICY school_isolation_via_record ON record_versions
  USING (EXISTS (
    SELECT 1 FROM records r
    WHERE r.id = record_versions.record_id
      AND r.school_id = current_setting('app.school_id')::uuid
  ));
-- feedback_reports, violations, embeddings, similarity_matches, llm_audits,
-- minhash_index, reviews, review_steps, review_comments, activity_links 에 동일 패턴 적용.

-- audit_logs는 UPDATE/DELETE 금지 정책
CREATE POLICY audit_no_mutation ON audit_logs FOR UPDATE USING (false);
CREATE POLICY audit_no_delete ON audit_logs FOR DELETE USING (false);

-- 애플리케이션은 트랜잭션 시작 시 항상:
--   SET LOCAL app.school_id = '<user.school_id>';
-- FastAPI 미들웨어가 강제.

-- 자주 쓰는 조회
CREATE INDEX idx_records_student_year ON records (student_id, year_id);
CREATE INDEX idx_reviews_status ON reviews (status) WHERE status = 'in_progress';
CREATE INDEX idx_feedback_version ON feedback_reports (version_id);
CREATE INDEX idx_similarity_source ON similarity_matches (source_version, cosine DESC);

-- 감사 로그 파티션
CREATE INDEX idx_audit_actor ON audit_logs (user_id, created_at DESC);
CREATE INDEX idx_audit_hash ON audit_logs (created_at, id);  -- 해시 체인 검증
```

---

## 13. 마이그레이션 전략

- Alembic 기반, `apps/saengibu-portal/backend/alembic/versions/`
- 초기 마이그레이션: `0001_baseline.py` — 위 전체 스키마
- 시드 마이그레이션: `0002_section_types_seed.py` — `section_types` 12개 + 교육관련기관 6개 화이트리스트
- 금지어 사전: `0003_banned_dict_seed.py` — 카테고리별 시드(별도 YAML에서 로드)
- 학교 초기 세팅: `0004_school_bootstrap.py` — 관리자 계정 1개, RLS 정책
