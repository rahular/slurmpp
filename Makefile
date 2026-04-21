.PHONY: dev build test lint clean setup

# ─── Development ──────────────────────────────────────────────────────────────
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Run both in parallel (requires tmux or two terminals)
dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals."
	@echo "Or use: docker compose -f docker-compose.yml -f docker-compose.dev.yml up"

# ─── Production ───────────────────────────────────────────────────────────────
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# ─── Setup ────────────────────────────────────────────────────────────────────
setup:
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it before starting")
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

setup-admin:
	@read -p "Admin username: " u; read -sp "Password: " p; echo; \
	cd backend && python -m app.cli create-admin $$u $$p

# ─── Tests ────────────────────────────────────────────────────────────────────
test:
	cd backend && pytest tests/ -v

test-coverage:
	cd backend && pytest tests/ --cov=app --cov-report=term-missing

# ─── Lint / Type-check ────────────────────────────────────────────────────────
lint:
	cd backend && python -m mypy app/ --ignore-missing-imports
	cd frontend && npm run typecheck

# ─── Clean ────────────────────────────────────────────────────────────────────
clean:
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find backend -name "*.pyc" -delete 2>/dev/null; true
	rm -f backend/slurmpp.db
	docker compose down -v 2>/dev/null; true
