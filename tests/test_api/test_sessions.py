"""Tests for session management endpoints."""

from fastapi.testclient import TestClient


def test_get_nonexistent_session_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/nobody")
    assert response.status_code == 404


def test_get_session_after_chat(client: TestClient) -> None:
    client.post("/api/v1/chat", json={"user_id": "user-s1", "message": "Hi"})

    response = client.get("/api/v1/sessions/user-s1")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-s1"
    assert data["current_phase"] == "CONTEXT_GATHERING"
    assert len(data["history"]) == 2


def test_reset_session_clears_state(client: TestClient) -> None:
    client.post("/api/v1/chat", json={"user_id": "user-s2", "message": "Hi"})

    response = client.post("/api/v1/sessions/user-s2/reset")
    assert response.status_code == 200
    assert response.json() == {"status": "reset"}

    # Session should be gone
    response = client.get("/api/v1/sessions/user-s2")
    assert response.status_code == 404


def test_reset_nonexistent_session_is_idempotent(client: TestClient) -> None:
    response = client.post("/api/v1/sessions/ghost/reset")
    assert response.status_code == 200


def test_export_session_returns_json_file(client: TestClient) -> None:
    client.post("/api/v1/chat", json={"user_id": "user-s3", "message": "Hi"})

    response = client.get("/api/v1/sessions/user-s3/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]


def test_export_nonexistent_session_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/nobody/export")
    assert response.status_code == 404
