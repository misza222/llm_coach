"""
End-to-end tests for session management flows.

Each test uses the `fresh_browser_state` autouse fixture (defined in conftest.py)
which navigates to the app, clears localStorage, and reloads so every test
begins with a fresh anonymous user and a single "Introduction" session.

Run with:
    uv run pytest tests/e2e/ -v

The frontend must be built before running:
    cd frontend && npm run build
"""

import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def end_session(page: Page) -> None:
    """Click End Session and confirm — goes through the two-step confirmation."""
    page.get_by_test_id("end-session-btn").click()
    page.get_by_test_id("confirm-end-btn").click()
    page.wait_for_load_state("networkidle")


# ---------------------------------------------------------------------------
# Session sidebar tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_first_visit_shows_introduction_session(page: Page) -> None:
    """A brand-new user sees exactly one session named 'Introduction' in the sidebar."""
    items = page.get_by_test_id("session-item")
    expect(items).to_have_count(1)
    expect(items.first).to_contain_text("Introduction")


@pytest.mark.e2e
def test_new_session_button_not_visible_during_active_session(page: Page) -> None:
    """'New Session' is hidden while a session is active — only 'End Session' is shown."""
    expect(page.get_by_test_id("end-session-btn")).to_be_visible()
    expect(page.get_by_test_id("new-session-btn")).not_to_be_visible()


# ---------------------------------------------------------------------------
# End Session confirmation tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_end_session_shows_confirmation_ui(page: Page) -> None:
    """Clicking End Session shows inline confirmation buttons instead of ending immediately."""
    page.get_by_test_id("end-session-btn").click()

    expect(page.get_by_test_id("confirm-end-btn")).to_be_visible()
    expect(page.get_by_test_id("cancel-end-btn")).to_be_visible()
    # The original End Session button is replaced by the confirmation UI
    expect(page.get_by_test_id("end-session-btn")).not_to_be_visible()


@pytest.mark.e2e
def test_cancel_end_session_restores_end_button(page: Page) -> None:
    """Cancelling the confirmation brings back the End Session button without ending."""
    page.get_by_test_id("end-session-btn").click()
    page.get_by_test_id("cancel-end-btn").click()

    # Session is still active
    expect(page.get_by_test_id("end-session-btn")).to_be_visible()
    expect(page.get_by_test_id("session-completed-banner")).not_to_be_visible()


@pytest.mark.e2e
def test_end_session_confirmed_shows_completion_banner(page: Page) -> None:
    """Confirming End Session marks the session done and shows the completion banner."""
    end_session(page)

    expect(page.get_by_test_id("session-completed-banner")).to_be_visible()
    expect(page.get_by_test_id("end-session-btn")).not_to_be_visible()


@pytest.mark.e2e
def test_end_session_marks_session_done_in_sidebar(page: Page) -> None:
    """After confirming End Session the sidebar shows the 'done' badge."""
    end_session(page)

    expect(page.get_by_test_id("session-item").first).to_contain_text("done")


@pytest.mark.e2e
def test_end_session_replaces_end_button_with_new_session_button(page: Page) -> None:
    """After ending, 'New Session' appears in place of 'End Session'."""
    end_session(page)

    expect(page.get_by_test_id("new-session-btn")).to_be_visible()
    expect(page.get_by_test_id("end-session-btn")).not_to_be_visible()


# ---------------------------------------------------------------------------
# New Session flow tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_new_session_after_ending_creates_fresh_session(page: Page) -> None:
    """Clicking New Session after ending opens a fresh chat and adds a second sidebar entry."""
    end_session(page)
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_test_id("session-completed-banner")).not_to_be_visible()
    expect(page.get_by_test_id("session-item")).to_have_count(2)
    # New session is active again — End Session button is back
    expect(page.get_by_test_id("end-session-btn")).to_be_visible()


@pytest.mark.e2e
def test_new_session_after_chat_gives_empty_panel_and_two_sessions(page: Page) -> None:
    """After chatting, ending, and starting a new session: panel clears, sidebar has two entries."""
    page.get_by_test_id("chat-input").fill("Hello")
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("Coach: Hello")).to_be_visible()

    end_session(page)
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_text("Start a conversation with your coach.")).to_be_visible()
    expect(page.get_by_test_id("session-item")).to_have_count(2)


# ---------------------------------------------------------------------------
# Session title tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_first_session_title_stays_introduction_after_chat(page: Page) -> None:
    """The 'Introduction' title is preserved even after the user sends their first message."""
    page.get_by_test_id("chat-input").fill("I want to become a better leader")
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_test_id("session-item").first).to_contain_text("Introduction")


@pytest.mark.e2e
def test_second_session_title_updates_from_first_message(page: Page) -> None:
    """A second session starts as 'New session' and gets titled from the first user message."""
    end_session(page)
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")

    # Newest session (first in list) has the placeholder title
    expect(page.get_by_test_id("session-item").first).to_contain_text("New session")

    page.get_by_test_id("chat-input").fill("I want to become a better leader")
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_test_id("session-item").first).not_to_contain_text("New session")
    expect(page.get_by_test_id("session-item").first).to_contain_text(
        "I want to become a better leader"
    )
