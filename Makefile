.PHONY: help install install-dev frontend-install frontend-build \
       api dev dev-ui dev-frontend \
       test lint format typecheck check \
       docker-build docker-run \
       clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install: ## Install Python dependencies
	uv sync

install-dev: ## Install Python + dev dependencies
	uv sync --group dev
	uv run pre-commit install

frontend-install: ## Install frontend (npm) dependencies
	cd frontend && npm install

frontend-build: frontend-install ## Build React frontend for production
	cd frontend && npm run build

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

api: frontend-build ## Start FastAPI server (serves built frontend)
	uv run life-coach-api

dev: ## Start FastAPI server (no frontend build)
	uv run life-coach-api

dev-ui: ## Start Gradio dev UI (dev/testing only)
	uv run python dev_ui.py

dev-frontend: ## Start Vite dev server with hot-reload (proxy to :8000)
	cd frontend && npm run dev

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

test: ## Run all tests
	uv run pytest

lint: ## Run ruff linter
	uv run ruff check src/ tests/

format: ## Auto-format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck: ## Run mypy type checker
	uv run mypy src/

check: lint typecheck test ## Run lint + typecheck + tests

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-build: ## Build Docker image
	docker build -t life-coach-system .

docker-run: ## Run Docker container (pass OPENAI_API_KEY etc. via --env-file)
	docker run --rm -p 8000:8000 --env-file .env life-coach-system

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts and caches
	rm -rf frontend/dist frontend/node_modules/.vite
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find src tests -type d -name __pycache__ -exec rm -rf {} +
