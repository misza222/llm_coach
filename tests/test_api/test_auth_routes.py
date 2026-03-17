"""Tests for auth API routes (/me, /logout, login redirect)."""

from fastapi.testclient import TestClient

from life_coach_system.auth.jwt import create_access_token


def test_auth_me_returns_unauthenticated_without_cookie(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["is_authenticated"] is False
    assert data["user"] is None


def test_auth_me_returns_user_with_valid_cookie(client: TestClient) -> None:
    token = create_access_token(
        user_id="user-42", email="test@example.com", name="Test User", provider="google"
    )
    response = client.get("/api/v1/auth/me", cookies={"access_token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["is_authenticated"] is True
    assert data["user"]["id"] == "user-42"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"
    assert data["user"]["provider"] == "google"


def test_auth_me_returns_unauthenticated_with_invalid_cookie(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", cookies={"access_token": "bad-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_authenticated"] is False


def test_logout_clears_cookie(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    # Cookie should be deleted (max-age=0 or expires in the past)
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie


def test_login_unsupported_provider_redirects(client: TestClient) -> None:
    response = client.get("/api/v1/auth/login/unsupported", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "error=unsupported_provider" in response.headers["location"]
