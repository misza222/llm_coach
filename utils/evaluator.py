# -*- coding: utf-8 -*-
"""
LLM-as-Judge Evaluator - dynamic model creation and evaluation.

Based on lesson 5.3 methodology using pydantic.create_model.
"""

from pydantic import BaseModel, Field, create_model
from typing import List, Type, Any, Dict
from .leaderboard_parser import CheckDefinition
from engine.client import get_llm_client
from config import Config


def create_evaluation_model(checks: List[CheckDefinition]) -> Type[BaseModel]:
    """
    Dynamically create Pydantic model for evaluation.

    For each check, create 2 fields:
    - {id}_reasoning: str (Chain of Thought with quoted dialog fragments)
    - {id}_passed: bool (Binary verdict)

    Args:
        checks: List of CheckDefinition to evaluate

    Returns:
        Dynamically created Pydantic model class

    Example:
        checks = [CheckDefinition(id="LC-001", ...)]
        Model = create_evaluation_model(checks)
        # Model has fields: LC_001_reasoning, LC_001_passed
    """
    fields = {}

    for check in checks:
        # Normalize ID: LC-001 -> LC_001 (pydantic field name)
        prefix = check.id.replace("-", "_")

        # Field 1: reasoning (Chain of Thought)
        fields[f"{prefix}_reasoning"] = (str, Field(
            ...,
            description=(
                f"Analysis for {check.id} ({check.title}). "
                f"Criterion: {check.description}. "
                f"IMPORTANT: Quote a specific dialog fragment as evidence, "
                f"or write 'No evidence in dialog' if the criterion does not appear."
            )
        ))

        # Field 2: passed (Binary verdict)
        fields[f"{prefix}_passed"] = (bool, Field(
            ...,
            description=(
                f"Binary verdict for {check.id}. "
                f"True if criterion is fully satisfied (all elements present). "
                f"False if an error, violation, or missing required element is detected."
            )
        ))

    # Create model dynamically
    return create_model("DynamicEvaluationResult", **fields)


def evaluate_conversation(
    conversation_history: List[dict],
    checks: List[CheckDefinition]
) -> Dict[str, Any]:
    """
    Evaluate conversation using LLM-as-Judge with structured output.

    Args:
        conversation_history: List of messages [{"role": "user", "content": "..."}, ...]
        checks: List of criteria to evaluate (already filtered by priority)

    Returns:
        Dict with:
        - results: List of {id, title, reasoning, passed}
        - summary: {passed_count, failed_count, total, score_pct}
        - priority: Priority group evaluated
    """
    if not checks:
        return {
            "error": "No checks provided for evaluation",
            "results": [],
            "summary": {}
        }

    if not conversation_history:
        return {
            "error": "No conversation to evaluate",
            "results": [],
            "summary": {}
        }

    # Create dynamic model
    EvaluationModel = create_evaluation_model(checks)

    # Format conversation for LLM
    dialog_text = "\n\n".join([
        f"**{msg['role'].upper()}**: {msg['content']}"
        for msg in conversation_history
    ])

    # Build system prompt
    system_prompt = """You are a coaching expert and judge evaluating the quality of coaching sessions.

Your task is to analyze the dialog and assess each criterion according to the provided instructions.

Evaluation rules:
1. For each criterion, write reasoning by quoting a specific dialog fragment as evidence
2. If you cannot find evidence in the dialog, write "No evidence in dialog"
3. Issue a verdict (passed): True if the criterion is FULLY satisfied, False otherwise
4. Be objective and strict — partial fulfillment = False
5. Quote EXACTLY what was said, do not paraphrase

Remember: This is an assessment of coaching QUALITY, not quantity of text."""

    # Build user prompt
    criteria_list = "\n".join([
        f"{i+1}. {check.id} - {check.title} ({check.priority}): {check.description}"
        for i, check in enumerate(checks)
    ])

    user_prompt = f"""## Dialog to evaluate:

{dialog_text}

---

## Criteria to evaluate ({len(checks)} total):

{criteria_list}

---

Evaluate the dialog above against all {len(checks)} criteria."""

    # Call LLM with structured output
    client = get_llm_client()

    try:
        result = client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_model=EvaluationModel,
            temperature=0.0  # Deterministic evaluation
        )
    except Exception as e:
        return {
            "error": f"LLM evaluation failed: {str(e)}",
            "results": [],
            "summary": {}
        }

    # Parse results
    results = []
    passed_count = 0

    for check in checks:
        prefix = check.id.replace("-", "_")
        reasoning = getattr(result, f"{prefix}_reasoning", "")
        passed = getattr(result, f"{prefix}_passed", False)

        if passed:
            passed_count += 1

        results.append({
            "id": check.id,
            "title": check.title,
            "priority": check.priority,
            "reasoning": reasoning,
            "passed": passed
        })

    failed_count = len(checks) - passed_count
    score_pct = (passed_count / len(checks) * 100) if checks else 0

    # Determine priority group
    priority_group = checks[0].priority if checks else "UNKNOWN"
    if len(set(c.priority for c in checks)) > 1:
        priority_group = "ALL"

    summary = {
        "passed_count": passed_count,
        "failed_count": failed_count,
        "total": len(checks),
        "score_pct": round(score_pct, 1),
        "priority": priority_group
    }

    return {
        "results": results,
        "summary": summary
    }


def format_evaluation_results(eval_result: Dict[str, Any]) -> str:
    """
    Format evaluation results as human-readable text for Gradio display.

    Args:
        eval_result: Output from evaluate_conversation()

    Returns:
        Formatted string with emoji indicators
    """
    if "error" in eval_result:
        return f"❌ **Error:** {eval_result['error']}"

    summary = eval_result["summary"]
    results = eval_result["results"]

    # Header
    output = f"""🎯 **Evaluation Results**

**Priority Group:** {summary['priority']}
**Score:** {summary['passed_count']}/{summary['total']} ({summary['score_pct']}%)
**Status:** {'✅ PASS' if summary['score_pct'] == 100 else '⚠️ PARTIAL' if summary['score_pct'] > 0 else '❌ FAIL'}

---

## Detailed Results:

"""

    # Individual results
    for r in results:
        icon = "✅" if r["passed"] else "❌"
        output += f"""
### {icon} {r['id']} - {r['title']} ({r['priority']})

**Verdict:** {'PASS ✅' if r['passed'] else 'FAIL ❌'}

**Reasoning:**
{r['reasoning']}

---
"""

    return output
