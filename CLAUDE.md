# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered life coaching application with a Gradio web UI. A coach named "Jacek" conducts structured coaching conversations using OpenAI-compatible LLM with Instructor for structured output (Chain of Thought via Pydantic models). Multi-user support with per-user session state. Includes LLM-as-Judge evaluation against 14 leaderboard criteria.

## Running

```bash
uv run life-coach-api   # FastAPI + React UI on localhost:8000
uv run python dev_ui.py # Gradio dev UI on 0.0.0.0:8080 (dev-only)
```

## Architecture

```
User Message → dev_ui.py (Dev UI) → CoachAgent.respond()
  → MemoryManager adds message to history
  → SystemPrompter builds Jinja2 prompt (memory/templates/main.j2)
  → call_llm() with response_model=CoachResponseAnalysis (structured output)
  → MemoryManager.update_from_output() updates SessionState
  → PersistenceBackend.save() persists state (InMemory, SQLite, or PostgreSQL)
  → UI displays ai_response
```

**Key layers:**
- `api/` — FastAPI REST API (`create_app()` factory, routes, schemas, DI via `dependencies.py`). Serves React frontend as static files from `frontend/dist/`.
- `engine/` — LLM client (OpenAI + Instructor), CoachAgent orchestration, Jinja2 prompt builder
- `memory/schemas/` — Pydantic models: `SessionState` (root state), `CoachResponseAnalysis` (structured LLM output with CoT), `CoachingPhase`/`QuestionType` enums
- `memory/logic/` — `MemoryManager` updates state from LLM output, manages conversation history window
- `memory/templates/` — Jinja2 templates for system prompts (`main.j2` is the active one)
- `persistence/` — `PersistenceBackend` Protocol with `InMemoryBackend` and `SqlBackend` (SQLite/PostgreSQL) implementations
- `utils/` — Leaderboard markdown parser + LLM-as-Judge evaluator (dynamically creates Pydantic models from parsed criteria)
- `skills/` — Stub modules (action, context, exploration, safety) for future expansion
- `dev_ui.py` — Gradio dev UI with global singletons (coach, storage, memory_manager); in-memory state, not for production

**API endpoints:**
- `GET /api/v1/health` — liveness check
- `POST /api/v1/chat` — send message, get coach reply (`ChatRequest` → `ChatResponse`)
- `GET /api/v1/sessions/{user_id}` — load session state
- `POST /api/v1/sessions/{user_id}/reset` — clear session
- `GET /api/v1/sessions/{user_id}/export` — download session JSON

**Frontend:** React + TypeScript + Tailwind in `frontend/`. Vite dev server proxies `/api` to `:8000`. Built output in `frontend/dist/` is served by FastAPI as static files.

**Evaluation flow:** `leaderboard_card_coach.md` → `parse_leaderboard_card()` → `create_evaluation_model()` (dynamic Pydantic) → `call_llm()` → formatted results

## Configuration

`src/life_coach_system/config.py` uses `pydantic-settings` `BaseSettings` (reads from `.env`). Key settings: `model_name`, `temperature` (0.0), `max_history_messages` (10), `coach_name` ("Jack"), `database_url` (None = in-memory, `sqlite:///sessions.db` for dev, `postgresql://...` for prod). Copy `.env.example` → `.env` to configure. For PostgreSQL, install with `pip install life-coach-system[postgres]`.
