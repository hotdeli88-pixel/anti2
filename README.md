# anti2 Monorepo

`hotdeli88-pixel/anti2` 모노레포. `uv` workspace 기반으로 여러 애플리케이션과 공용 패키지를 단일 저장소에서 관리합니다.

## 구조

```text
anti2/
├── apps/                    # 실행 가능한 애플리케이션
│   └── saengibu-portal/     # 학교생활기록부 포털 (Next.js + FastAPI) — 예정
├── packages/                # 공용 라이브러리/모듈
├── pyproject.toml           # uv workspace 루트
├── .python-version
└── MONOREPO_GUIDELINES.md   # 상세 운영 지침
```

## 시작

```bash
uv sync
```

상세 지침은 [MONOREPO_GUIDELINES.md](./MONOREPO_GUIDELINES.md) 참조.
