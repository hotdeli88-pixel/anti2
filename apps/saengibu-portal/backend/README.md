# saengibu-portal backend

FastAPI 백엔드. `saengibu-portal-backend` uv workspace member.

## 실행

```bash
# 루트에서
uv sync

# 로컬 개발
cp apps/saengibu-portal/backend/.env.example apps/saengibu-portal/backend/.env
# .env의 JWT_SECRET / DATABASE_URL / API 키 채우기

uv run --package saengibu-portal-backend uvicorn app.main:app --reload \
  --app-dir apps/saengibu-portal/backend
```

## 구조

- `app/api/` — REST 라우터
- `app/core/` — 설정·인증·RBAC·로깅
- `app/domain/` — 도메인 모델
- `app/services/` — AI 파이프라인·Byte 카운터·중복 검출·NEIS 정규화
- `app/workers/` — Celery 태스크
- `alembic/` — 마이그레이션
- `tests/` — pytest (unit/integration)

## 설계 문서

- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- [../docs/ERD.md](../docs/ERD.md)
- [../docs/API.md](../docs/API.md)
- [../docs/AI_PIPELINE.md](../docs/AI_PIPELINE.md)

## 테스트

```bash
uv run --package saengibu-portal-backend pytest
```

## 린트

```bash
uv run --package saengibu-portal-backend ruff check .
uv run --package saengibu-portal-backend ruff format .
uv run --package saengibu-portal-backend mypy app
```
