"""Tests for the dynamic evaluation model builder."""

from life_coach_system.utils.evaluator import create_evaluation_model
from life_coach_system.utils.leaderboard_parser import CheckDefinition


def _make_check(check_id: str) -> CheckDefinition:
    return CheckDefinition(
        id=check_id,
        title=f"Title {check_id}",
        description=f"Description for {check_id}",
        priority="MUST-HAVE",
    )


def test_create_evaluation_model_has_correct_field_names() -> None:
    """Model for LC-001 has fields LC_001_reasoning and LC_001_passed."""
    checks = [_make_check("LC-001")]
    Model = create_evaluation_model(checks)
    field_names = set(Model.model_fields.keys())
    assert "LC_001_reasoning" in field_names
    assert "LC_001_passed" in field_names


def test_create_evaluation_model_has_two_fields_per_check() -> None:
    """Dynamically created model has exactly 2 * len(checks) fields."""
    checks = [_make_check(f"LC-{i:03d}") for i in range(1, 6)]
    Model = create_evaluation_model(checks)
    assert len(Model.model_fields) == 2 * len(checks)
