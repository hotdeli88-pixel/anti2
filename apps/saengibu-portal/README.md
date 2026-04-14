# saengibu-portal — 학교생활기록부 포털

> 교사가 먼저 쓰고 → AI가 피드백. 훈령 제555호·2026 기재요령 준수.

## 개요

한국 중·고등학교 교사의 학교생활기록부(이하 **생기부**) 작성·검토·NEIS 입력 전 과정을 지원하는 통합 포털.

- **AI는 대신 쓰지 않는다.** 교사 초안을 검수하는 피드백 엔진.
- **결정적 검증(Byte/금지어/문체)은 비-LLM**, 맥락 판단(과장·개별성)만 LLM.
- **1검 → 2검 → 3검 → NEIS 복사** 워크플로우 네이티브 지원.
- **훈령 제555호 제3조·제16조·2026 "AI 활용 유의사항"** 준수.

## 기술 스택

| 레이어 | 선택 | 근거 |
|---|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript | SSR·Edge, 교내망 배포 용이 |
| Backend | FastAPI 0.115+ · Python 3.11 | uv workspace 편입, Pydantic v2 |
| DB | PostgreSQL 16 + pgvector 0.7 | 임베딩 + 메타 JOIN 단일 엔진 |
| 벡터 | pgvector (실시간) · FAISS (배치) | 이중 트랙 |
| 임베딩 | `jhgan/ko-sroberta-multitask` | 한국어 KLUE-STS 84.77 |
| 토큰화 | `kiwipiepy` | 2024+ 업계 표준 |
| 인증 | OAuth2 + JWT · casbin 정책 | 학교 조직도 RBAC/ABAC |
| 큐 | Celery + Redis | 야간 배치 중복 검출 |

## 디렉토리

```text
apps/saengibu-portal/
├── backend/              FastAPI 서비스
│   ├── app/
│   │   ├── api/          라우터
│   │   ├── core/         설정·인증·RBAC
│   │   ├── domain/       도메인 모델 (교사·학생·기록·검토)
│   │   ├── services/
│   │   │   ├── ai/       6단계 피드백 파이프라인
│   │   │   ├── byte/     NEIS CP949 Byte 카운터
│   │   │   ├── duplicate/유사도·중복 검출
│   │   │   └── neis/     복사 최적화 (정규화·변환)
│   │   └── workers/      Celery tasks
│   └── pyproject.toml
├── frontend/             Next.js 앱
│   ├── app/              App Router 페이지
│   ├── components/       공용 컴포넌트
│   ├── features/         영역별 에디터 (행종·창체·세특 등)
│   └── package.json
└── docs/                 설계 문서 (ARCHITECTURE·ERD·API·AI_PIPELINE·RBAC·WORKFLOW·FRONTEND)
```

## 시작

```bash
# 루트에서
uv sync                                     # Python 워크스페이스 동기화

# 백엔드
uv run --package saengibu-portal-backend uvicorn app.main:app --reload

# 프론트엔드
cd apps/saengibu-portal/frontend
pnpm install
pnpm dev
```

## 문서 맵

- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — C4 레벨 1~2
- [ERD.md](./docs/ERD.md) — 데이터 모델
- [API.md](./docs/API.md) — FastAPI 엔드포인트
- [FRONTEND.md](./docs/FRONTEND.md) — 탭·페이지·컴포넌트 구조
- [AI_PIPELINE.md](./docs/AI_PIPELINE.md) — 6단계 피드백 엔진
- [RBAC.md](./docs/RBAC.md) — 학교 조직도 권한 모델
- [WORKFLOW_1_2_3_REVIEW.md](./docs/WORKFLOW_1_2_3_REVIEW.md) — 검토 상태 머신

## 법적·제도적 근거

- 교육부훈령 제555호 「학교생활기록 작성 및 관리지침」
- 2026학년도 학교생활기록부 기재요령(중·고)
- 초·중등교육법 제25조, 제9장
- 개인정보보호법 §15·§18 (업무 관련성)

## 커밋 규칙

Conventional Commits, 범위는 `saengibu-portal`:

```
feat(saengibu-portal): Byte 카운터 CP949 지원
fix(saengibu-portal): 행종 300B 임계 계산 오류
docs(saengibu-portal): AI_PIPELINE 6단계 보강
```
