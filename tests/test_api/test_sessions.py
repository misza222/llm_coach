"""Tests for session management endpoints."""

from fastapi.testclient import TestClient


def test_list_sessions_empty_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/nobody")
    assert response.status_code == 200
    assert response.json() == {"sessions": []}


def test_list_sessions_after_chat(client: TestClient) -> None:
    client.post("/api/v1/chat", json={"user_id": "user-s1", "message": "Hi"})

    response = client.get("/api/v1/sessions/user-s1")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["status"] == "ACTIVE"


def test_get_specific_session_after_chat(client: TestClient) -> None:
    r = client.post("/api/v1/chat", json={"user_id": "user-s1", "message": "Hi"})
    session_id = r.json()["session_id"]

    response = client.get(f"/api/v1/sessions/user-s1/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-s1"
    assert data["session_id"] == session_id
    assert data["current_phase"] == "CONTEXT_GATHERING"
    assert len(data["history"]) == 2


def test_get_nonexistent_session_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/user-s1/nonexistent")
    assert response.status_code == 404


def test_create_new_session(client: TestClient) -> None:
    # Chat to create initial session
    client.post("/api/v1/chat", json={"user_id": "user-s2", "message": "Hi"})

    # Create new session (auto-completes old one)
    response = client.post("/api/v1/sessions/user-s2/new")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"

    # List should show 2 sessions
    list_resp = client.get("/api/v1/sessions/user-s2")
    sessions = list_resp.json()["sessions"]
    assert len(sessions) == 2
    statuses = {s["status"] for s in sessions}
    assert statuses == {"ACTIVE", "COMPLETED"}


def test_end_session(client: TestClient) -> None:
    r = client.post("/api/v1/chat", json={"user_id": "user-s3", "message": "Hi"})
    session_id = r.json()["session_id"]

    response = client.post(f"/api/v1/sessions/user-s3/{session_id}/end")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_delete_session(client: TestClient) -> None:
    r = client.post("/api/v1/chat", json={"user_id": "user-s4", "message": "Hi"})
    session_id = r.json()["session_id"]

    response = client.delete(f"/api/v1/sessions/user-s4/{session_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Session should be gone
    list_resp = client.get("/api/v1/sessions/user-s4")
    assert list_resp.json()["sessions"] == []


def test_export_session_returns_json_file(client: TestClient) -> None:
    r = client.post("/api/v1/chat", json={"user_id": "user-s5", "message": "Hi"})
    session_id = r.json()["session_id"]

    response = client.get(f"/api/v1/sessions/user-s5/{session_id}/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]


def test_export_nonexistent_session_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/nobody/nonexistent/export")
    assert response.status_code == 404
