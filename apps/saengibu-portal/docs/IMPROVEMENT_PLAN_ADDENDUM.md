# 개선안 보완(ADDENDUM) — 전문가 평가 통합

> 2026-04-14. 본 문서는 [`IMPROVEMENT_PLAN.md`](./IMPROVEMENT_PLAN.md)의 부록이다.
> Codex 단일 산출물에 + 하마룸 추가 페이지 분석 + Claude 전문가 3종(Frontend/UX · Backend Architecture · Design/ContentOps) 피드백을
> 통합했다. **결제 관련 기능은 제외하며**, Notion 기획서는 JavaScript 렌더링 장벽으로 직접 추출 불가하여
> 하마룸 공개 페이지 분석과 훈령/기재요령 원문으로 갈음했다.

## 0. 변경 범위 요약

- ✅ 사이드바 IA 확장 (3 → 7개): 홈 / 결재 대기열 / 세특 작성 / 담임 전용 / 라이브러리 / 공지·게시판 / 환경 설정
- ✅ 디자인 토큰 보강 (info/ok/warn/danger의 bg 변형, AI 피드백 보라, 타이포 스케일 8단계, 모션·zIndex·focus ring)
- ✅ ApprovalTable AI 경보 컬럼 복원 + 스켈레톤 + Empty State
- ✅ 신규 Backend 스키마 6종 (achievement_standards · activity_tags · favorite_templates · uploaded_files · ai_suggestions · notice_posts)
- ✅ Alembic 0004/0005 추가 (스키마 + 시드: 성취기준 25건, 태그 50+ 건, 공지 샘플 4건)
- ✅ 신규 Frontend 페이지 5종 (/writer /writer/new/subject /library /board /homeroom)
- ✅ 신규 컴포넌트 5종 (WizardSteps · TagChipGroup · ByteMeter · FileUploader · EmptyState)

## 1. 하마룸 추가 분석 (서브젝트별 태그 차이)

| 영역 | 수학 | 국어 | 영어 | 공통 |
|---|---|---|---|---|
| **수업 활동 태그** | 문제풀이·창의사고·교구·개별학습·탐구보고서·자료해석·그래프·실생활연계 | 토론·발표·독서·글쓰기·문학감상·자료조사·역할극·창작·비판적사고·퀴즈게임·모둠 | 듣기·말하기발표·원서읽기·글쓰기과제·모둠프로젝트·어휘학습 | — |
| **학생 특성** | 개념이해/융합능력/논리사고력/도형공간감각/수리표현 | 독해력/표현력/어휘력/창의성/필자의도파악/비판적사고력 | 듣기집중력/발음/문법정확성 | — |
| **역할 수행** | — | — | — | 과목부장·모둠장·모둠원·봉사정신·교사지원 |
| **성장 정도** | — | — | — | 역량향상·사고발달·수준향상·협력성장·자기주도성 |

→ 본 프로젝트는 `activity_tags.subject_code` + `section_type_id` + `category` 3차원으로
분리해 배치하고, `NULL`은 "전 과목·전 영역 공통"을 의미한다. 2026-04-14 기준 총 50+ 시드 태그.

## 2. 하마룸 담임 전용 분석

하마룸 담임 전용 페이지는 3가지 기능 제공:
1. **행동특성 및 종합의견**: 학생 행동 특성 + 누가기록 파일 첨부
2. **창체-자율 특기사항 B타입**: 활동명 → 특기사항 자동 생성
3. **진로활동 C타입**: 활동명 → 특기사항 자동 생성

우리 포지셔닝 차이: "활동명만 입력하면 자동 생성"은 훈령 2026 "AI 생성 자료를 그대로 입력 금지"
조항과 충돌한다. 따라서 **동일한 진입점(/homeroom)을 제공하되, 각 영역은 6단계 위저드**로 구성한다.
`/homeroom` 페이지에 6개 영역 카드(행종의·자율·진로·봉사·일상생활·출결)를 배치하고 각각 `/writer/new/homeroom/{code}`로 이동.

## 3. Frontend/UX 전문가 주요 반영 (P0 7건)

| P0 | 반영 상태 | 파일 |
|---|---|---|
| P0-1. AI 경보 컬럼 누락 | ✅ 반영 | `components/records/ApprovalTable.tsx:53,84-94` |
| P0-2. 반려 버튼·optimistic UI 부재 | 🟡 계획만 | 다음 PR: Dialog + useReject 연결 |
| P0-3. DOMPurify 없이 dangerouslySetInnerHTML | 🟡 계획만 | `components/records/{Guidelines,Decisions}Panel.tsx` — `isomorphic-dompurify` 도입 예정 |
| P0-4. IA 3개 → 7개 확장 | ✅ 반영 | `components/layout/Sidebar.tsx` 섹션 그룹핑 포함 |
| P0-5. 로그아웃 하드 리다이렉트 | 🟡 계획만 | `lib/queries.ts:96` `useLogout` onSuccess에 router.replace 도입 |
| P0-6. 로딩 상태 텍스트 1줄 | ✅ 반영 | `.skeleton` 유틸 + `SkeletonRows` in ApprovalTable |
| P0-7. 모바일 사이드바 260px 고정 | 🟡 계획만 | Radix Dialog Drawer로 ≤md 분기 필요 |

추가로 반영:
- `focus-visible` 전역 ring (globals.css :focus-visible)
- `prefers-reduced-motion` 준수
- aria-label·scope 속성 (ApprovalTable, WizardSteps)
- EmptyState 컴포넌트 신규 (Empty State 카피 10종 중 "오늘은 검토할 초안이 없어요" 채택)

## 4. Backend 전문가 주요 반영 (총 36개 엔드포인트 중 기초 단계)

### 도입된 부분
- 신규 도메인 모델 6종 (`app/models/standards.py`)
- 신규 마이그레이션 0004 (스키마) · 0005 (시드)
- Sidebar IA 확장 시 요구되는 API 윤곽

### P0 중 후속 스프린트에서 처리
- B1. `/records` CRUD 라우터 신설 → `app/api/v1/records.py` (다음 PR)
- B2. FSM `SELECT ... FOR UPDATE` 락
- B3. Stage 2 금지어 사전 (pyahocorasick)
- B4. Stage 5 LLM 클라이언트·llm_audits
- B5. RLS 정책 실제 ENABLE
- B6. 감사 체인 advisory lock
- B7. RBAC scope matching (담임=학급 매칭)
- B9. 테스트 0건 → `tests/{unit,integration,rbac,e2e}/` 도입
- B10. `python-multipart` 의존성 + UploadFile 파이프라인

구체적 마이그레이션 로드맵: [`IMPROVEMENT_PLAN.md`](./IMPROVEMENT_PLAN.md) §4 참조.

## 5. Design/ContentOps 전문가 주요 반영

### 도입된 부분
- 색상 토큰 보강: `info/ok/warn/danger` 전부에 `.bg` 변형 추가, `ai.{detected,pii,guideline,style,brain}` 네임스페이스 신설, `brand.tertiary`(#7C3AED) 보라
- 타이포 스케일 8단계 (`caption/body-sm/body/body-lg/title/heading/display/display-lg`)
- 모션 토큰: `quick/base/moderate/med/slow`, `out-expo/standard` 이징
- zIndex 토큰 (`dropdown/sticky/overlay/modal/toast/tooltip/command`)
- 신규 유틸: `.skeleton` · `.bg-ai-gradient` · `.text-ai-gradient` · `.badge-ai`
- 접근성: reduce-motion · focus-visible 전역

### 후속 스프린트 (카피·안내 콘텐츠)
- Guidelines 12개 이상 확장 (현재 3건 → 15건) — 별도 마이그레이션 0006
- Notice(공지) 카테고리 5종: announcement · training · library · faq · release
- 알림 카피 템플릿 20+ · 에러 카피 20+ · Empty State 10+ → `docs/UX_TONE.md` 분리 작성 예정
- 로고 심볼 커스터마이즈 (심볼+워드마크 2안 중 선택)
- 다크모드 대응 (next-themes 도입 전 CSS variable 재구성 필요)
- **아이콘 단일화**: preview.html은 FontAwesome, React는 lucide 혼재 → lucide 전면 채택 (preview는 디자인 명세로 주석)

## 6. "AI 생성기"가 아닌 "AI 피드백 assistant" 포지셔닝 구체화

### UI 카피 규칙 (금지/허용)

| 금지 | 허용 |
|---|---|
| "AI가 생성하기" | "AI 관점 점검" |
| "자동 작성" | "초안 검토" |
| "결과 생성" | "고려할 관점 확인" |
| "문장 추천" | "개선 제안" |
| "점수: 78/100" | "기준 충족 / 검토 권장 / 필수 수정" |

### 훈령 위반 없이 "생성기 효과"를 내는 4가지 기법

1. **태그 칩 체크리스트**: 교사 관찰 단서 수집 → LLM 입력 맥락에 포함, 단 **출력은 "제시할 관점"만**
2. **교사 초안 강제**: 빈 에디터로 1검 제출 시 422 `validation/missing-draft` 반환
3. **AI 제안 사용 흔적 플래그**: 제안 수용 시 `ai_suggestion_accepted_at` 기록, 검토자 UI에서 "재작성 권장" 표시
4. **체크리스트 게이트**: `no_fabrication_confirmed` + `guidelines_reviewed` + `own_sentence` 3개 모두 체크 시에만 submit 가능

### 구현 반영 위치

- `/writer/new/subject/page.tsx` Step 4 텍스트 강제 입력
- `/writer/new/subject/page.tsx` Step 5 "AI 관점 점검"으로 명명
- `/writer/new/subject/page.tsx` Step 6 체크리스트 3종 모두 체크 전 "1검 제출" 비활성화
- `FeedbackSidePanel`(후속 PR): "개선 제안 N건" 카피, 🛑 대신 ⛔ + 조력 톤

## 7. Notion 기획 문서 대응

제공 URL(`adventurous-country-d08.notion.site/AI-21eb7446305880a78f03dca693e6d534`)은
Notion의 클라이언트 사이드 렌더링으로 공개 HTML을 통한 직접 추출이 불가했다.

**대응 전략**:
- 문서 본문이 필요한 경우 사용자가 PDF/Markdown 익스포트 후 첨부 요청
- 임시 대안으로 교육부 훈령 제555호 원문 + 하마룸 공개 UX + Claude 전문가 3인의 의견으로 갈음
- 추후 콘텐츠 수령 시 `docs/notion-spec-review.md`로 별도 정리

## 8. 에이전트 팀 호출 예시 (실행 가능)

Codex 플랜 §6에서 정의된 6 에이전트 팀을 실제 호출하는 방법:

```bash
# PM이 Sprint 1 킥오프
claude "product-manager 역할로 saengibu-portal Sprint 1 user-stories.md 작성.
        /mnt/c/Users/sdm24/OneDrive/바탕 화면/03_개발프로젝트/anti2/apps/saengibu-portal/docs/
        IMPROVEMENT_PLAN.md 참고. 최소 20개 스토리."

# 병렬 실행
claude --agent backend-specialist "신규 엔드포인트 /achievement-standards GET 구현. 파일:
        backend/app/api/v1/standards.py, schemas/standards.py. curriculum/grade/subject 필터.
        테스트 3건(200/필터/페이지네이션)."
claude --agent frontend-specialist "LibraryPage 검색 엔드포인트 연결. useAchievementStandards 훅
        추가. standards 탭에 서버 응답 바인딩. 페이지네이션 cursor 지원."
claude --agent security-auditor "alembic 0004/0005 마이그레이션 RLS 정책 누락 점검.
        activity_tags, favorite_templates, uploaded_files, ai_suggestions, notice_posts
        school_id 기반 policy 추가."
```

## 9. 다음 PR 우선순위 (2주 내)

1. **P0 치명**: DOMPurify 도입, 반려 플로우, 로그아웃 SPA 전환
2. **Backend B1/B5/B7**: `/records` CRUD + RLS 활성화 + RBAC 스코프 매칭
3. **Backend B3**: 금지어 사전 12 카테고리 + Aho-Corasick
4. **Frontend 검증**: WizardSteps/TagChipGroup/ByteMeter/FileUploader 유닛 테스트 + Storybook
5. **Backend B10**: uploaded_files API + `python-multipart` + mimetype/magic 검증
6. **테스트**: backend `tests/` 디렉터리 생성 + conftest + FSM·byte·mask 유닛 10건 이상
7. **CI**: `.github/workflows/saengibu-ci.yml` 경로 필터 + pytest --cov 게이트

## 10. 체크리스트 (이번 PR 완료 항목)

- [x] 디자인 토큰 확장 (colors/typography/motion/zIndex)
- [x] 접근성 (focus-visible, reduce-motion)
- [x] Sidebar IA 7-section 재구성
- [x] ApprovalTable AI 경보 컬럼 + Skeleton + EmptyState
- [x] 신규 모델 6종 (`app/models/standards.py`)
- [x] Alembic 0004 스키마 + 0005 시드 (성취기준·태그·공지)
- [x] WizardSteps · TagChipGroup · ByteMeter · FileUploader · EmptyState 컴포넌트
- [x] /writer · /writer/new/subject · /library · /board · /homeroom 페이지
- [x] IMPROVEMENT_PLAN.md (Codex) + 본 ADDENDUM (통합)
- [x] AGENT_TEAM.md (6인 팀 편성·의존성)
