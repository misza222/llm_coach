"""
Fixtures for Playwright e2e tests.

The live_server fixture starts a real uvicorn server on port 8001 with:
- A fake coach that returns deterministic responses (no LLM calls).
- In-memory storage shared across the session.
- Anonymous message limit raised to 100 so tests never hit it.

Each test gets a fresh anonymous user ID because fresh_browser_state clears
localStorage before each test, causing the React app to generate a new UUID
on reload.  Sessions from different tests therefore belong to different users
and do not interfere.

Before running e2e tests, the frontend must be built:
    cd frontend && npm run build
"""

import os
import threading
import time

import httpx
import pytest
import uvicorn
from playwright.sync_api import Page
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

_SERVER_PORT = 8001
_SERVER_URL = f"http://127.0.0.1:{_SERVER_PORT}"


class _FakeCoachAgent:
    """Returns deterministic replies without calling any LLM.

    Behaviour hooks for e2e tests:
    - Always returns detected_emotions: ["curiosity"]
    - Messages starting with "My goal is " extract the goal into main_goal
    - The message "please close" triggers the CLOSING phase
    """

    def __init__(self) -> None:
        self._memory_manager = MemoryManager()

    def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState, bool]:
        state = self._memory_manager.add_user_message(state, user_message)
        reply = f"Coach: {user_message}"

        output: dict = {
            "response": reply,
            "coaching_phase": "CONTEXT_GATHERING",
            "detected_emotions": ["curiosity"],
            "question_type": "OPEN",
        }

        # Allow tests to trigger goal extraction
        if user_message.lower().startswith("my goal is "):
            output["main_goal"] = user_message[len("my goal is ") :]

        # Allow tests to trigger the closing phase
        if user_message.lower() == "please close":
            output["coaching_phase"] = "CLOSING"

        state, is_closing = self._memory_manager.update_from_output(state, output)
        return reply, state, is_closing


@pytest.fixture(scope="session")
def live_server():
    """Start the FastAPI app with a fake coach on port 8001 for the test session."""
    # Raise the anonymous message limit so tests never bump into it
    os.environ.setdefault("MAX_ANONYMOUS_MESSAGES", "100")

    storage = InMemoryBackend()
    memory_manager = MemoryManager()
    fake_coach = _FakeCoachAgent()

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    metadata.create_all(engine)
    user_repo = UserRepository(engine=engine)

    app = create_app()
    app.dependency_overrides[get_coach] = lambda: fake_coach
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_memory_manager] = lambda: memory_manager
    app.dependency_overrides[get_user_repository] = lambda: user_repo

    config = uvicorn.Config(app, host="127.0.0.1", port=_SERVER_PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait until the health endpoint responds
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            httpx.get(f"{_SERVER_URL}/api/v1/health", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Test server did not start within 10 seconds")

    yield _SERVER_URL

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def fresh_browser_state(page: Page, live_server: str) -> None:
    """Reset browser state before each test for a clean anonymous user ID.

    Sequence:
    1. Navigate to the app (creates an anonymous ID in localStorage).
    2. Clear localStorage (discards that ID).
    3. Reload — React generates a *new* anonymous ID and fetches a fresh
       empty session list, then auto-creates the first "Introduction" session.
    4. Wait for network activity to settle before handing control to the test.
    """
    page.goto(live_server)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_load_state("networkidle")
