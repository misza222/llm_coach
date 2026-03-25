"""
Fixtures for API tests.

Overrides CoachAgent with a fake that returns canned responses,
so tests never hit a real LLM.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from life_coach_system.api.app import create_app
from life_coach_system.api.dependencies import (
    get_coach,
    get_memory_manager,
    get_storage,
    get_user_repository,
)
from life_coach_system.auth.user_repository import UserRepository
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend
from life_coach_system.persistence.tables import metadata


class FakeCoachAgent:
    """Returns a canned response without calling any LLM."""

    def __init__(self, *, storage=None) -> None:
        self.memory_manager = MemoryManager()
        self._storage = storage

    def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState, bool]:
        state = self.memory_manager.add_user_message(state, user_message)
        state, is_closing = self.memory_manager.update_from_output(
            state,
            {
                "response": f"Coach reply to: {user_message}",
                "coaching_phase": "CONTEXT_GATHERING",
                "detected_emotions": ["curiosity"],
                "question_type": "OPEN",
            },
        )
        return f"Coach reply to: {user_message}", state, is_closing


@pytest.fixture()
def client() -> TestClient:
    """TestClient with fake coach and fresh storage per test."""
    app = create_app()

    fresh_storage = InMemoryBackend()
    fresh_memory_manager = MemoryManager()
    fake_coach = FakeCoachAgent(storage=fresh_storage)

    # Create a fresh in-memory SQLite for auth tables (StaticPool shares one connection)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    metadata.create_all(engine)
    fresh_user_repo = UserRepository(engine=engine)

    app.dependency_overrides[get_coach] = lambda: fake_coach
    app.dependency_overrides[get_storage] = lambda: fresh_storage
    app.dependency_overrides[get_memory_manager] = lambda: fresh_memory_manager
    app.dependency_overrides[get_user_repository] = lambda: fresh_user_repo

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()

    # Clear lru_cache on dependency providers to avoid cross-test leaks
    for dep_fn in (get_coach, get_storage, get_memory_manager, get_user_repository):
        if hasattr(dep_fn, "cache_clear"):
            dep_fn.cache_clear()
