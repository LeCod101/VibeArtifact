.PHONY: install dev dev-infra dev-api dev-worker dev-web lint test gate stop

# ── Install ──
install:
	uv sync --all-packages
	cd apps/web && pnpm install

# ── Infrastructure ──
dev-infra:
	docker compose -f infra/compose/docker-compose.dev.yml up -d

stop:
	docker compose -f infra/compose/docker-compose.dev.yml down

# ── Dev (individual services) ──
dev-api:
	cd services/api && uv run uvicorn api_app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	cd services/worker && uv run celery -A worker_app.celery_app worker --loglevel=info

dev-web:
	cd apps/web && pnpm dev

# ── Dev (all) ──
dev: dev-infra
	@echo "Infrastructure started. Run these in separate terminals:"
	@echo "  make dev-api"
	@echo "  make dev-worker"
	@echo "  make dev-web"

# ── Lint ──
lint:
	uv run ruff check .
	cd apps/web && pnpm lint

# ── Test ──
test:
	uv run pytest
	cd apps/web && pnpm build

# ── Gate (all checks) ──
gate: lint test
	@echo "All checks passed."
