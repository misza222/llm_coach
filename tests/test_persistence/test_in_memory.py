"""Tests for InMemoryBackend persistence implementation."""

import pytest

from life_coach_system.exceptions import PersistenceError
from life_coach_system.persistence.in_memory import InMemoryBackend


def test_save_and_load_round_trip(backend: InMemoryBackend) -> None:
    """Saved state is returned unchanged by load."""
    state = {"user_id": "alice", "score": 42}
    backend.save("alice", state)
    loaded = backend.load("alice")
    assert loaded == state


def test_exists_returns_false_for_unknown_user(backend: InMemoryBackend) -> None:
    """exists() is False when no state has been saved for the user."""
    assert backend.exists("ghost") is False


def test_exists_returns_true_after_save(backend: InMemoryBackend) -> None:
    """exists() is True immediately after save()."""
    backend.save("bob", {"x": 1})
    assert backend.exists("bob") is True


def test_delete_removes_state(backend: InMemoryBackend) -> None:
    """delete() removes the entry so subsequent load() returns None."""
    backend.save("carol", {"data": "value"})
    backend.delete("carol")
    assert backend.load("carol") is None


def test_delete_raises_for_unknown_user(backend: InMemoryBackend) -> None:
    """delete() raises PersistenceError when user doesn't exist."""
    with pytest.raises(PersistenceError):
        backend.delete("nobody")


def test_list_users_returns_correct_ids(backend: InMemoryBackend) -> None:
    """list_users() returns exactly the saved user IDs."""
    backend.save("u1", {})
    backend.save("u2", {})
    assert set(backend.list_users()) == {"u1", "u2"}


def test_load_returns_deep_copy(backend: InMemoryBackend) -> None:
    """Mutating the returned dict does not affect the stored state."""
    original = {"items": [1, 2, 3]}
    backend.save("dave", original)

    loaded = backend.load("dave")
    assert loaded is not None
    loaded["items"].append(99)  # mutate the returned copy

    # Internal storage must be untouched
    stored_again = backend.load("dave")
    assert stored_again == {"items": [1, 2, 3]}
