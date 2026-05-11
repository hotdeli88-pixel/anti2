# saengibu-portal 통합 개선안

작성일: 2026-04-14  
대상 프로젝트: `/mnt/c/Users/sdm24/OneDrive/바탕 화면/03_개발프로젝트/anti2/apps/saengibu-portal/`  
작성 기준: 기존 문서 `docs/ARCHITECTURE.md`, `docs/ERD.md`, `docs/API.md`, `docs/AI_PIPELINE.md`, `docs/FRONTEND.md`, `docs/AGENT_TEAM.md` 확인 완료  
외부 근거: 학교생활기록부 종합지원포털의 `학교생활기록 작성 및 관리지침 [시행 2026. 3. 1.] [교육부훈령 제555호, 2026. 2. 12.]` 확인 완료. 2026학년도 학교생활기록부 기재요령 PDF 게시 사실은 동일 포털 검색 결과로 확인했으나, PDF 본문 원문 라인 단위 확인은 추가 조사 필요.

## 1. 경쟁 포지셔닝 전략

하마룸은 교사가 과목, 성취기준, 활동 유형, 학생 특성을 빠르게 선택해 결과 문장을 받는 "생성기" 경험에 강점이 있다. `saengibu-portal`은 같은 속도감을 제공하되, 최종 포지션을 "생성"이 아니라 "훈령 준수형 작성·검토 포털"로 고정한다. 차별화는 3가지다.

첫째, 하마룸식 태그 선택 UX를 흡수하되 교사 초안 입력을 필수 단계로 둔다. 태그는 문장을 자동 완성하는 재료가 아니라 교사가 관찰 근거를 빠뜨리지 않도록 돕는 체크리스트다. 둘째, 1검·2검·3검 워크플로우, 감사 해시체인, RLS, 승인제 계정을 결합해 학교 내부 결재 체계에 맞춘다. 하마룸이 개인 작성 도구라면 본 프로젝트는 학교 단위 운영 시스템이다. 셋째, 훈령 제555호 제4조 제2항의 "학생에 대해 직접 관찰·평가한 내용" 원칙과 2026 기재요령의 생성형 AI 그대로 입력 금지 취지를 제품 핵심 엣지로 삼는다.

따라서 UI 용어는 `AI 생성`, `자동 작성`, `결과 생성`을 금지하고 `AI 피드백`, `관점 점검`, `초안 개선`, `기재요령 검토`로 통일한다. 버튼도 `생성하기`가 아니라 `관점 점검`, `초안 검토`, `위반 가능성 확인`으로 표기한다. LLM 출력은 완성 문장이 아니라 누락 관점, 과장 위험, 근거 부족, 문체 리스크, Byte 초과 가능성으로 제한한다.

구현 체크박스

- [ ] `docs/POSITIONING.md`에 금지 용어와 허용 용어 표 추가
- [ ] `frontend/lib/copy.ts`에 제품 카피 상수 추가
- [ ] `backend/app/services/ai/llm_stage.py` 시스템 프롬프트에 "완성 문장 제공 금지" 명시
- [ ] `frontend/components/editor/FeedbackSidePanel.tsx`에서 `AI 생성` 문자열 사용 금지 테스트 추가

## 2. UX 개선안: 탭·페이지 재설계

### 2.1 정보 구조

```text
[사이드바]
- 홈 (대시보드)
- 생기부 작성
    - 담임 (행종의/자율/진로/봉사/창체/일상생활)
    - 교과 (과목별 세특)
    - 독서·자유학기
    - 수상·출결·인적
- 검토 센터 (1검/2검/3검 큐)
- 라이브러리 (성취기준·활동 태그·예시문)
- 통계·대시보드
- 공지·가이드
- 설정
```

현재 `frontend/components/layout/Sidebar.tsx`의 메뉴는 `/dashboard`, `/records`, `/settings` 3개다. Sprint 1에서 사이드바를 위 구조로 교체한다. 라우트는 Next.js App Router 기준으로 다음처럼 고정한다.

```text
frontend/app/
├── dashboard/page.tsx
├── records/
│   ├── page.tsx
│   ├── homeroom/page.tsx
│   ├── subject/page.tsx
│   ├── subject/new/page.tsx
│   ├── [recordId]/edit/page.tsx
│   └── [recordId]/review/page.tsx
├── reviews/page.tsx
├── library/
│   ├── page.tsx
│   ├── standards/page.tsx
│   ├── tags/page.tsx
│   └── templates/page.tsx
├── notices/page.tsx
└── settings/page.tsx
```

### 2.2 페이지별 주요 컴포넌트

홈 대시보드(`/dashboard`)는 `ProgressSummaryCards`, `RecentDraftList`, `ReviewQueueWidget`, `FavoriteTemplateWidget`, `ComplianceAlertWidget`로 구성한다. 최근 작성 내역은 최근 14일 기준 20건을 노출하고, 즐겨찾기 템플릿은 사용 빈도 상위 8개를 노출한다.

생기부 작성(`/records`)은 `RecordSectionTabs`, `StudentSearchCombobox`, `RecordStatusMatrix`, `QuickStartPanel`로 구성한다. 담임 페이지는 행종의, 자율, 진로, 봉사, 창체, 일상생활을 영역 카드로 보여준다. 교과 페이지는 과목별 세특 전용 위저드로 진입한다.

검토 센터(`/reviews`)는 `ReviewStageTabs`, `ReviewQueueTable`, `ReviewDiffPreview`, `DecisionPanel`로 구성한다. 탭은 `1검`, `2검`, `3검`, `반려`, `승인 완료` 5개로 고정한다. 기존 `backend/app/services/workflow/fsm.py` 상태 전이를 그대로 사용한다.

라이브러리(`/library`)는 `StandardExplorer`, `TagLibraryManager`, `TemplateGallery`, `GuidelineReferencePanel`로 구성한다. 성취기준은 과목, 학교급, 학년군, 영역, 키워드로 필터링한다. 활동 태그와 학생 특성 태그는 관리자와 교과부장만 생성·수정할 수 있고 일반 교사는 개인 즐겨찾기만 가능하다.

공지·가이드(`/notices`)는 `GuidelineNoticeList`, `PolicyChangeTimeline`, `FaqSearch`로 구성한다. 2026 기재요령 변경사항은 별도 카테고리 `policy_2026`으로 저장한다.

설정(`/settings`)은 `ProfileSettings`, `SchoolYearSelector`, `SubjectAssignmentPanel`, `PrivacySettings`, `AdminGuardSettings`로 구성한다.

### 2.3 3-pane과 스텝 위저드 결합

하마룸의 장점은 선택 단계가 짧고 명확하다는 점이다. 기존 프로젝트의 3-pane 에디터는 검토와 수정에는 적합하지만 초안 시작에는 진입 장벽이 있다. 따라서 교과세특은 "상단 스텝 위저드 + 본문 3-pane"으로 결합한다.

초기 작성 흐름은 `/records/subject/new`에서 6단계 스텝 위저드로 시작한다. 1~4단계는 입력 정보 수집, 5단계는 피드백 확인, 6단계는 제출이다. 사용자가 4단계에서 교사 초안을 저장하면 서버가 `records`, `record_versions`, `feedback_reports`를 생성하고 `/records/{recordId}/edit`로 이동한다. 이후 화면은 좌측 `DraftEditorPane`, 중앙 또는 하단 `WizardContextPanel`, 우측 `FeedbackSidePanel`의 3-pane으로 유지한다.

이 결합 방식은 작성 시작에서는 하마룸식 클릭 UX를 제공하고, 검토·수정에서는 현재 프로젝트의 규정 검증형 에디터를 유지한다. 모바일에서는 우측 피드백 패널을 하단 드로어로 전환하고, 스텝 네비게이션은 상단 가로 스크롤이 아니라 `StepProgressSelect` 단일 컨트롤로 표시한다.

구현 체크박스

- [ ] `frontend/components/layout/Sidebar.tsx` 메뉴 IA 교체
- [ ] `frontend/app/records/subject/new/page.tsx` 생성
- [ ] `frontend/app/records/[recordId]/edit/page.tsx` 생성
- [ ] `frontend/components/wizard/WizardSteps.tsx` 생성
- [ ] `frontend/components/editor/FeedbackSidePanel.tsx` 생성
- [ ] `frontend/components/library/StandardExplorer.tsx` 생성

## 3. 에디터 상세 설계: 교과세특 기준

### 3.1 Step 1: 학생·과목·단원 선택

목표는 기록의 권위 키를 확정하는 것이다. 사용자는 학년도, 학급, 학생, 과목, 단원을 선택한다. 학생은 `students`와 `enrollments`, 과목은 `subjects`, 교과 배정은 `teacher_assignments`를 기준으로 필터링한다. 교과 교사는 본인이 배정된 반과 과목만 선택 가능하다.

```ts
export interface SubjectWizardStep1 {
  yearId: string;
  classId: string;
  studentId: string;
  subjectId: string;
  subjectCode: string;
  unitId: string | null;
  semester: 1 | 2 | null;
}
```

### 3.2 Step 2: 성취기준 선택

성취기준은 검색과 체크 선택을 함께 제공한다. 검색 필드는 코드, 본문, 키워드를 대상으로 한다. 기본 선택 권장 수는 1~3개다. 0개면 다음 단계로 이동할 수 없다. 4개 이상이면 UI는 `성취기준이 많아 문장이 산만해질 수 있음` 경고를 띄우되 차단하지 않는다.

```ts
export interface SelectedAchievementStandard {
  id: string;
  curriculumYear: 2022;
  schoolLevel: "elementary" | "middle" | "high";
  subjectCode: string;
  gradeBand: string;
  areaCode: string;
  standardCode: string;
  content: string;
  keywords: string[];
}

export interface SubjectWizardStep2 {
  selectedStandardIds: string[];
  searchQuery: string;
  areaFilter: string | null;
  selectedCount: number;
}
```

### 3.3 Step 3: 활동 태그·학생 특성 태그

태그는 3개 그룹으로 분리한다. 활동 유형은 2개 권장, 역할 수행은 1개 권장, 학생 특성은 2개 권장이다. 권장 수는 UI 가이드일 뿐 저장 차단 조건은 아니다. 단, 전체 태그 0개는 차단한다. 사용자는 `편집/키워드 등록` 버튼으로 개인 태그를 추가할 수 있다. 개인 태그는 `scope='personal'`, 교과 공용 태그는 `scope='subject'`, 학교 공용 태그는 `scope='school'`로 저장한다.

```ts
export type TagGroup = "activity_type" | "student_role" | "student_trait";
export type TagScope = "system" | "school" | "subject" | "personal";

export interface ActivityTag {
  id: string;
  schoolId: string | null;
  subjectId: string | null;
  group: TagGroup;
  label: string;
  description: string | null;
  scope: TagScope;
  sortOrder: number;
  isActive: boolean;
}

export interface SubjectWizardStep3 {
  activityTagIds: string[];
  roleTagIds: string[];
  traitTagIds: string[];
  customKeywords: string[];
}
```

### 3.4 Step 4: 교사 초안 입력 + 파일 업로드

교사 초안은 최소 80자 또는 240 CP949 Byte 이상이어야 저장 가능하다. 이유는 빈 에디터 또는 태그만으로 LLM을 호출하는 생성기 흐름을 차단하기 위해서다. 파일 업로드는 선택 사항이며, 파일당 10MB, 기록당 3개, 확장자는 `.hwp`, `.doc`, `.docx`, `.pdf`로 제한한다. 업로드 파일은 문장 생성 재료가 아니라 과제 수행 흔적을 요약·검증하는 근거 자료로만 사용한다.

```ts
export interface DraftInput {
  text: string;
  byteCountClient: number;
  minimumByteRequired: 240;
  uploadedFileIds: string[];
  teacherObservationConfirmed: boolean;
}

export interface UploadedFileClient {
  id: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
  scanStatus: "pending" | "clean" | "rejected" | "failed";
  extractStatus: "pending" | "done" | "failed" | "unsupported";
}
```

### 3.5 Step 5: AI 피드백

기존 `docs/AI_PIPELINE.md`의 6단계 파이프라인을 그대로 사용한다. Stage 1 Byte, Stage 2 금지어, Stage 3 문체, Stage 4 유사도, Stage 5 LLM 심층 피드백, Stage 6 체크리스트다. 여기서 LLM은 "문장 제안"을 반환하지 않는다. 반환 필드는 `missing_evidence`, `risk_flags`, `questions_for_teacher`, `rewrite_required_spans`로 제한한다.

```ts
export interface FeedbackReportView {
  reportId: string;
  versionId: string;
  byte: { count: number; limit: number; over: boolean };
  banned: FeedbackIssue[];
  style: FeedbackIssue[];
  similarity: SimilarityIssue[];
  llm: LlmFeedbackView | null;
  checklist: HumanChecklist;
  hasBlockingIssue: boolean;
}

export interface LlmFeedbackView {
  missingEvidence: string[];
  riskFlags: Array<{
    code: "fabrication_risk" | "exaggeration" | "generic_expression" | "policy_risk";
    message: string;
    spanStart: number | null;
    spanEnd: number | null;
    needsHumanRewrite: true;
  }>;
  questionsForTeacher: string[];
}
```

### 3.6 Step 6: 확정 → 1검 제출

제출 조건은 결정적으로 고정한다. `byte.over=false`, `banned`의 `severity='block'` 0건, `teacherObservationConfirmed=true`, `guidelinesReviewed=true`, `needsHumanRewrite=true` span 0건, 현재 버전 저장 완료 상태여야 한다. 조건을 통과하면 `POST /api/v1/records/{id}/reviews`를 호출해 `draft → review_1` 전이를 수행한다.

```ts
export interface SubmitGate {
  recordId: string;
  versionId: string;
  byteOk: boolean;
  noBlockViolation: boolean;
  noHumanRewriteRequired: boolean;
  teacherObservationConfirmed: boolean;
  guidelinesReviewed: boolean;
  submitEnabled: boolean;
}
```

구현 체크박스

- [ ] `frontend/types/subject-wizard.ts` 생성
- [ ] `frontend/components/wizard/SubjectSelector.tsx` 생성
- [ ] `frontend/components/wizard/StandardPicker.tsx` 생성
- [ ] `frontend/components/wizard/TagChipGroup.tsx` 생성
- [ ] `frontend/components/wizard/UploadZone.tsx` 생성
- [ ] `frontend/components/editor/ChecklistGate.tsx` 생성
- [ ] `backend/app/schemas/subject_wizard.py` 생성

## 4. 백엔드 스키마 추가

### 4.1 `achievement_standards`

성취기준은 학교별 데이터가 아니라 국가 교육과정 기준 데이터다. 다만 학교별 비활성화나 별칭 관리 가능성을 위해 `school_id`를 nullable로 둔다. 2022 개정 교육과정 원자료의 공식 CSV 또는 PDF 원문 매핑은 조사 필요다.

```sql
CREATE TABLE achievement_standards (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    curriculum_year smallint NOT NULL CHECK (curriculum_year IN (2022)),
    school_level varchar(20) NOT NULL CHECK (school_level IN ('elementary','middle','high')),
    subject_code varchar(30) NOT NULL,
    subject_name varchar(50) NOT NULL,
    grade_band varchar(20) NOT NULL,
    area_code varchar(50) NOT NULL,
    area_name varchar(100) NOT NULL,
    standard_code varchar(50) NOT NULL,
    content text NOT NULL,
    keywords text[] NOT NULL DEFAULT '{}',
    source_doc varchar(200) NOT NULL,
    source_page integer,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (curriculum_year, school_level, subject_code, standard_code)
);
CREATE INDEX idx_achievement_standards_search
ON achievement_standards USING gin (to_tsvector('simple', standard_code || ' ' || content));
```

### 4.2 `activity_tags`

```sql
CREATE TABLE activity_tags (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id uuid REFERENCES schools(id),
    subject_id uuid REFERENCES subjects(id),
    group_code varchar(30) NOT NULL CHECK (group_code IN ('activity_type','student_role')),
    label varchar(50) NOT NULL,
    description text,
    scope varchar(20) NOT NULL CHECK (scope IN ('system','school','subject','personal')),
    owner_user_id uuid REFERENCES users(id),
    sort_order integer NOT NULL DEFAULT 0,
    usage_count integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (school_id, subject_id, group_code, label, owner_user_id)
);
```

### 4.3 `student_traits`

```sql
CREATE TABLE student_traits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id uuid REFERENCES schools(id),
    subject_id uuid REFERENCES subjects(id),
    label varchar(50) NOT NULL,
    description text,
    scope varchar(20) NOT NULL CHECK (scope IN ('system','school','subject','personal')),
    owner_user_id uuid REFERENCES users(id),
    sort_order integer NOT NULL DEFAULT 0,
    usage_count integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
```

### 4.4 `favorite_templates`

즐겨찾기는 완성 문장 복붙 도구가 아니라 구조화된 작성 힌트 저장소다. 템플릿 본문에 `needs_human_rewrite=true`를 표시할 수 있도록 JSONB 메타를 둔다.

```sql
CREATE TABLE favorite_templates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id uuid NOT NULL REFERENCES schools(id),
    owner_user_id uuid NOT NULL REFERENCES users(id),
    section_type_id integer NOT NULL REFERENCES section_types(id),
    subject_id uuid REFERENCES subjects(id),
    title varchar(100) NOT NULL,
    template_body text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}',
    visibility varchar(20) NOT NULL DEFAULT 'private'
      CHECK (visibility IN ('private','department','school')),
    usage_count integer NOT NULL DEFAULT 0,
    last_used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
```

### 4.5 `uploaded_files`

파일은 DB에 바이너리 저장하지 않는다. 로컬 또는 S3 호환 스토리지의 object key만 저장한다. 업로드 후 `pending → scanning → clean/rejected → extracted` 상태를 거친다.

```sql
CREATE TABLE uploaded_files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id uuid NOT NULL REFERENCES schools(id),
    record_id uuid REFERENCES records(id) ON DELETE CASCADE,
    uploader_id uuid NOT NULL REFERENCES users(id),
    original_filename varchar(255) NOT NULL,
    stored_object_key varchar(500) NOT NULL,
    content_type varchar(100) NOT NULL,
    detected_mime varchar(100),
    extension varchar(10) NOT NULL,
    size_bytes integer NOT NULL CHECK (size_bytes <= 10485760),
    sha256 char(64) NOT NULL,
    scan_status varchar(20) NOT NULL DEFAULT 'pending'
      CHECK (scan_status IN ('pending','scanning','clean','rejected','failed')),
    extract_status varchar(20) NOT NULL DEFAULT 'pending'
      CHECK (extract_status IN ('pending','done','failed','unsupported')),
    extracted_text text,
    rejection_reason text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX idx_uploaded_files_sha_school ON uploaded_files (school_id, sha256);
```

파일 검증 흐름은 8단계로 고정한다. 1단계 확장자 allowlist 검사, 2단계 파일 크기 검사, 3단계 magic bytes 검사, 4단계 MIME 불일치 차단, 5단계 SHA-256 계산, 6단계 ClamAV 또는 동등한 백신 스캔, 7단계 PDF/HWP/DOC 텍스트 추출, 8단계 추출 텍스트 PII 마스킹 후 요약 지표 저장이다. `.hwp` 파서는 조사 필요이며, MVP에서는 `.pdf`, `.docx` 추출을 먼저 지원하고 `.hwp`는 업로드 보관 + 수동 확인으로 제한한다.

### 4.6 API 엔드포인트 추가 목록

```text
GET    /api/v1/standards
GET    /api/v1/standards/{standard_id}
POST   /api/v1/standards/import
PATCH  /api/v1/standards/{standard_id}/active
GET    /api/v1/tags/activity
POST   /api/v1/tags/activity
PATCH  /api/v1/tags/activity/{tag_id}
DELETE /api/v1/tags/activity/{tag_id}
GET    /api/v1/tags/traits
POST   /api/v1/tags/traits
PATCH  /api/v1/tags/traits/{trait_id}
DELETE /api/v1/tags/traits/{trait_id}
POST   /api/v1/records/subject-wizard
GET    /api/v1/records/{record_id}/wizard-context
POST   /api/v1/records/{record_id}/suggestion-context
POST   /api/v1/records/{record_id}/uploads
GET    /api/v1/records/{record_id}/uploads
DELETE /api/v1/uploads/{file_id}
GET    /api/v1/uploads/{file_id}/analysis
GET    /api/v1/favorite-templates
POST   /api/v1/favorite-templates
PATCH  /api/v1/favorite-templates/{template_id}
DELETE /api/v1/favorite-templates/{template_id}
POST   /api/v1/favorite-templates/{template_id}/use
GET    /api/v1/library/examples
POST   /api/v1/library/examples
```

구현 체크박스

- [ ] `backend/alembic/versions/0004_achievement_standards.py` 생성
- [ ] `backend/alembic/versions/0005_tags_traits.py` 생성
- [ ] `backend/alembic/versions/0006_favorites_uploads.py` 생성
- [ ] `backend/app/models/library.py` 생성
- [ ] `backend/app/models/upload.py` 생성
- [ ] `backend/app/api/v1/standards.py` 생성
- [ ] `backend/app/api/v1/tags.py` 생성
- [ ] `backend/app/api/v1/uploads.py` 생성
- [ ] `backend/app/api/v1/favorites.py` 생성

## 5. 훈령 위반 없이 "생성기" 효과를 내는 기법

근거는 두 층으로 둔다. 공식 훈령 제555호 제4조 제2항은 사용자가 학생에 대해 직접 관찰·평가한 내용을 근거로 자료를 입력해야 한다고 규정한다. 제15조 제6항은 중·고등학교 세부능력 및 특기사항에 과목별 성취기준에 따른 성취수준의 특성과 학습활동 참여도 등을 문장으로 입력한다고 규정한다. 2026 기재요령의 생성형 AI 관련 상세 문구는 공식 PDF 원문 확인이 추가 필요하지만, 사용자 제공 조건과 공개 보도 기준으로 "생성형 AI가 생성한 자료를 그대로 입력하는 행위 방지"를 제품 요구사항으로 채택한다.

첫째, 태그 조합은 `관점 후보`만 만든다. 예를 들어 `문제풀이`, `창의적 사고`, `모둠장`, `논리적 사고력`을 선택하면 LLM은 "풀이 과정의 오류 수정 사례가 있는지 확인", "모둠 내 설명 역할이 실제 관찰되었는지 확인" 같은 질문을 반환한다. 완성 문장, 문장 일부, 바꿔 쓸 표현은 반환하지 않는다.

둘째, 교사 초안 입력을 강제한다. `POST /api/v1/records/{id}/draft`는 본문 80자 미만 또는 240 CP949 Byte 미만이면 `422 draft_too_short`를 반환한다. 파일만 업로드하거나 태그만 선택한 상태에서는 피드백 호출이 불가능하다.

셋째, AI 제안이 포함된 문장에는 `needs_human_rewrite=true`를 저장한다. 사용자가 LLM 질문을 바탕으로 문장을 붙여 넣거나 "AI 문장 반영" 버튼을 누르는 기능은 만들지 않는다. 대신 피드백 항목을 클릭하면 에디터 해당 위치에 `교사 재작성 필요` 마크만 남긴다. 제출 시 이 플래그가 남아 있으면 `1검 제출` 버튼은 비활성화된다.

넷째, UI 카피는 "제안"보다 "점검"으로 쓴다. `AI 피드백`, `관찰 근거 확인`, `기재요령 리스크`, `Byte 점검`, `유사도 경보`를 기본 용어로 사용한다. `생성 수량 최대 10` 같은 하마룸 기능은 도입하지 않는다. 대신 `검토 관점 최대 10개`로 제한한다.

다섯째, 감사 로그에 AI 관여도를 남긴다. `llm_audits`에 프롬프트 해시, 마스킹 여부, 반환 유형, `contains_sentence_suggestion=false`, `needs_human_rewrite_count`를 저장한다. 추후 학교 감사에서 "AI가 대신 작성하지 않았다"는 시스템 증거가 된다.

구현 체크박스

- [ ] `backend/app/services/suggestion/composer.py`에서 완성 문장 반환 금지
- [ ] `backend/app/api/v1/records.py`에 최소 초안 Byte 검증 추가
- [ ] `record_versions.metadata.needs_human_rewrite_spans` JSONB 추가 검토
- [ ] `frontend/components/editor/RewriteRequiredMark.tsx` 생성
- [ ] `backend/tests/test_no_ai_sentence_generation.py` 생성
- [ ] `docs/COMPLIANCE_AI_USAGE.md`에 훈령 제4조·제15조 근거 정리

## 6. Claude 에이전트 팀 편성

기존 `docs/AGENT_TEAM.md`는 6명 구성이지만, 이번 실행팀은 요구사항에 맞춰 5명으로 고정한다. QA는 각 역할의 성공 지표와 리뷰 조건에 포함하고 별도 인원으로 두지 않는다.

### 6.1 `product-manager`

책임 범위는 사용자 스토리, 수용 기준, 스프린트 범위, 용어 정책이다. 하마룸 벤치마크 기능을 `도입`, `변형 도입`, `도입 금지` 3단계로 분류한다.

산출물은 `docs/PRODUCT_REQUIREMENTS.md`, `docs/SPRINT_PLAN.md`, `docs/COPY_POLICY.md`다. 성공 지표는 각 스프린트 종료 시 P0 스토리 완료율 90% 이상, 미정 요구사항 0건, 용어 정책 위반 0건이다. 의존성은 모든 역할에 요구사항을 제공하고, security-auditor에게 규제 리스크 결정을 받는다.

### 6.2 `backend-specialist`

책임 범위는 SQLAlchemy 모델, Alembic 마이그레이션, FastAPI 엔드포인트, 파일 업로드 검증, AI 피드백 파이프라인이다. 성취기준과 태그 라이브러리를 권위 데이터로 만들고, 학교 단위 RLS와 감사 로그를 적용한다.

산출물은 `backend/alembic/versions/0004_achievement_standards.py`, `0005_tags_traits.py`, `0006_favorites_uploads.py`, `backend/app/api/v1/standards.py`, `backend/app/api/v1/tags.py`, `backend/app/api/v1/uploads.py`, `backend/app/services/suggestion/composer.py`다. 성공 지표는 동기 API p95 300ms 이하, 파일 업로드 차단 테스트 100% 통과, 외부 LLM 호출 전 PII 마스킹 100%다. 의존성은 product-manager의 API 우선순위와 security-auditor의 정책을 입력으로 받고, frontend-specialist에 OpenAPI 계약을 제공한다.

### 6.3 `frontend-specialist`

책임 범위는 Next.js 15 App Router 라우트, 스텝 위저드, 3-pane 에디터, 태그 칩, 업로드 UI, 접근성이다. 기존 `/records` 중심 화면을 `/records/subject/new`와 `/records/{recordId}/edit`로 분리한다.

산출물은 `frontend/app/records/subject/new/page.tsx`, `frontend/app/records/[recordId]/edit/page.tsx`, `frontend/components/wizard/*`, `frontend/components/editor/*`, `frontend/types/subject-wizard.ts`다. 성공 지표는 키보드만으로 Step 1~6 완료 가능, Lighthouse Accessibility 95 이상, Byte 카운터 서버 오차 1% 미만이다. 의존성은 backend-specialist의 API 계약과 design-director의 토큰을 받는다.

### 6.4 `design-director`

책임 범위는 IA, 디자인 토큰, 태그 칩 상태, 피드백 심각도 시각화, 사용자 카피다. 하마룸 민트 계열은 유지하되, "AI 생성기"처럼 보이는 시각 언어는 피한다.

산출물은 `docs/DESIGN_SYSTEM.md`, `docs/UX_TONE.md`, `frontend/design-tokens/colors.ts`, `frontend/components/ui/Chip.tsx`, `frontend/components/ui/Stepper.tsx`다. 성공 지표는 색 대비 WCAG AA 100%, 버튼 radius 8px 이하, AI 생성·자동 작성 금지어 UI 노출 0건이다. 의존성은 product-manager의 카피 정책을 받고 frontend-specialist에 토큰과 컴포넌트 규칙을 제공한다.

### 6.5 `security-auditor`

책임 범위는 훈령·개인정보·외부 API·파일 업로드·감사 로그 검증이다. 특히 파일 업로드와 LLM 호출 경로를 P0 보안 영역으로 본다.

산출물은 `docs/SECURITY_AUDIT.md`, `docs/COMPLIANCE_AI_USAGE.md`, `backend/tests/security/test_upload_validation.py`, `backend/tests/security/test_rbac_records.py`, `scripts/verify_audit_chain.py`다. 성공 지표는 P0 보안 이슈 0건, 외부 도메인 allowlist 3개 이하, 감사 해시체인 검증 성공률 100%다. 의존성은 backend-specialist와 frontend-specialist의 구현물을 입력으로 받고 product-manager에게 출시 승인 또는 보류 의견을 제공한다.

구현 체크박스

- [ ] `docs/AGENT_TEAM.md`를 5명 구성으로 개정
- [ ] `docs/PRODUCT_REQUIREMENTS.md` 생성
- [ ] `docs/COPY_POLICY.md` 생성
- [ ] `docs/COMPLIANCE_AI_USAGE.md` 생성
- [ ] 각 에이전트별 PR 템플릿 생성

## 7. 구현 로드맵: 6주 스프린트 × 4회

### Sprint 1: 성취기준·태그 라이브러리 스키마/시드/API/라이브러리 페이지

기간: 2026-04-15 ~ 2026-05-26. 목표는 작성 재료의 권위 데이터를 구축하는 것이다. 백엔드는 `achievement_standards`, `activity_tags`, `student_traits`, `favorite_templates` 모델과 마이그레이션을 만든다. API는 `/standards`, `/tags/activity`, `/tags/traits`, `/favorite-templates`를 우선 구현한다. 프론트엔드는 `/library`와 `/library/standards`, `/library/tags`, `/library/templates`를 만든다.

완료 기준은 중학교 수학·국어·영어 성취기준 최소 100건 시드, 시스템 활동 태그 40개, 학생 특성 태그 40개, 라이브러리 검색 응답 p95 300ms 이하, 관리자 태그 생성·비활성화 가능이다. 성취기준 공식 원자료 위치는 Sprint 1 Day 1에 확정해야 하며, 확정 전에는 샘플 시드에 `source_doc='조사 필요'`를 명시한다.

### Sprint 2: 교과세특 스텝 위저드 프론트엔드

기간: 2026-05-27 ~ 2026-07-07. 목표는 교과세특 작성 시작 경험을 완성하는 것이다. `/records/subject/new`에 Step 1~6을 구현하고, `/records/{recordId}/edit`에 3-pane 에디터를 연결한다. 태그 선택 카운터는 활동 유형 2개, 역할 1개, 특성 2개 권장으로 고정한다. Byte 제한은 `section_types.byte_limit`의 `setuk_subject=1500`을 사용한다.

완료 기준은 빈 초안 제출 차단, 성취기준 0개 차단, 전체 태그 0개 차단, 1검 제출 게이트 통과 시 `POST /records/{id}/reviews` 호출, 모바일 390px 폭에서 텍스트 overflow 0건이다.

### Sprint 3: 담임 전용 작성기 + 파일 업로드 분석

기간: 2026-07-08 ~ 2026-08-18. 목표는 담임 영역에 동일한 작성 보조 흐름을 적용하고 업로드 분석을 추가하는 것이다. `/records/homeroom`에 행종의, 자율, 진로, 봉사, 창체, 일상생활 탭을 둔다. 파일 업로드는 `.pdf`, `.docx`를 우선 지원하고 `.hwp`는 MVP에서 보관·검증만 한다. 업로드 분석 결과는 "과제 근거 요약", "관찰 근거 후보", "개인정보 포함 가능성" 3개 카드로만 표시한다.

완료 기준은 파일당 10MB, 기록당 3개 제한 적용, magic bytes 검증, 악성 파일 스캔 실패 시 사용 차단, 추출 텍스트 외부 LLM 전송 전 마스킹, 담임 작성기에서 최소 초안 Byte 검증 적용이다.

### Sprint 4: 즐겨찾기·검토 개선·접근성·성능

기간: 2026-08-19 ~ 2026-09-29. 목표는 반복 사용성과 운영 품질을 올리는 것이다. 즐겨찾기 템플릿, 최근 작성 내역, 검토 큐 필터, span 코멘트, 접근성, 성능 최적화를 구현한다. `ReviewQueueTable`은 단계, 학년, 반, 과목, 대기일수로 필터링한다. 최근 작성 내역은 `/dashboard`에 20건 표시한다.

완료 기준은 Lighthouse Performance 90 이상, Accessibility 95 이상, 검토 큐 p95 500ms 이하, Playwright E2E 20개 통과, `AI 생성` 금지어 스냅샷 테스트 통과, 감사 로그 해시 검증 스크립트 통과다.

구현 체크박스

- [ ] Sprint 1 백엔드 마이그레이션 3개 완료
- [ ] Sprint 1 라이브러리 페이지 4개 완료
- [ ] Sprint 2 교과세특 위저드 완료
- [ ] Sprint 2 제출 게이트 완료
- [ ] Sprint 3 파일 업로드 분석 완료
- [ ] Sprint 3 담임 작성기 완료
- [ ] Sprint 4 즐겨찾기·최근 내역 완료
- [ ] Sprint 4 접근성·성능 게이트 완료

## 8. 리스크·완화

1. 2022 개정 교육과정 성취기준 원자료 확보 리스크. 공식 원자료의 구조가 PDF 중심이면 자동 시드 정확도가 낮아질 수 있다. 완화책은 Sprint 1 Day 1에 원자료 URL, 저작권, 표 구조를 확정하고, Day 5까지 중학교 수학 30건을 수동 검수한 golden dataset으로 만든다.

2. 훈령 위반 포지셔닝 리스크. 태그 선택 후 LLM이 완성 문장을 반환하면 제품 정체성이 무너진다. 완화책은 API 스키마에서 `sentence_suggestions` 필드를 만들지 않고, LLM JSON Schema를 `missingEvidence`, `riskFlags`, `questionsForTeacher`로 제한한다. 테스트는 반환값에 종결어미 `함/임/음/다`가 포함된 긴 문장이 있는지 검사한다.

3. 파일 업로드 보안 리스크. HWP, DOC, PDF는 매크로, polyglot, zip bomb, 개인정보 메타데이터 위험이 있다. 완화책은 magic bytes, MIME, 크기, 압축비, 백신 스캔, 텍스트 추출 격리 워커를 적용하고, 실패 시 피드백 파이프라인 입력에서 제외한다.

4. 개인정보 외부 유출 리스크. 학생 이름, 학번, 반 정보, 과제 본문이 LLM으로 나갈 수 있다. 완화책은 `backend/app/services/mask/pii.py`를 LLM 호출 전 강제 경유시키고, `llm_audits.masked=true`가 아니면 요청을 중단한다.

5. UI 복잡도 리스크. 6단계 위저드와 3-pane을 함께 쓰면 화면이 복잡해질 수 있다. 완화책은 최초 작성은 위저드, 수정은 3-pane으로 역할을 분리하고, 모바일에서는 피드백 패널을 드로어로 숨긴다.

6. 성능 리스크. 성취기준 검색, 태그 로딩, 피드백 저장, 유사도 조회가 한 화면에 몰리면 초기 로딩이 느려질 수 있다. 완화책은 standards/tags를 TanStack Query로 10분 캐시하고, Stage 5 LLM은 비동기 SSE 또는 폴링으로 합류시킨다.

7. 교사 수용성 리스크. "AI가 감시한다"는 인상을 주면 사용률이 낮아진다. 완화책은 카피를 `위반`, `차단` 중심이 아니라 `확인 필요`, `근거 보강`, `제출 전 점검`으로 조정하되, block 조건은 명확히 유지한다.

8. 결제 섹션 도입 리스크. 하마룸에는 플랜 결제가 있지만 학교 내부 포털에서 결제 UI는 조달·계약 흐름과 충돌할 수 있다. 완화책은 MVP에서 `플랜 결제`를 도입하지 않고, 관리자용 `라이선스 상태` 읽기 화면만 조사 대상으로 둔다.

구현 체크박스

- [ ] `docs/RISK_REGISTER.md` 생성
- [ ] 성취기준 원자료 조사 티켓 생성
- [ ] LLM JSON Schema 회귀 테스트 생성
- [ ] 파일 업로드 보안 테스트 생성
- [ ] PII 마스킹 강제 테스트 생성
- [ ] UX 사용성 테스트 시나리오 5개 작성

## 근거 및 조사 필요 항목

확인한 공식 근거는 학교생활기록부 종합지원포털의 `학교생활기록 작성 및 관리지침 [시행 2026. 3. 1.] [교육부훈령 제555호, 2026. 2. 12., 일부개정]`이다. 확인한 조항은 제4조 제2항의 직접 관찰·평가 근거 입력 원칙, 제15조 제6항의 과목별 성취기준·성취수준·학습활동 참여도 문장 입력 원칙, 제15조 제14항의 교과담당교사 입력 원칙이다. 공식 페이지: https://star.moe.go.kr/web/contents/m20103.do?id=108056&schM=view

추가 조사 필요 항목은 4개다. 첫째, 2026학년도 학교생활기록부 기재요령 PDF의 생성형 AI 문구 정확한 페이지와 원문. 둘째, 2022 개정 교육과정 성취기준의 과목별 공식 데이터 파일 위치와 사용 조건. 셋째, `.hwp` 서버 측 텍스트 추출 라이브러리의 안정성과 라이선스. 넷째, 학교 단위 상용 배포 시 결제/라이선스 UI가 필요한지 여부다.

