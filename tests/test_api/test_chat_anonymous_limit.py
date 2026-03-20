"""Tests for anonymous message gating in the chat endpoint."""

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
from life_coach_system.auth.jwt import create_access_token
from life_coach_system.auth.user_repository import UserRepository
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend
from life_coach_system.persistence.tables import metadata


class _FakeCoach:
    def __init__(self) -> None:
        self.memory_manager = MemoryManager()

    def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState, bool]:
        state = self.memory_manager.add_user_message(state, user_message)
        state, is_closing = self.memory_manager.update_from_output(
            state,
            {
                "response": f"Reply: {user_message}",
                "coaching_phase": "CONTEXT_GATHERING",
                "detected_emotions": [],
                "question_type": "OPEN",
            },
        )
        return f"Reply: {user_message}", state, is_closing


def _make_client(*, max_anonymous: int = 3) -> TestClient:
    """Create a test client with a specific anonymous message limit."""
    # Patch config at the module level for this test
    from life_coach_system.config import settings

    original_limit = settings.max_anonymous_messages
    settings.max_anonymous_messages = max_anonymous

    app = create_app()

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    metadata.create_all(engine)
    user_repo = UserRepository(engine=engine)

    app.dependency_overrides[get_coach] = lambda: _FakeCoach()
    app.dependency_overrides[get_storage] = lambda: InMemoryBackend()
    app.dependency_overrides[get_memory_manager] = lambda: MemoryManager()
    app.dependency_overrides[get_user_repository] = lambda: user_repo

    return TestClient(app), settings, original_limit


def test_anonymous_user_gets_remaining_messages_count() -> None:
    tc, settings_obj, original = _make_client(max_anonymous=5)
    try:
        with tc:
            r = tc.post("/api/v1/chat", json={"user_id": "anon-1", "message": "hello"})
            assert r.status_code == 200
            data = r.json()
            assert data["is_anonymous"] is True
            assert data["remaining_messages"] == 4  # 5 - 0 - 1
    finally:
        settings_obj.max_anonymous_messages = original


def test_anonymous_user_blocked_after_limit() -> None:
    tc, settings_obj, original = _make_client(max_anonymous=2)
    try:
        with tc:
            # Send 2 messages (the limit)
            for i in range(2):
                r = tc.post("/api/v1/chat", json={"user_id": "anon-x", "message": f"msg-{i}"})
                assert r.status_code == 200

            # Third message should be blocked
            r = tc.post("/api/v1/chat", json={"user_id": "anon-x", "message": "too many"})
            assert r.status_code == 403
            assert "limit" in r.json()["detail"].lower()
    finally:
        settings_obj.max_anonymous_messages = original


def test_authenticated_user_bypasses_limit() -> None:
    tc, settings_obj, original = _make_client(max_anonymous=1)
    try:
        with tc:
            token = create_access_token(user_id="real-user-1", email="a@b.com")
            # Authenticated users should not be limited
            for i in range(5):
                r = tc.post(
                    "/api/v1/chat",
                    json={"user_id": "ignored", "message": f"msg-{i}"},
                    cookies={"access_token": token},
                )
                assert r.status_code == 200
                data = r.json()
                assert data["is_anonymous"] is False
                assert data["remaining_messages"] is None
    finally:
        settings_obj.max_anonymous_messages = original
