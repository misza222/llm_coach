"""
Fixtures for API tests.

Overrides CoachAgent with a fake that returns canned responses,
so tests never hit a real LLM.
"""

import pytest
from fastapi.testclient import TestClient

from life_coach_system.api.app import create_app
from life_coach_system.api.dependencies import get_coach, get_memory_manager, get_storage
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend


class FakeCoachAgent:
    """Returns a canned response without calling any LLM."""

    def __init__(self) -> None:
        self.memory_manager = MemoryManager()

    def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState]:
        state = self.memory_manager.add_user_message(state, user_message)
        state = self.memory_manager.update_from_output(
            state,
            {
                "response": f"Coach reply to: {user_message}",
                "coaching_phase": "CONTEXT_GATHERING",
                "detected_emotions": ["curiosity"],
                "question_type": "OPEN",
            },
        )
        return f"Coach reply to: {user_message}", state


@pytest.fixture()
def client() -> TestClient:
    """TestClient with fake coach and fresh storage per test."""
    app = create_app()

    fresh_storage = InMemoryBackend()
    fresh_memory_manager = MemoryManager()
    fake_coach = FakeCoachAgent()

    app.dependency_overrides[get_coach] = lambda: fake_coach
    app.dependency_overrides[get_storage] = lambda: fresh_storage
    app.dependency_overrides[get_memory_manager] = lambda: fresh_memory_manager

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()
