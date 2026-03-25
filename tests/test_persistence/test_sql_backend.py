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
    state = {"user_id": "alice", "session_id": "s1", "status": "ACTIVE", "score": 42}
    sql_backend.save("s1", state)
    loaded = sql_backend.load("s1")
    assert loaded == state


def test_load_returns_none_for_unknown_session(sql_backend: SqlBackend) -> None:
    """load() returns None when no state has been saved."""
    assert sql_backend.load("ghost") is None


def test_exists_returns_false_for_unknown_session(sql_backend: SqlBackend) -> None:
    """exists() is False when no state has been saved for the session."""
    assert sql_backend.exists("ghost") is False


def test_exists_returns_true_after_save(sql_backend: SqlBackend) -> None:
    """exists() is True immediately after save()."""
    sql_backend.save("s1", {"user_id": "bob", "session_id": "s1", "status": "ACTIVE"})
    assert sql_backend.exists("s1") is True


def test_save_overwrites_existing_state(sql_backend: SqlBackend) -> None:
    """Saving twice for the same session overwrites the first entry."""
    sql_backend.save("s1", {"user_id": "carol", "session_id": "s1", "version": 1})
    sql_backend.save("s1", {"user_id": "carol", "session_id": "s1", "version": 2})
    loaded = sql_backend.load("s1")
    assert loaded == {"user_id": "carol", "session_id": "s1", "version": 2}


def test_delete_removes_state(sql_backend: SqlBackend) -> None:
    """delete() removes the entry so subsequent load() returns None."""
    sql_backend.save("s1", {"user_id": "carol", "session_id": "s1", "status": "ACTIVE"})
    sql_backend.delete("s1")
    assert sql_backend.load("s1") is None


def test_delete_raises_for_unknown_session(sql_backend: SqlBackend) -> None:
    """delete() raises PersistenceError when session doesn't exist."""
    with pytest.raises(PersistenceError):
        sql_backend.delete("nobody")


def test_list_sessions_returns_summaries(sql_backend: SqlBackend) -> None:
    """list_sessions() returns summaries for the given user."""
    sql_backend.save(
        "s1",
        {
            "user_id": "alice",
            "session_id": "s1",
            "status": "ACTIVE",
            "current_phase": "INTRODUCTION",
        },
    )
    sql_backend.save(
        "s2",
        {
            "user_id": "alice",
            "session_id": "s2",
            "status": "COMPLETED",
            "current_phase": "CLOSING",
        },
    )
    sql_backend.save(
        "s3",
        {
            "user_id": "bob",
            "session_id": "s3",
            "status": "ACTIVE",
        },
    )

    alice_sessions = sql_backend.list_sessions("alice")
    assert len(alice_sessions) == 2


def test_list_sessions_empty_initially(sql_backend: SqlBackend) -> None:
    """list_sessions() returns empty list for a user with no sessions."""
    assert sql_backend.list_sessions("nobody") == []


def test_find_active_session(sql_backend: SqlBackend) -> None:
    """find_active_session() returns the active session for a user."""
    sql_backend.save(
        "s1",
        {
            "user_id": "alice",
            "session_id": "s1",
            "status": "COMPLETED",
        },
    )
    sql_backend.save(
        "s2",
        {
            "user_id": "alice",
            "session_id": "s2",
            "status": "ACTIVE",
        },
    )

    active = sql_backend.find_active_session("alice")
    assert active is not None
    assert active["session_id"] == "s2"


def test_find_active_session_returns_none_when_none_active(sql_backend: SqlBackend) -> None:
    """find_active_session() returns None when all sessions are completed."""
    sql_backend.save(
        "s1",
        {
            "user_id": "alice",
            "session_id": "s1",
            "status": "COMPLETED",
        },
    )
    assert sql_backend.find_active_session("alice") is None


def test_nested_state_round_trip(sql_backend: SqlBackend) -> None:
    """Complex nested state survives JSON serialization round-trip."""
    state = {
        "user_id": "eve",
        "session_id": "s1",
        "status": "ACTIVE",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        "detected_emotions": ["happy", "curious"],
        "nested": {"deep": {"value": True}},
    }
    sql_backend.save("s1", state)
    loaded = sql_backend.load("s1")
    assert loaded == state


# --- User profile tests ---


def test_save_and_load_user_profile_round_trip(sql_backend: SqlBackend) -> None:
    """Saved profile is returned unchanged by load_user_profile."""
    profile = {"user_id": "alice", "user_name": "Alice", "completed_session_count": 3}
    sql_backend.save_user_profile("alice", profile)
    loaded = sql_backend.load_user_profile("alice")
    assert loaded == profile


def test_load_user_profile_returns_none_for_unknown_user(sql_backend: SqlBackend) -> None:
    """load_user_profile() returns None when no profile exists."""
    assert sql_backend.load_user_profile("ghost") is None


def test_save_user_profile_overwrites_existing(sql_backend: SqlBackend) -> None:
    """Saving a profile twice overwrites the first entry."""
    sql_backend.save_user_profile("alice", {"user_name": "Alice", "version": 1})
    sql_backend.save_user_profile("alice", {"user_name": "Alice W.", "version": 2})
    loaded = sql_backend.load_user_profile("alice")
    assert loaded == {"user_name": "Alice W.", "version": 2}
