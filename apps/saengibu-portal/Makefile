.PHONY: help install check test typecheck build up down db migrate seed backend frontend verify-standards validate-jsonl

help:
	@echo "saengibu-portal make targets"
	@echo "  install    install backend/frontend deps from lockfiles"
	@echo "  check      run backend unit tests + frontend typecheck"
	@echo "  test       run backend unit tests"
	@echo "  typecheck  run frontend TypeScript check"
	@echo "  build      build frontend"
	@echo "  up         docker-compose (postgres, redis)"
	@echo "  down       stop compose"
	@echo "  migrate    alembic upgrade head"
	@echo "  seed       demo-seed for 성당중학교"
	@echo "  backend    run FastAPI with reload"
	@echo "  frontend   run Next.js dev server"

install:
	cd ../.. && uv sync --frozen --package saengibu-portal-backend --extra dev
	cd frontend && corepack enable && corepack prepare pnpm@9.15.9 --activate && corepack pnpm install --frozen-lockfile

check: test typecheck

test:
	cd backend && uv run --frozen --no-editable --package saengibu-portal-backend --extra dev pytest tests/unit -q

typecheck:
	cd frontend && corepack pnpm typecheck

build:
	cd frontend && corepack pnpm build

up:
	docker compose -f docker-compose.dev.yml up -d
	@echo "Postgres on 5432, Redis on 6379"

down:
	docker compose -f docker-compose.dev.yml down

migrate:
	cd backend && uv run --package saengibu-portal-backend alembic upgrade head

seed:
	cd backend && uv run --package saengibu-portal-backend saengibu demo-seed

backend:
	cd backend && uv run --package saengibu-portal-backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && corepack pnpm dev

verify-standards:
	cd backend && uv run --package saengibu-portal-backend python ../scripts/verify_coverage.py --out ../data/reports/coverage_$$(date +%F).md

validate-jsonl:
	@for f in data/processed/middle_*.jsonl; do \
		echo "=== $$f ==="; \
		uv run --package saengibu-portal-backend python scripts/validate.py "$$f"; \
	done
