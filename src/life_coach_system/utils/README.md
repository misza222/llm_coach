# utils/

Utility modules for leaderboard parsing and LLM-as-Judge evaluation.

## Modules

### `leaderboard_parser.py`

Parses `leaderboard_card_coach.md` into structured `CheckDefinition` objects.

Key functions:
- `parse_leaderboard_card(filepath)` — reads the markdown file and returns a `List[CheckDefinition]`
- `filter_checks_by_priority(checks, priority)` — returns a filtered list (`"MUST-HAVE"`, `"SHOULD-HAVE"`, or `"ALL"`)

### `evaluator.py`

LLM-as-Judge evaluation against leaderboard criteria.

Key functions:
- `create_evaluation_model(checks)` — dynamically builds a Pydantic model with `{LC_XXX_reasoning, LC_XXX_passed}` fields for each check
- `evaluate_conversation(conversation_history, checks)` — sends the conversation to the LLM judge and returns structured results
- `format_evaluation_results(eval_result)` — formats the results as Gradio-friendly markdown

## How the dynamic model works

`pydantic.create_model` is called at evaluation time with field names derived from the check IDs (e.g. `LC-001` → `LC_001_reasoning`, `LC_001_passed`). This allows the evaluation model to adapt to any subset of criteria without code changes.
