# Osool — top-level developer commands.
#
# Run `make` (no args) to see this list.
# Most targets assume you are at the Osool-Platform/ root.

.PHONY: help infra backend frontend dev migrate seed test test-backend test-frontend lint stop clean

help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

infra:  ## Start Postgres + Redis via Docker.
	docker compose up -d postgres redis

stop:  ## Stop Docker services.
	docker compose down

backend:  ## Run the FastAPI backend on :8000.
	cd backend && uvicorn app.main:app --reload

frontend:  ## Run the Next.js frontend on :3000.
	cd web && npm run dev

migrate:  ## Apply pending Alembic migrations.
	cd backend && alembic upgrade head

seed:  ## Ingest property data into pgvector (needs OPENAI_API_KEY + Supabase).
	cd backend && python ingest_data.py

test: test-backend test-frontend  ## Run all tests.

test-backend:  ## Run pytest suite.
	cd backend && pytest

test-frontend:  ## Run Playwright e2e (visualization config).
	cd web && npm run test:e2e:viz-fullscreen

lint:  ## Lint frontend (backend has no linter wired yet).
	cd web && npm run lint

clean:  ## Remove Python bytecode and Next.js build artefacts.
	cd backend && python -m compileall -q app/
	cd web && rm -rf .next
