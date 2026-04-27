# anti2 Monorepo

`hotdeli88-pixel/anti2` 모노레포. `uv` workspace 기반으로 여러 애플리케이션과 공용 패키지를 단일 저장소에서 관리합니다.

## 구조

```text
anti2/
├── apps/                    # 실행 가능한 애플리케이션
│   └── saengibu-portal/     # 학교생활기록부 포털 (Next.js + FastAPI)
│       ├── backend/         # FastAPI 서비스 (uv workspace member)
│       ├── frontend/        # Next.js 15 App Router
│       └── docs/            # 설계 문서 (ARCHITECTURE·ERD·API·AI_PIPELINE·RBAC·WORKFLOW·FRONTEND)
├── packages/                # 공용 라이브러리/모듈
├── dev/active/              # 진행 중 프로젝트 플랜·컨텍스트·태스크
├── pyproject.toml           # uv workspace 루트
├── .python-version
└── MONOREPO_GUIDELINES.md   # 상세 운영 지침
```

## 활성 프로젝트

- **[saengibu-portal](./apps/saengibu-portal/)** — 학교생활기록부 포털 (훈령 제555호·2026 기재요령 준수). 플랜: [`dev/active/saengibu-portal-plan.md`](./dev/active/saengibu-portal-plan.md)

## 시작

```bash
uv sync
```

상세 지침은 [MONOREPO_GUIDELINES.md](./MONOREPO_GUIDELINES.md) 참조.
