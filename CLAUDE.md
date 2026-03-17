# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered life coaching application with a Gradio web UI. A coach named "Jacek" conducts structured coaching conversations using OpenAI-compatible LLM with Instructor for structured output (Chain of Thought via Pydantic models). Multi-user support with per-user session state. Includes LLM-as-Judge evaluation against 14 leaderboard criteria.

## Running

```bash
uv run python dev_ui.py  # Gradio dev UI on 0.0.0.0:8080
```

## Architecture

```
User Message → dev_ui.py (Dev UI) → CoachAgent.respond()
  → MemoryManager adds message to history
  → SystemPrompter builds Jinja2 prompt (memory/templates/main.j2)
  → call_llm() with response_model=CoachResponseAnalysis (structured output)
  → MemoryManager.update_from_output() updates SessionState
  → InMemoryBackend.save() persists state
  → UI displays ai_response
```

**Key layers:**
- `engine/` — LLM client (OpenAI + Instructor), CoachAgent orchestration, Jinja2 prompt builder
- `memory/schemas/` — Pydantic models: `SessionState` (root state), `CoachResponseAnalysis` (structured LLM output with CoT), `CoachingPhase`/`QuestionType` enums
- `memory/logic/` — `MemoryManager` updates state from LLM output, manages conversation history window
- `memory/templates/` — Jinja2 templates for system prompts (`main.j2` is the active one)
- `persistence/` — Abstract `PersistenceBackend` (ABC) with `InMemoryBackend` implementation
- `utils/` — Leaderboard markdown parser + LLM-as-Judge evaluator (dynamically creates Pydantic models from parsed criteria)
- `skills/` — Stub modules (action, context, exploration, safety) for future expansion
- `dev_ui.py` — Gradio dev UI with global singletons (coach, storage, memory_manager); in-memory state, not for production

**Evaluation flow:** `leaderboard_card_coach.md` → `parse_leaderboard_card()` → `create_evaluation_model()` (dynamic Pydantic) → `call_llm()` → formatted results

## Configuration

`src/life_coach_system/config.py` uses `pydantic-settings` `BaseSettings` (reads from `.env`). Key settings: `model_name`, `temperature` (0.0), `max_history_messages` (10), `coach_name` ("Jack"). Copy `.env.example` → `.env` to configure.
