"""Shared test fixtures for Life Coach System tests."""

import pytest

from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend


@pytest.fixture
def empty_state() -> SessionState:
    return SessionState(user_id="test_user")


@pytest.fixture
def backend() -> InMemoryBackend:
    return InMemoryBackend()


@pytest.fixture
def manager() -> MemoryManager:
    return MemoryManager()
