# memory/

The memory package defines the session state data model and the logic that keeps it up to date.

## Sub-packages

### `schemas/`

Pydantic models that describe the coaching session:

| Module | Key exports |
|---|---|
| `session_state.py` | `SessionState` — root state object stored per user |
| `coach_types.py` | `CoachResponseAnalysis`, `CoachingPhase`, `QuestionType` |

`CoachResponseAnalysis` is the Structured Output model returned by the LLM. It enforces Chain of Thought: the LLM must fill in `analysis_summary` before writing `ai_response`.

### `logic/`

| Module | Key exports |
|---|---|
| `manager.py` | `MemoryManager` — creates, reads, and mutates `SessionState` |
| `compressor.py` | (reserved for future history compression) |

`MemoryManager` never mutates a `SessionState` in place; it always calls `model_copy(deep=True)` first, preserving immutability of the caller's reference.

### `templates/`

Jinja2 templates rendered by `SystemPrompter`:

| Template | Purpose |
|---|---|
| `main.j2` | Active system prompt — injects user profile, session phase, and conversation context |
| `core.j2`, `episodic.j2`, `semantic.j2`, `working.j2` | Reserved partial templates for future multi-section prompt assembly |
