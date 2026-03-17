"""Tests for the chat endpoint."""

from fastapi.testclient import TestClient


def test_chat_returns_coach_reply(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"user_id": "user-1", "message": "Hello coach"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Coach reply to: Hello coach"
    assert data["phase"] == "CONTEXT_GATHERING"
    assert "curiosity" in data["detected_emotions"]
    assert len(data["history"]) == 2  # user + assistant


def test_chat_empty_message_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"user_id": "user-1", "message": ""},
    )
    assert response.status_code == 422


def test_chat_missing_user_id_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello"},
    )
    assert response.status_code == 422


def test_chat_preserves_history_across_turns(client: TestClient) -> None:
    client.post("/api/v1/chat", json={"user_id": "user-2", "message": "First"})
    response = client.post("/api/v1/chat", json={"user_id": "user-2", "message": "Second"})
    data = response.json()
    # 2 turns × 2 messages each = 4
    assert len(data["history"]) == 4


def test_chat_llm_error_returns_502(client: TestClient) -> None:
    """When the coach raises LLMError the API returns 502."""
    from life_coach_system.api.dependencies import get_coach
    from life_coach_system.exceptions import LLMError
    from life_coach_system.memory.schemas.session_state import SessionState

    class BrokenCoach:
        def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState]:
            raise LLMError("upstream timeout")

    app = client.app
    app.dependency_overrides[get_coach] = lambda: BrokenCoach()

    response = client.post(
        "/api/v1/chat",
        json={"user_id": "user-err", "message": "Hello"},
    )
    assert response.status_code == 502
    assert "upstream timeout" in response.json()["detail"]
