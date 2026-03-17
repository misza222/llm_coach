"""Tests for leaderboard card parsing and priority filtering."""

from pathlib import Path

import pytest

from life_coach_system.utils.leaderboard_parser import (
    CheckDefinition,
    filter_checks_by_priority,
    parse_leaderboard_card,
)

LEADERBOARD_PATH = str(Path(__file__).parents[2] / "leaderboard_card_coach.md")


@pytest.fixture(scope="module")
def all_checks() -> list[CheckDefinition]:
    return parse_leaderboard_card(LEADERBOARD_PATH)


def test_parse_leaderboard_card_returns_14_checks(all_checks: list[CheckDefinition]) -> None:
    """The leaderboard file defines exactly 14 criteria."""
    assert len(all_checks) == 14


def test_must_have_and_should_have_priorities_are_correctly_assigned(
    all_checks: list[CheckDefinition],
) -> None:
    """Every check has a priority of either MUST-HAVE or SHOULD-HAVE."""
    for check in all_checks:
        assert check.priority in {"MUST-HAVE", "SHOULD-HAVE"}


def test_filter_must_have_returns_7_checks(all_checks: list[CheckDefinition]) -> None:
    """Filtering by MUST-HAVE returns exactly 7 checks."""
    result = filter_checks_by_priority(all_checks, "MUST-HAVE")
    assert len(result) == 7
    assert all(c.priority == "MUST-HAVE" for c in result)


def test_filter_should_have_returns_7_checks(all_checks: list[CheckDefinition]) -> None:
    """Filtering by SHOULD-HAVE returns exactly 7 checks."""
    result = filter_checks_by_priority(all_checks, "SHOULD-HAVE")
    assert len(result) == 7
    assert all(c.priority == "SHOULD-HAVE" for c in result)


def test_filter_all_returns_all_14_checks(all_checks: list[CheckDefinition]) -> None:
    """Filtering by ALL returns all 14 checks unchanged."""
    result = filter_checks_by_priority(all_checks, "ALL")
    assert len(result) == 14
