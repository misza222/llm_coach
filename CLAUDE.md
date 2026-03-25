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
- `auth/` — OAuth social login (Google, Twitter, Facebook) via Authlib, JWT tokens (PyJWT), `UserRepository` for user/OAuth account persistence, anonymous message counting
- `engine/` — LLM client (OpenAI + Instructor), CoachAgent orchestration, Jinja2 prompt builder
- `memory/schemas/` — Pydantic models: `SessionState` (root state), `CoachResponseAnalysis` (structured LLM output with CoT), `CoachingPhase`/`QuestionType` enums, `UserProfile`/`CompletedSessionSummary` (cross-session memory)
- `memory/logic/` — `MemoryManager` updates state from LLM output, manages conversation history window, builds cross-session context and materializes user profiles on session completion
- `memory/templates/` — Jinja2 templates for system prompts (`main.j2` is the active one)
- `persistence/` — `PersistenceBackend` Protocol with `InMemoryBackend` and `SqlBackend` (SQLite/PostgreSQL) implementations. `tables.py` defines shared SQLAlchemy table definitions (sessions, users, oauth_accounts, anonymous_message_counts, user_profiles).
- `utils/` — Leaderboard markdown parser + LLM-as-Judge evaluator (dynamically creates Pydantic models from parsed criteria)
- `skills/` — Stub modules (action, context, exploration, safety) for future expansion
- `dev_ui.py` — Gradio dev UI with global singletons (coach, storage, memory_manager); in-memory state, not for production

**API endpoints:**
- `GET /api/v1/health` — liveness check
- `POST /api/v1/chat` — send message, get coach reply (`ChatRequest` → `ChatResponse`). Anonymous users limited to N messages (configurable via `MAX_ANONYMOUS_MESSAGES`).
- `GET /api/v1/sessions/{user_id}` — load session state
- `POST /api/v1/sessions/{user_id}/reset` — clear session
- `GET /api/v1/sessions/{user_id}/export` — download session JSON
- `GET /api/v1/auth/login/{provider}` — redirect to OAuth provider (Google, Twitter, Facebook)
- `GET /api/v1/auth/callback/{provider}` — OAuth callback, creates/finds user, sets JWT cookie
- `GET /api/v1/auth/me` — return auth status + user info
- `POST /api/v1/auth/logout` — clear JWT cookie

**Frontend:** React + TypeScript + Tailwind in `frontend/`. Vite dev server proxies `/api` to `:8000`. Built output in `frontend/dist/` is served by FastAPI as static files.

**Evaluation flow:** `leaderboard_card_coach.md` → `parse_leaderboard_card()` → `create_evaluation_model()` (dynamic Pydantic) → `call_llm()` → formatted results

## Configuration

`src/life_coach_system/config.py` uses `pydantic-settings` `BaseSettings` (reads from `.env`). Key settings: `model_name`, `temperature` (0.0), `max_history_messages` (10), `max_past_sessions` (3), `coach_name` ("Jack"), `database_url` (None = in-memory, `sqlite:///sessions.db` for dev, `postgresql://...` for prod). Copy `.env.example` → `.env` to configure. For PostgreSQL, install with `pip install life-coach-system[postgres]`.

**Auth settings:** `jwt_secret`, `jwt_algorithm` (HS256), `jwt_expiry_minutes` (10080 = 1 week), `max_anonymous_messages` (5), OAuth client IDs/secrets for Google/Twitter/Facebook, `oauth_redirect_base_url` (http://localhost:8000). JWT stored in httpOnly cookie. Anonymous users get N free messages before login is required; their session migrates to the authenticated account on sign-in.
