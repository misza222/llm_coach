# engine/

The engine package is the orchestration layer that drives LLM interactions.

## Modules

| Module | Responsibility |
|---|---|
| `client.py` | Singleton OpenAI + Instructor client; `call_llm()` wraps all API calls |
| `coach.py` | `CoachAgent` — the main agent; assembles prompt, calls LLM, updates state |
| `prompter.py` | `SystemPrompter` — renders Jinja2 templates into system prompts |
| `prompts.py` | (reserved for static prompt constants) |

## Design notes

- `get_llm_client()` is `@lru_cache`-decorated, so the patched OpenAI client is created once per process.
- `call_llm()` raises `LLMError` (from `life_coach_system.exceptions`) on any API failure, preserving the original traceback with `raise X from Y`.
- `CoachAgent.respond()` is the single public entry point; it enforces the Chain-of-Thought pattern via `CoachResponseAnalysis` structured output.
- `SystemPrompter` uses `jinja2.Environment` with `FileSystemLoader` pointing at `memory/templates/`.
