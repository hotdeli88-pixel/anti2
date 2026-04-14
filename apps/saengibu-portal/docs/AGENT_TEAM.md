# Claude 에이전트 팀 편성 — saengibu-portal

> 하마룸(hamaroom.com) 패리티 + 훈령 준수를 양립시키는 고성능 개발 팀 구성. 각 에이전트는 독립적으로 호출되며, 지정된 입출력 계약을 준수한다.

## 0. 팀 철학

| 원칙 | 구현 |
|---|---|
| **전문성 분리** | 각 역할은 단일 책임만, 크로스오버는 "의존성"으로 표현 |
| **결정적 산출물** | 모든 산출물은 파일 경로 · PR 제목 · 체크박스까지 명시 |
| **병렬 우선** | 의존성이 없으면 병렬 호출, 동기 지점만 수동 제어 |
| **근거 우선** | 추측 금지, 실제 파일·훈령 조항·벤치마크 URL 인용 |
| **품질 게이트** | 각 산출물은 최소 1명의 다른 에이전트 리뷰 통과 필요 |

---

## 1. 팀 구성 (6명)

### 1.1 `product-manager` (PM)

**책임**
- 사용자 스토리·수용 기준(AC)·마일스톤 관리
- 이해관계자(교사·관리자·감사) 요구 번역
- 에이전트 간 우선순위 중재

**산출물**
- `dev/active/saengibu-sprints.md` — 6주 스프린트 4회 계획
- `dev/active/user-stories.md` — 20개 이상 스토리 (`AS … I WANT … SO THAT …`)
- `dev/active/release-notes-v1.md`

**성공 지표**
- 스프린트 완료율 ≥ 85%
- 스토리 AC 통과율 ≥ 90%

**의존성**
- Input: `IMPROVEMENT_PLAN.md` (이 문서와 동시 생성)
- Output → all other agents

---

### 1.2 `backend-specialist`

**책임**
- FastAPI/SQLAlchemy 설계·구현·마이그레이션
- AI 파이프라인 6단계 (Stage 1 Byte · 2 금지어 · 3 문체 · 4 유사도 · 5 LLM · 6 체크리스트)
- RLS·감사 해시체인·성능 최적화
- 파일 업로드 파이프라인 (hwp/doc/pdf MIME+Magic 검증, 바이러스 스캔)

**산출물**
- `backend/alembic/versions/0004_achievement_standards.py` — 성취기준 시드 (2022 개정 교육과정 / 중학교 수학/국어/영어 최소)
- `backend/alembic/versions/0005_activity_tags.py` — 과목별 활동 태그 · 학생 특성 태그 시드
- `backend/alembic/versions/0006_favorites_uploads.py` — 즐겨찾기 · 업로드 파일 테이블
- `backend/app/api/v1/{standards,tags,uploads,suggestions,favorites}.py`
- `backend/app/services/ai/{banned_stage,style_stage,llm_stage}.py`
- `backend/app/services/suggestion/composer.py` — 태그 조합 → LLM "관점 제시" 프롬프트
- `backend/tests/` — 커버리지 목표 ≥ 70% (services/*, api/*)

**성공 지표**
- API p95 레이턴시 ≤ 300ms (동기 경로)
- Stage 1~4 확정적 결과 (동일 입력 동일 출력)
- 회원 가입·승인·세션 플로우 E2E 테스트 통과

**의존성**
- Input: PM의 user-stories + `IMPROVEMENT_PLAN.md`
- Output → frontend-specialist (API 계약), security-auditor (리뷰)

---

### 1.3 `frontend-specialist`

**책임**
- Next.js 15 App Router 페이지·컴포넌트·상태 관리
- 하마룸 3-step wizard UX 이식 (교과세특 에디터)
- 태그 칩 · Byte 미터 · 파일 업로더 · AI 피드백 사이드 패널
- 접근성(WCAG AA) · 키보드 네비 · 모바일 반응형

**산출물**
- `frontend/app/records/new/page.tsx` — 3-step 위저드 진입
- `frontend/app/records/[recordId]/edit/page.tsx` — 3-pane 에디터 (좌: 본문, 우: 피드백, 하단: 단계 진행)
- `frontend/app/library/page.tsx` — 성취기준·활동 태그·예시문 라이브러리
- `frontend/components/wizard/{WizardSteps,SubjectSelector,StandardPicker,TagChipGroup,UploadZone}.tsx`
- `frontend/components/editor/{RecordEditor,FeedbackSidePanel,ByteMeter,ChecklistGate}.tsx`
- `frontend/components/ui/{Chip,Stepper,Drawer,CommandPalette,EmptyState}.tsx`

**성공 지표**
- Lighthouse Performance ≥ 90, Accessibility ≥ 95
- 키보드만으로 "행종의 작성 → 1검 제출" 완주 가능
- Byte 미터 클라이언트 오차 < 1% (서버와 비교)

**의존성**
- Input: backend-specialist API 스펙, design-director 디자인 토큰
- Output → qa-engineer, design-director (리뷰)

---

### 1.4 `design-director`

**책임**
- 디자인 시스템(색/타이포/간격/모션/elevation) 토큰화
- 하마룸 대비 "AI 피드백" 포지셔닝 시각 차별화
- 로고·브랜드·온보딩·Empty State 비주얼
- 콘텐츠 운영 (Guidelines, 알림 카피, 에러 메시지 톤)

**산출물**
- `frontend/design-tokens/{colors,typography,spacing,motion}.ts`
- `frontend/components/ui/Brand.tsx` — 로고 + 타이포 조합
- `docs/DESIGN_SYSTEM.md` — 토큰 카탈로그 + 사용 가이드
- `docs/UX_TONE.md` — 카피 톤 가이드 (감시 아닌 조력)
- `backend/alembic/versions/0007_guidelines_expansion.py` — 안내 콘텐츠 10+ 추가
- `backend/alembic/versions/0008_notification_templates.py` — 알림 카피 20+

**성공 지표**
- 색 대비 AA 통과 100%
- 콘텐츠 톤 검토 사용자 만족도 ≥ 4.2/5
- 디자인 토큰 사용률 ≥ 95% (하드코딩 색/값 ≤ 5%)

**의존성**
- Input: PM 스토리, 하마룸 벤치마크
- Output → frontend-specialist (토큰 소비), PM (콘텐츠 승인)

---

### 1.5 `security-auditor`

**책임**
- 훈령 제555호 · 개인정보보호법 · 교육부 지침 준수 검증
- 외부 API 호출 경로 감사 (LLM·Google 외 차단)
- 감사 해시체인·RLS·쿠키·CSP 강화
- 파일 업로드 공격 벡터 차단 (ZIP slip, polyglot, 메타데이터 PII)

**산출물**
- `docs/SECURITY_AUDIT.md` — P0/P1/P2 이슈 + 수정 제안
- `backend/alembic/versions/0009_rls_enable.py` — 전 테이블 RLS 정책
- `backend/tests/security/` — 권한 우회·CSRF·JWT 만료·SQL 인젝션 테스트
- `docs/PRIVACY_DPA.md` — 개인정보 처리방침 + DPA 템플릿
- `scripts/verify_audit_chain.py` — 감사 로그 해시 검증

**성공 지표**
- OWASP ASVS Level 2 통과
- 감사 로그 체인 무결성 100% (일 1회 자동 검증)
- 외부 도메인 아웃바운드 차단 제외 목록 ≤ 3개

**의존성**
- Input: backend-specialist 구현 → 리뷰
- Output → PM (리스크 보고), backend-specialist (수정 요청)

---

### 1.6 `qa-engineer`

**책임**
- 단위/통합/E2E 테스트 설계·실행
- 훈령 위반 탐지 정확도(Recall/Precision) 측정
- 성능·부하 테스트 (동시 100 교사 시뮬레이션)
- 회귀 방지 CI 파이프라인

**산출물**
- `backend/tests/fixtures/records_clean/` 100건, `records_violations/` 360건(12×30)
- `frontend/e2e/` Playwright 시나리오 20개
- `backend/tests/perf/locustfile.py` — 동시 100 교사 시나리오
- `.github/workflows/ci.yml` — path filter + test matrix
- `docs/QA_METRICS.md` — 월 1회 측정 리포트 템플릿

**성공 지표**
- 테스트 커버리지 ≥ 70% (backend), ≥ 60% (frontend)
- 위반 탐지 Recall ≥ 0.95, Precision ≥ 0.80
- CI 실행 시간 ≤ 5분

**의존성**
- Input: 모든 에이전트 산출물
- Output → PM (품질 리포트), 모든 에이전트 (버그 티켓)

---

## 2. 협업 프로토콜

### 2.1 호출 패턴

```
[User / Main Claude]
      │
      ▼
┌──────────────────────┐
│  product-manager     │  ← 최상위 오케스트레이터
└─┬───┬───┬───┬───┬───┘
  │   │   │   │   │
  ▼   ▼   ▼   ▼   ▼
 BE  FE  DS  SA  QA         ← 병렬 실행 가능
  │   │   │   │
  └───┴─┬─┴───┘
        ▼
┌──────────────────────┐
│  qa-engineer         │  ← 최종 품질 게이트
└──────────────────────┘
```

### 2.2 상호 의존성 매트릭스

| 소비자 ↓ \ 생산자 → | PM | BE | FE | DS | SA | QA |
|---|---|---|---|---|---|---|
| **PM** | — | 진도 | 진도 | 진도 | 리스크 | 품질 |
| **BE** | 스토리·AC | — | API 계약 요청 | — | 보안 요구 | 버그 |
| **FE** | 스토리·AC | API 계약 | — | 토큰·카피 | — | 버그 |
| **DS** | 브랜드 요구 | — | 토큰 요청 | — | — | — |
| **SA** | 규제 맥락 | 코드 | 코드 | — | — | 보안 테스트 |
| **QA** | 수용 기준 | 구현물 | 구현물 | 카피 | 보안 기준 | — |

### 2.3 산출물 품질 게이트

1. **PR 생성 시**: 해당 영역 전문가가 자신 작성
2. **리뷰 필수**: 최소 1명의 다른 전문가 (크로스 리뷰 매트릭스 참조)
3. **CI 통과**: qa-engineer의 테스트 스위트 전 항목 green
4. **보안 스캔**: security-auditor의 `bandit`, `semgrep`, `npm audit` 무결
5. **Merge**: PM 최종 승인

### 2.4 호출 예시 (Main Claude에서)

```text
# Sprint 1 착수 시
Agent({subagent_type: "general-purpose", name: "pm-001",
       prompt: "You are product-manager for saengibu-portal ..."})

# Sprint 1.1: 성취기준 DB 구축 (병렬)
parallel([
  Agent({name: "be-standards", prompt: "You are backend-specialist. \n" +
         "Task: Implement achievement_standards table + seed ..."}),
  Agent({name: "ds-tokens", prompt: "You are design-director. \n" +
         "Task: Finalize color/typography/motion tokens ..."}),
])

# Sprint 1.1 완료 후 리뷰
Agent({name: "sa-review-01", prompt: "You are security-auditor. \n" +
       "Review be-standards PR for RLS/PII/injection risks ..."})
```

---

## 3. 구현 가이드라인 (모든 에이전트 공통)

### 3.1 코드 스타일
- Python: PEP 8 + `ruff` (line-length 100)
- TypeScript: strict + ESLint + Prettier (tailwind plugin)
- 코멘트: 기본 없음, WHY 명확할 때만 1줄

### 3.2 커밋
- Conventional Commits, 범위 `saengibu-portal`
- 한 PR = 한 논리 변경 (최대 500줄 권장)

### 3.3 문서
- API 변경 시 `docs/API.md` 업데이트
- ADR 추가는 `docs/adr/NNNN-title.md`
- 설계 공용 지식은 `docs/` 루트, 일시적 계획은 `dev/active/`

### 3.4 훈령 준수 (모두 숙지)
1. AI는 **문장을 대신 쓰지 않는다** — 태그·관점·체크리스트만 제시
2. 모든 LLM 호출 전에 학교·학년도 전체 실명 마스킹
3. 학교 도메인 이메일만 가입, 관리자 승인 필수
4. 외부 LLM은 기본 차단 (`LLM_EXTERNAL_ENABLED=false`)
5. 감사 로그 해시 체인 무결성 유지

---

## 4. 킥오프 체크리스트

- [ ] PM이 `user-stories.md` 초안 작성
- [ ] design-director가 `DESIGN_SYSTEM.md` 토큰 카탈로그 완성
- [ ] backend-specialist가 Sprint 1 스키마 3종 마이그레이션
- [ ] frontend-specialist가 WizardSteps·TagChipGroup 컴포넌트 프로토
- [ ] security-auditor가 RLS 정책 초안 + 파일 업로드 검증 체크리스트
- [ ] qa-engineer가 CI 워크플로우 + fixture 디렉터리 생성
- [ ] 모든 에이전트 상호 의존성 매트릭스 합의

---

## 5. 에스컬레이션

- 역할 간 충돌 → PM 중재
- 훈령 해석 불명 → security-auditor + 외부 자문(교육청 질의)
- 기술 부채 누적 → backend-specialist 주도 리팩토링 스프린트 (Sprint 4 말)
- 성능 KPI 미달 → qa-engineer + backend-specialist 합동 TF
