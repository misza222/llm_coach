"""Tests for session management endpoints."""

from fastapi.testclient import TestClient

from life_coach_system.api.dependencies import get_storage


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
    # Chat to create initial session with messages
    client.post("/api/v1/chat", json={"user_id": "user-s2", "message": "Hi"})

    # Create new session (auto-completes old one because it has messages)
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


def test_new_session_returns_existing_when_active_session_is_empty(
    client: TestClient,
) -> None:
    """Clicking New Session on an empty session returns the same session, not a new one."""
    # Create first session (no messages)
    first = client.post("/api/v1/sessions/user-s2b/new").json()
    first_id = first["session_id"]

    # Requesting another new session should return the same empty session
    second = client.post("/api/v1/sessions/user-s2b/new").json()
    assert second["session_id"] == first_id

    # Still only one session
    sessions = client.get("/api/v1/sessions/user-s2b").json()["sessions"]
    assert len(sessions) == 1


def test_first_session_has_introduction_title(client: TestClient) -> None:
    """First session created for a user gets the fixed 'Introduction' title."""
    session = client.post("/api/v1/sessions/user-s2c/new").json()
    assert session["title"] == "Introduction"


def test_subsequent_session_has_placeholder_title(client: TestClient) -> None:
    """Second session (after user has chatted) starts with 'New session' placeholder."""
    # Chat to give first session some messages, then create a second session
    client.post("/api/v1/chat", json={"user_id": "user-s2d", "message": "Hi"})
    session = client.post("/api/v1/sessions/user-s2d/new").json()
    assert session["title"] == "New session"


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


def test_end_session_creates_user_profile(client: TestClient) -> None:
    """Ending a session materializes a cross-session user profile."""
    r = client.post("/api/v1/chat", json={"user_id": "user-prof", "message": "Hello"})
    session_id = r.json()["session_id"]

    client.post(f"/api/v1/sessions/user-prof/{session_id}/end")

    # Verify profile was persisted via the injected storage
    storage = client.app.dependency_overrides[get_storage]()
    profile = storage.load_user_profile("user-prof")
    assert profile is not None
    assert profile["completed_session_count"] == 1


def test_create_new_session_auto_complete_creates_profile(client: TestClient) -> None:
    """Auto-completing an active session via POST /new also creates a user profile."""
    client.post("/api/v1/chat", json={"user_id": "user-auto", "message": "Hi there"})
    client.post("/api/v1/sessions/user-auto/new")

    storage = client.app.dependency_overrides[get_storage]()
    profile = storage.load_user_profile("user-auto")
    assert profile is not None
    assert profile["completed_session_count"] == 1
