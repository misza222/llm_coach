"""Tests for SqlBackend persistence implementation (SQLite)."""

import pytest

from life_coach_system.exceptions import PersistenceError
from life_coach_system.persistence.sql_backend import SqlBackend


@pytest.fixture
def sql_backend(tmp_path) -> SqlBackend:
    """Create a SqlBackend with a temporary SQLite database."""
    db_path = tmp_path / "test.db"
    return SqlBackend(database_url=f"sqlite:///{db_path}")


def test_save_and_load_round_trip(sql_backend: SqlBackend) -> None:
    """Saved state is returned unchanged by load."""
    state = {"user_id": "alice", "score": 42, "items": [1, 2, 3]}
    sql_backend.save("alice", state)
    loaded = sql_backend.load("alice")
    assert loaded == state


def test_load_returns_none_for_unknown_user(sql_backend: SqlBackend) -> None:
    """load() returns None when no state has been saved."""
    assert sql_backend.load("ghost") is None


def test_exists_returns_false_for_unknown_user(sql_backend: SqlBackend) -> None:
    """exists() is False when no state has been saved for the user."""
    assert sql_backend.exists("ghost") is False


def test_exists_returns_true_after_save(sql_backend: SqlBackend) -> None:
    """exists() is True immediately after save()."""
    sql_backend.save("bob", {"x": 1})
    assert sql_backend.exists("bob") is True


def test_save_overwrites_existing_state(sql_backend: SqlBackend) -> None:
    """Saving twice for the same user overwrites the first entry."""
    sql_backend.save("carol", {"version": 1})
    sql_backend.save("carol", {"version": 2})
    loaded = sql_backend.load("carol")
    assert loaded == {"version": 2}


def test_delete_removes_state(sql_backend: SqlBackend) -> None:
    """delete() removes the entry so subsequent load() returns None."""
    sql_backend.save("carol", {"data": "value"})
    sql_backend.delete("carol")
    assert sql_backend.load("carol") is None


def test_delete_raises_for_unknown_user(sql_backend: SqlBackend) -> None:
    """delete() raises PersistenceError when user doesn't exist."""
    with pytest.raises(PersistenceError):
        sql_backend.delete("nobody")


def test_list_users_returns_correct_ids(sql_backend: SqlBackend) -> None:
    """list_users() returns exactly the saved user IDs."""
    sql_backend.save("u1", {})
    sql_backend.save("u2", {})
    assert set(sql_backend.list_users()) == {"u1", "u2"}


def test_list_users_empty_initially(sql_backend: SqlBackend) -> None:
    """list_users() returns empty list for fresh database."""
    assert sql_backend.list_users() == []


def test_nested_state_round_trip(sql_backend: SqlBackend) -> None:
    """Complex nested state survives JSON serialization round-trip."""
    state = {
        "user_id": "eve",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        "detected_emotions": ["happy", "curious"],
        "nested": {"deep": {"value": True}},
    }
    sql_backend.save("eve", state)
    loaded = sql_backend.load("eve")
    assert loaded == state
