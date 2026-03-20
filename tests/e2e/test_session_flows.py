"""
End-to-end tests for session management flows.

Each test uses the `fresh_browser_state` autouse fixture (defined in conftest.py)
which navigates to the app, clears localStorage, and reloads so every test
begins with a fresh anonymous user and a single "Introduction" session.

Run with:
    uv run pytest -m e2e -v

The frontend must be built before running:
    cd frontend && npm run build
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_first_visit_shows_introduction_session(page: Page) -> None:
    """A brand-new user sees exactly one session named 'Introduction' in the sidebar."""
    # fresh_browser_state already navigated and waited for network idle
    items = page.get_by_test_id("session-item")
    expect(items).to_have_count(1)
    expect(items.first).to_contain_text("Introduction")


@pytest.mark.e2e
def test_new_session_button_on_empty_session_is_idempotent(page: Page) -> None:
    """Clicking New Session multiple times on an empty session does not create duplicates."""
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")

    # Still only one session — the empty Introduction session was re-used each time
    items = page.get_by_test_id("session-item")
    expect(items).to_have_count(1)
    expect(items.first).to_contain_text("Introduction")


@pytest.mark.e2e
def test_end_session_shows_completion_banner(page: Page) -> None:
    """Clicking End Session marks the session done and shows the completion banner."""
    page.get_by_test_id("end-session-btn").click()

    # The completion banner must appear and the End Session button must disappear
    expect(page.get_by_test_id("session-completed-banner")).to_be_visible()
    expect(page.get_by_test_id("end-session-btn")).not_to_be_visible()


@pytest.mark.e2e
def test_end_session_marks_session_done_in_sidebar(page: Page) -> None:
    """After ending a session the sidebar shows the 'done' badge on that session."""
    page.get_by_test_id("end-session-btn").click()
    page.wait_for_load_state("networkidle")

    # The session item should now show the 'done' text rendered alongside the title
    expect(page.get_by_test_id("session-item").first).to_contain_text("done")


@pytest.mark.e2e
def test_start_new_session_after_completion_creates_fresh_session(page: Page) -> None:
    """The 'Start a new session' link in the completion banner opens a new empty session."""
    # End the current session
    page.get_by_test_id("end-session-btn").click()
    expect(page.get_by_test_id("session-completed-banner")).to_be_visible()

    # Start a new session via the banner link
    page.get_by_test_id("start-new-session-link").click()
    page.wait_for_load_state("networkidle")

    # Banner should be gone and we should have 2 sessions in the sidebar
    expect(page.get_by_test_id("session-completed-banner")).not_to_be_visible()
    expect(page.get_by_test_id("session-item")).to_have_count(2)


@pytest.mark.e2e
def test_first_session_title_stays_introduction_after_chat(page: Page) -> None:
    """The 'Introduction' title is preserved even after the user sends their first message."""
    page.get_by_test_id("chat-input").fill("I want to become a better leader")
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")

    # Title must remain "Introduction" — it is a fixed label, not an auto-generated one
    expect(page.get_by_test_id("session-item").first).to_contain_text("Introduction")


@pytest.mark.e2e
def test_second_session_title_updates_from_first_message(page: Page) -> None:
    """A second session starts as 'New session' and gets titled from the first user message."""
    # Complete the Introduction session and start a fresh one
    page.get_by_test_id("end-session-btn").click()
    expect(page.get_by_test_id("session-completed-banner")).to_be_visible()
    page.get_by_test_id("start-new-session-link").click()
    page.wait_for_load_state("networkidle")

    # The new session has the placeholder title
    expect(page.get_by_test_id("session-item").first).to_contain_text("New session")

    # Send a message — the placeholder title should be replaced
    page.get_by_test_id("chat-input").fill("I want to become a better leader")
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_test_id("session-item").first).not_to_contain_text("New session")
    expect(page.get_by_test_id("session-item").first).to_contain_text(
        "I want to become a better leader"
    )


@pytest.mark.e2e
def test_new_session_after_chat_gives_empty_chat_and_two_sessions(page: Page) -> None:
    """After chatting, creating a new session clears the chat panel and adds a second session."""
    # Chat once to populate the Introduction session
    page.get_by_test_id("chat-input").fill("Hello")
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")

    # Confirm there is a coach reply in the chat panel
    expect(page.get_by_text("Coach: Hello")).to_be_visible()

    # Create a new session (the Introduction session now has messages, so it gets completed)
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")

    # Chat panel should be empty (the placeholder text is shown)
    expect(page.get_by_text("Start a conversation with your coach.")).to_be_visible()

    # Sidebar should list two sessions
    expect(page.get_by_test_id("session-item")).to_have_count(2)
