"""Tests for InMemoryBackend persistence implementation."""

import pytest

from life_coach_system.exceptions import PersistenceError
from life_coach_system.persistence.in_memory import InMemoryBackend


def test_save_and_load_round_trip(backend: InMemoryBackend) -> None:
    """Saved state is returned unchanged by load."""
    state = {"user_id": "alice", "session_id": "s1", "status": "ACTIVE", "score": 42}
    backend.save("s1", state)
    loaded = backend.load("s1")
    assert loaded == state


def test_exists_returns_false_for_unknown_session(backend: InMemoryBackend) -> None:
    """exists() is False when no state has been saved for the session."""
    assert backend.exists("ghost") is False


def test_exists_returns_true_after_save(backend: InMemoryBackend) -> None:
    """exists() is True immediately after save()."""
    backend.save("s1", {"user_id": "bob", "session_id": "s1", "status": "ACTIVE"})
    assert backend.exists("s1") is True


def test_delete_removes_state(backend: InMemoryBackend) -> None:
    """delete() removes the entry so subsequent load() returns None."""
    backend.save("s1", {"user_id": "carol", "session_id": "s1", "status": "ACTIVE"})
    backend.delete("s1")
    assert backend.load("s1") is None


def test_delete_raises_for_unknown_session(backend: InMemoryBackend) -> None:
    """delete() raises PersistenceError when session doesn't exist."""
    with pytest.raises(PersistenceError):
        backend.delete("nobody")


def test_list_sessions_returns_summaries_for_user(backend: InMemoryBackend) -> None:
    """list_sessions() returns summaries for sessions belonging to the given user."""
    backend.save(
        "s1",
        {
            "user_id": "alice",
            "session_id": "s1",
            "status": "ACTIVE",
            "title": "First",
            "current_phase": "INTRODUCTION",
            "created_at": "2024-01-01",
        },
    )
    backend.save(
        "s2",
        {
            "user_id": "alice",
            "session_id": "s2",
            "status": "COMPLETED",
            "title": "Second",
            "current_phase": "CLOSING",
            "created_at": "2024-01-02",
        },
    )
    backend.save(
        "s3",
        {
            "user_id": "bob",
            "session_id": "s3",
            "status": "ACTIVE",
            "title": "Bob's",
            "current_phase": "INTRODUCTION",
            "created_at": "2024-01-01",
        },
    )

    alice_sessions = backend.list_sessions("alice")
    assert len(alice_sessions) == 2
    assert all(s["session_id"] in ("s1", "s2") for s in alice_sessions)


def test_find_active_session_returns_active(backend: InMemoryBackend) -> None:
    """find_active_session() returns the active session state for a user."""
    backend.save(
        "s1",
        {
            "user_id": "alice",
            "session_id": "s1",
            "status": "COMPLETED",
        },
    )
    backend.save(
        "s2",
        {
            "user_id": "alice",
            "session_id": "s2",
            "status": "ACTIVE",
        },
    )

    active = backend.find_active_session("alice")
    assert active is not None
    assert active["session_id"] == "s2"


def test_find_active_session_returns_none_when_all_completed(
    backend: InMemoryBackend,
) -> None:
    """find_active_session() returns None when user has no active sessions."""
    backend.save(
        "s1",
        {
            "user_id": "alice",
            "session_id": "s1",
            "status": "COMPLETED",
        },
    )
    assert backend.find_active_session("alice") is None


def test_load_returns_deep_copy(backend: InMemoryBackend) -> None:
    """Mutating the returned dict does not affect the stored state."""
    original = {"session_id": "s1", "user_id": "dave", "items": [1, 2, 3]}
    backend.save("s1", original)

    loaded = backend.load("s1")
    assert loaded is not None
    loaded["items"].append(99)  # mutate the returned copy

    # Internal storage must be untouched
    stored_again = backend.load("s1")
    assert stored_again == {"session_id": "s1", "user_id": "dave", "items": [1, 2, 3]}
