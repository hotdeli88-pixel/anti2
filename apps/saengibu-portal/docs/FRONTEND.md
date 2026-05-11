# FRONTEND — Next.js 15 App Router 설계

> TypeScript strict · Tailwind · Radix UI · TanStack Query · Zustand · next-intl (ko 기본)

## 0. 설계 원칙

1. **영역(section)-first UI**: NEIS 화면과 1:1 매칭. 탭 전환 = 영역 전환.
2. **에디터 중심**: 모든 작성 경로는 좌측 에디터 + 우측 피드백 패널.
3. **실시간 피드백 지연 < 500ms**: Stage 1~4 결과는 에디터 하단 배지·하이라이트.
4. **LLM 결과는 비동기 배지**: "AI 심층 피드백 분석 중…" 후 SSE로 합류.
5. **NEIS 복사 버튼은 approved 이후에만 활성**: 상태 가드는 서버 + 클라 이중.

---

## 1. 라우팅 (App Router)

```text
app/
├── (auth)/
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── pending/page.tsx              가입 승인 대기 안내
├── (admin)/
│   ├── schools/page.tsx              학교 설정
│   ├── organization/page.tsx         직제·부서
│   ├── users/page.tsx                사용자 관리·승인
│   ├── banned-dict/page.tsx          금지어 사전
│   └── audit/page.tsx                감사 로그
├── dashboard/
│   ├── page.tsx                      교사 대시보드 (기본)
│   ├── class/[classId]/page.tsx      학급 진행률 (담임)
│   ├── school/page.tsx               학교 전체 (교감+)
│   ├── review-queue/page.tsx         내 결재 대기
│   └── quality-trend/page.tsx        품질 트렌드 (관리자)
├── students/
│   ├── page.tsx                      내 학생 목록
│   └── [studentId]/
│       ├── page.tsx                  학생 개요 (전 영역)
│       └── records/[section]/page.tsx 영역별 에디터
├── reviews/
│   ├── page.tsx                      검토 내역
│   └── [reviewId]/page.tsx           단건 결재
├── activity-plans/
│   ├── page.tsx                      활동 계획 목록
│   ├── new/page.tsx                  신규 작성
│   └── [planId]/page.tsx             상세
├── duplicates/
│   └── page.tsx                      유사도 경보 (관리자)
├── settings/
│   └── page.tsx
└── layout.tsx                        전역 레이아웃 (네비·i18n 프로바이더)
```

### 레이아웃 그룹

- `(auth)`: 미인증 상태에서만 접근, 간단한 인증 레이아웃
- `(admin)`: 관리자·교감 이상만, 별도 사이드바
- 기본: 인증된 교사 모두

---

## 2. 네비게이션

### 상단 헤더

```
[로고] [학교명 · 2026학년도] ——— [검색] ——— [알림🔔] [사용자▾]
```

### 좌측 사이드바

```
📊 대시보드
👥 내 학생
📝 검토 큐 (12)
🗂 활동 계획
⚠️ 유사도 경보 (관리자)
⚙️ 설정
──────
[관리자 섹션]
🏫 학교 설정
👤 사용자 관리
📚 금지어 사전
🔍 감사 로그
```

---

## 3. 핵심 화면: 영역별 에디터

### 경로

`/students/[studentId]/records/[section]` — 예: `/students/xxx/records/haengjongjeui`

### 레이아웃 (3-pane)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [← 학생 목록]  학생: 홍*동 (1-3-15)  ·  영역: 행동특성 및 종합의견 ·│
│  2026학년도  ·  상태: 초안 [draft 배지]                              │
├────────────────────────────────────────┬────────────────────────────┤
│                                          │                            │
│  ┌────────────────────────────────────┐│  📊 피드백 패널            │
│  │                                    ││                            │
│  │   [Tiptap 에디터]                  ││  ─ Byte ─────────────      │
│  │   본문 입력…                        ││   287 / 300 B (95%) ✓    │
│  │                                    ││                            │
│  │                                    ││  ─ 금지어 ────────────     │
│  │                                    ││   ⚠️ "TOEIC" (line 3)     │
│  │                                    ││                            │
│  │                                    ││  ─ 문체 ──────────────     │
│  │                                    ││   ✓ 명사형 종결 OK         │
│  │                                    ││                            │
│  └────────────────────────────────────┘│  ─ 유사도 ────────────     │
│  [저장] [1검 제출]                     │   ⚠️ 91% 유사 (같은 반)   │
│                                          │                            │
│                                          │  ─ AI 심층 (LLM) ─        │
│  ─── 버전 이력 ───                       │   분석 중…                 │
│   v3  방금 전  홍길동                    │                            │
│   v2  어제    홍길동                     │  ─ 확인사항 체크리스트 ─  │
│                                          │   □ 허위·과장 없음        │
│                                          │   □ 기재요령 재확인        │
│                                          │   □ 내가 직접 작성        │
└────────────────────────────────────────┴────────────────────────────┘
```

### 컴포넌트

```tsx
// features/editor/RecordEditor.tsx
export function RecordEditor({ recordId }: Props) {
  const { data: record } = useRecord(recordId)
  const { data: feedback } = useFeedback(record?.current_version?.id)
  const mutate = useSaveDraft(recordId)
  const editor = useTiptap({ initialContent: record?.current_version?.text })

  // 저장 버튼 → Stage 1-4,6 실시간 검증
  const onSave = async () => {
    const res = await mutate.mutateAsync({ text: editor.getText() })
    // 하이라이트 span 업데이트
    highlightViolations(editor, res.violations)
  }

  return (
    <div className="grid grid-cols-[1fr_360px] gap-4 h-full">
      <EditorPane editor={editor} byteCount={feedback?.stages.byte.count} />
      <FeedbackPanel feedback={feedback} onSubmit={onSubmit} />
    </div>
  )
}
```

### Byte 카운터 (클라이언트)

- 클라에서도 CP949 근사 계산 (한글 3B, 영숫자 1B, 엔터 2B) 실시간 표시
- 서버 결과로 "최종 확정"
- 진행바: 0~80% green, 80~95% yellow, 95~100% orange, >100% red

### 하이라이트

- Tiptap 커스텀 Mark: `violation-block`, `violation-warn`
- 클릭 시 우측 패널 해당 항목 스크롤·하이라이트
- 호버 시 툴팁: 규칙 코드 · 근거 · 제안

---

## 4. 대시보드 화면

### 교사 대시보드 (`/dashboard`)

```
┌ 오늘 ──────────────────────────┐  ┌ 검토 대기 ────────────┐
│ 내 담당 기록 총 45건            │  │ 1검: 8건              │
│ 작성중 12  검토중 20  완료 13   │  │ 2검: 3건              │
│ [진행률 차트]                    │  │ 3검: 1건              │
└─────────────────────────────────┘  └────────────────────────┘

┌ 내 학급 (1-3) ──────────────────────────────────────────────┐
│ 학생별 진행률 표 (30명)                                      │
│ [홍**  행종:draft  자율:review_2  세특:approved  ...]        │
└──────────────────────────────────────────────────────────────┘

┌ 최근 반려 ─────────────────────┐  ┌ AI 피드백 요약 ────────┐
│ [홍** 행종] "개별성 부족"        │  │ Block 0건              │
│ 교무부장 · 2시간 전              │  │ Warn 12건              │
└─────────────────────────────────┘  └────────────────────────┘
```

### 학급 대시보드 (`/dashboard/class/[classId]`, 담임)

- 학생×영역 매트릭스 (히트맵)
- 영역별 완료율
- 주간 작성 추이

### 학교 대시보드 (`/dashboard/school`, 교감+)

- 학년별·학급별 완료율
- 검토 병목 지점 (오래 대기 중인 review_step)
- 이번 주 정정 건수

---

## 5. 검토 화면 (`/reviews/[reviewId]`)

- 본문 (읽기 전용)
- AI 피드백 요약 (stage별)
- 이전 검토 단계 결과 (누가 승인/반려)
- 코멘트 작성 (본문 span 선택 → 연결)
- [승인] [반려] 버튼

---

## 6. NEIS 복사 버튼

`approved` 이후 기록 상세에서:

```tsx
<NeisCopyButton recordId={id} onCopied={notify} />
```

클릭 플로우:

1. `POST /records/{id}/neis/render` — CP949 호환 텍스트 + 경고 반환
2. 경고 있으면 모달로 변환 내역 확인 ("— → -, U+3000 → ' ' …")
3. 확인 시 `navigator.clipboard.writeText(text)` + `POST /neis/copy-event`
4. 토스트: "클립보드에 복사됨. NEIS로 이동하여 붙여넣기 하세요."

---

## 7. 활동 계획 공유

### 리스트 (`/activity-plans`)

- 필터: 영역, 범위(학교/학년/학급/동아리), 작성자
- 카드: 제목, 대상, 기간, 공유 범위, 공유받은 교사 수

### 편집 (`/activity-plans/[planId]`)

- 계획 본문 (Tiptap)
- 공유 대상 선택 (사용자 검색 모달)
- "기록에 연결" 액션: 기존 record에 이 계획을 연결 (중복 탐지 컨텍스트용)

### 템플릿화

- "템플릿으로 저장" → `is_template=true`
- 다른 교사가 "복제(fork)" 가능

---

## 8. 유사도 경보 (`/duplicates`, 관리자)

| 열 | 내용 |
|---|---|
| 감지 시각 | 야간 배치 실행 시간 |
| 유형 | 학급 내 / 연도 간 / 교사 복붙 |
| Cosine | 0.93 |
| 원본·대상 기록 | 본문 diff 모달 |
| 조치 | [정상] [수정 요청] [무시] |

---

## 9. 금지어 사전 관리 (`/admin/banned-dict`)

- 카테고리별 탭 (12개)
- 각 엔트리: 패턴·severity·근거·활성 여부
- [추가] [비활성화] [연 단위 버전 태그]
- 테스트 모드: 샘플 텍스트 붙여넣고 탐지 결과 확인

---

## 10. 상태 배지 · 색상

| Status | 색 | 아이콘 |
|---|---|---|
| draft | gray | ✏️ |
| review_1 | blue | 👀 |
| review_2 | indigo | 👀 |
| review_3 | purple | 👀 |
| approved | green | ✅ |
| neis_copied | teal | 📋 |
| correction_pending | orange | ⚠️ |

피드백 severity (UX 톤은 "감시"가 아닌 "검토 조력"):

| Severity | 색 | 아이콘 | 카피 예 |
|---|---|---|---|
| block | red | ⛔ | "훈령상 기재 불가 항목입니다" |
| warn | orange | ⚠️ | "확인해 주세요" |
| info | blue | 💡 | "개선 제안" |

- 배지 카피는 "위반 N건"보다 "개선 제안 N건" 선호
- 전체 결과 요약은 "검토 완료: 제안 3건" 등 비판단적 어조
- 상세 톤 가이드는 별도 `docs/UX_TONE.md`로 관리 (M9에서 작성)

---

## 11. 상태 관리

| 도구 | 용도 |
|---|---|
| **TanStack Query** | 서버 상태 (records, reviews, feedback) |
| **Zustand** | 전역 UI 상태 (선택된 학생, 에디터 사이드패널 열림 등) |
| **React Hook Form + Zod** | 폼 유효성 (로그인, 학교 설정, 사전 편집) |
| **next-intl** | 한국어 기본, 영어 번역 선택(교육청 시연용) |

---

## 12. 실시간(SSE)

- `EventSource('/api/sse/records/{id}/feedback')` — Stage 5 완료 푸시
- `EventSource('/api/sse/reviews/assigned')` — 새 결재 요청 푸시

---

## 13. 접근성·i18n

- 한국어 우선, 한자·외국어 최소화 (정책과 일치)
- 키보드 단축키: `Ctrl+S` 저장 (브라우저 기본 저장 동작을 `event.preventDefault()`로 차단), `Ctrl+Enter` 제출
- 스크린 리더 대응: Radix UI 기본 aria
- 색맹 고려: severity는 색 + 아이콘 병기

---

## 14. 테스트

- **Vitest**: 유틸 · 훅 · 폼 스키마
- **Testing Library**: 컴포넌트 단위
- **Playwright** (별도): 골든 패스 E2E
  - 로그인 → 에디터 → 저장 → 피드백 확인 → 제출
  - 금지어 포함 시 제출 실패
  - 결재자 승인·반려
  - NEIS 복사 (네트워크 인터셉트)

---

## 15. 배포

- `next build && next start` (Node 20)
- 교내망: Docker + NGINX reverse proxy
- 교육청 폐쇄망: 정적 빌드 + 백엔드만 교내 서버
- 빌드 시 `NEXT_PUBLIC_API_BASE` 등 환경변수로 스위칭
