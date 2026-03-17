# Life Coach System

An AI-powered life coaching application with a Gradio web UI. The coach conducts structured coaching conversations using an OpenAI-compatible LLM with Instructor for structured output (Chain of Thought via Pydantic models). Supports multiple users with independent per-user session state and includes an LLM-as-Judge evaluation system against 14 leaderboard criteria.

---

## Architecture

### Message flow

```mermaid
flowchart TD
    User["User (browser)"]
    AppPy["dev_ui.py\n(Dev UI)"]
    CoachAgent["engine.CoachAgent"]
    SystemPrompter["engine.SystemPrompter\n(Jinja2 templates)"]
    LLM["LLM API\n(OpenAI + Instructor)"]
    MemoryManager["memory.MemoryManager"]
    SessionState["memory.SessionState\n(Pydantic model)"]
    Persistence["persistence.PersistenceBackend\n(InMemory / SQL)"]

    User -->|"user message"| AppPy
    AppPy -->|"respond(msg, state)"| CoachAgent
    CoachAgent -->|"add_user_message"| MemoryManager
    CoachAgent -->|"build_system_prompt"| SystemPrompter
    SystemPrompter -->|"rendered prompt"| CoachAgent
    CoachAgent -->|"call_llm(messages, CoachResponseAnalysis)"| LLM
    LLM -->|"structured CoachResponseAnalysis"| CoachAgent
    CoachAgent -->|"update_from_output"| MemoryManager
    MemoryManager -->|"updated SessionState"| SessionState
    CoachAgent -->|"ai_response + state"| AppPy
    AppPy -->|"save(user_id, state)"| Persistence
    AppPy -->|"response"| User
```

### Evaluation flow

```mermaid
flowchart TD
    LC["leaderboard_card_coach.md"]
    Parser["utils.parse_leaderboard_card"]
    Filter["utils.filter_checks_by_priority"]
    EvalModel["utils.create_evaluation_model\n(dynamic Pydantic model)"]
    EvalLLM["LLM API (judge)"]
    Results["format_evaluation_results"]
    UI["Gradio Leaderboard tab"]

    LC -->|"markdown"| Parser
    Parser -->|"List[CheckDefinition]"| Filter
    Filter -->|"filtered checks"| EvalModel
    EvalModel -->|"DynamicEvaluationResult model"| EvalLLM
    EvalLLM -->|"structured verdict"| Results
    Results -->|"formatted markdown"| UI
```

### Diagram narrative

**Message flow:** The user sends a message through the dev UI (`dev_ui.py`). `CoachAgent.respond()` first adds the message to the conversation history via `MemoryManager`, then builds a Jinja2 system prompt with current session context. The prompt and recent history are sent to the LLM via `call_llm()`, which returns a structured `CoachResponseAnalysis` model (Chain of Thought enforced). `MemoryManager.update_from_output()` maps the structured response back into `SessionState` (phase, emotions, question counters). The final text response and updated state are returned to the UI, which persists the state.

**Evaluation flow:** The user triggers evaluation in the Leaderboard tab. `parse_leaderboard_card()` reads the 14 criteria from the markdown file; `filter_checks_by_priority()` narrows the list. `create_evaluation_model()` dynamically builds a Pydantic model with two fields per criterion (`{id}_reasoning` + `{id}_passed`). The judge LLM evaluates the conversation against all criteria and returns a structured verdict, which is formatted as markdown for display.

---

## Persistence

Session state is pluggable via the `PersistenceBackend` protocol. The backend is selected by the `DATABASE_URL` environment variable:

| `DATABASE_URL` | Backend | Use case |
|---|---|---|
| *(not set)* | `InMemoryBackend` | Development — state lost on restart |
| `sqlite:///sessions.db` | `SqlBackend` (SQLite) | Local dev with persistence |
| `postgresql://user:pass@host/db` | `SqlBackend` (PostgreSQL) | Production | <!-- pragma: allowlist secret -->

For PostgreSQL, install the driver extra: `uv pip install life-coach-system[postgres]`.

The SQL backend stores each user's `SessionState` as a JSON blob in a single `sessions` table (auto-created on startup).

---

## How to run

### Client UI (FastAPI + React)

```bash
# 1. Build the frontend (one-time, or after frontend changes)
cd frontend && npm install && npm run build && cd ..

# 2. Start the API server (serves both API and built frontend)
uv run life-coach-api
```

The app is available at `http://localhost:8000`.

#### Frontend development

For hot-reload during frontend work, run the API and Vite dev server separately:

```bash
# Terminal 1 — API backend
uv run life-coach-api

# Terminal 2 — Vite dev server (proxies /api to :8000)
cd frontend && npm run dev
```

The Vite dev server runs at `http://localhost:5173`.

### Docker

```bash
docker build -t life-coach-system .
docker run --rm -p 8000:8000 --env-file .env life-coach-system
```

The app is available at `http://localhost:8000`. Environment variables (API keys, model config) are injected at runtime via `--env-file` or `-e` flags — nothing is baked into the image.

For persistent storage inside Docker, mount a volume for SQLite or point to an external PostgreSQL:

```bash
# SQLite with a volume
docker run --rm -p 8000:8000 --env-file .env \
  -e DATABASE_URL=sqlite:////data/sessions.db \
  -v life-coach-data:/data life-coach-system

# PostgreSQL
docker run --rm -p 8000:8000 --env-file .env \
  -e DATABASE_URL=postgresql://user:pass@db-host:5432/life_coach \  # pragma: allowlist secret
  life-coach-system
```

### Dev UI (Gradio)

Gradio is a dev-only dependency. Install dev dependencies first:

```bash
make install-dev        # or: uv sync --group dev
uv run python dev_ui.py
```

The Gradio dev UI starts at `http://0.0.0.0:8080`. This is a development/testing interface — uses in-memory state and exposes evaluation tooling. Not for production use.

### Tests

```bash
uv run pytest
```

### Linting and formatting

```bash
uv run ruff check src/ && uv run ruff format --check src/
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | API key for your OpenAI-compatible endpoint |
| `OPENAI_BASE_URL` | Base URL of the LLM API |
| `MODEL_NAME` | Full model identifier (e.g. `gpt-4o-mini-2024-07-18`) |
| `DATABASE_URL` | DB connection string (omit for in-memory). SQLite: `sqlite:///sessions.db`, PostgreSQL: `postgresql://user:pass@host/db` | <!-- pragma: allowlist secret -->
| `DEBUG` | Set to `false` in production for JSON logging |

### Authentication (OAuth)

| Variable | Description |
|---|---|
| `JWT_SECRET` | Secret key for signing JWT tokens (change from default in production!) |
| `JWT_EXPIRY_MINUTES` | Token lifetime in minutes (default: 10080 = 1 week) |
| `MAX_ANONYMOUS_MESSAGES` | Free messages before login required (default: 5) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials ([console](https://console.cloud.google.com/apis/credentials)) |
| `TWITTER_CLIENT_ID` / `TWITTER_CLIENT_SECRET` | Twitter/X OAuth 2.0 credentials ([portal](https://developer.twitter.com/en/portal/projects)) |
| `FACEBOOK_CLIENT_ID` / `FACEBOOK_CLIENT_SECRET` | Facebook OAuth credentials ([apps](https://developers.facebook.com/apps/)) |
| `OAUTH_REDIRECT_BASE_URL` | Base URL for OAuth callbacks (default: `http://localhost:8000`) |

OAuth is optional — the app works without it, but anonymous users are limited to `MAX_ANONYMOUS_MESSAGES` messages per session. Configure at least one provider for production use.

#### Google OAuth setup

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** (application type: Web application)
3. Under **Authorized redirect URIs**, add: `http://localhost:8000/api/v1/auth/callback/google`
4. Copy the Client ID and Client Secret into your `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id-here
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

#### Twitter/X OAuth setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/projects)
2. Create an app with **OAuth 2.0** enabled (User authentication → Type: Web App)
3. Set the callback URL to: `http://localhost:8000/api/v1/auth/callback/twitter`
4. Copy credentials into `.env`:
   ```
   TWITTER_CLIENT_ID=your-client-id-here
   TWITTER_CLIENT_SECRET=your-client-secret-here
   ```

#### Facebook OAuth setup

1. Go to [Facebook Developers → Apps](https://developers.facebook.com/apps/)
2. Create an app, go to **Facebook Login → Settings**
3. Add `http://localhost:8000/api/v1/auth/callback/facebook` to **Valid OAuth Redirect URIs**
4. Copy credentials into `.env`:
   ```
   FACEBOOK_CLIENT_ID=your-app-id-here
   FACEBOOK_CLIENT_SECRET=your-app-secret-here
   ```

**Important:** Only providers with credentials configured in `.env` will appear as available login options. If a provider's `CLIENT_ID` is empty, the sign-in button will redirect back with an "unsupported provider" error. For local development, configure at least one provider (Google is the easiest to set up).
