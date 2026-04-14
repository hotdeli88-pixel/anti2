.PHONY: help up down db migrate seed backend frontend

help:
	@echo "saengibu-portal make targets"
	@echo "  up         docker-compose (postgres, redis)"
	@echo "  down       stop compose"
	@echo "  migrate    alembic upgrade head"
	@echo "  seed       demo-seed for 성당중학교"
	@echo "  backend    run FastAPI with reload"
	@echo "  frontend   run Next.js dev server"

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
	cd frontend && pnpm dev
