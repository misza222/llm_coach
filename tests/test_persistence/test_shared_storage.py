"""Integration test: two app instances sharing the same database see each other's data.

Simulates the scenario where the FastAPI API and Gradio dev UI both point to the
same SQLite file via DATABASE_URL. A session created by one must be visible to the other.
"""

from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence import create_storage


def test_session_created_by_one_instance_is_visible_to_another(tmp_path) -> None:
    """Two SqlBackend instances pointing at the same SQLite file share state."""
    db_url = f"sqlite:///{tmp_path / 'shared.db'}"

    # Simulate the API backend
    api_storage = create_storage(database_url=db_url)
    manager = MemoryManager()
    state = manager.create_empty_state("user-1", is_first=True)
    state = manager.add_user_message(state, "Hello from the API")
    api_storage.save(state.session_id, state.model_dump())

    # Simulate the dev UI backend (separate instance, same DB)
    devui_storage = create_storage(database_url=db_url)
    loaded = devui_storage.find_active_session("user-1")

    assert loaded is not None
    assert loaded["session_id"] == state.session_id
    assert loaded["conversation_history"][0]["content"] == "Hello from the API"


def test_user_profile_shared_across_instances(tmp_path) -> None:
    """UserProfile saved by one instance is loadable by another."""
    db_url = f"sqlite:///{tmp_path / 'shared.db'}"

    api_storage = create_storage(database_url=db_url)
    api_storage.save_user_profile("user-1", {"user_name": "Alice", "completed_session_count": 2})

    devui_storage = create_storage(database_url=db_url)
    profile = devui_storage.load_user_profile("user-1")

    assert profile is not None
    assert profile["user_name"] == "Alice"
    assert profile["completed_session_count"] == 2


def test_session_completed_in_devui_visible_in_api(tmp_path) -> None:
    """Full round-trip: create in instance A, complete in instance B, list in A."""
    db_url = f"sqlite:///{tmp_path / 'shared.db'}"
    manager = MemoryManager()

    # Instance A creates a session
    storage_a = create_storage(database_url=db_url)
    state = manager.create_empty_state("user-1")
    state = manager.add_user_message(state, "Hi")
    storage_a.save(state.session_id, state.model_dump())

    # Instance B loads, completes, and saves
    storage_b = create_storage(database_url=db_url)
    loaded = storage_b.find_active_session("user-1")
    assert loaded is not None
    active_state = manager.complete_session(SessionState(**loaded))
    storage_b.save(active_state.session_id, active_state.model_dump())

    # Instance A sees the session as completed
    sessions = storage_a.list_sessions("user-1")
    assert len(sessions) == 1
    assert sessions[0]["status"] == "COMPLETED"
