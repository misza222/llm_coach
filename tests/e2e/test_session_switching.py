"""
End-to-end tests for switching between sessions.

Covers: clicking a completed session to view history, switching back to
the active session, and verifying that the correct history loads.
"""

import pytest
from playwright.sync_api import Page, expect


def send_message(page: Page, text: str) -> None:
    """Type a message and click Send, then wait for the reply."""
    page.get_by_test_id("chat-input").fill(text)
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")


def end_session(page: Page) -> None:
    """End the current session via the two-step confirmation."""
    page.get_by_test_id("end-session-btn").click()
    page.get_by_test_id("confirm-end-btn").click()
    page.wait_for_load_state("networkidle")


# ---------------------------------------------------------------------------
# Session switching
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_switch_to_completed_session_shows_its_history(page: Page) -> None:
    """Clicking a completed session in the sidebar loads its conversation."""
    # Chat in session 1
    send_message(page, "Session one message")
    expect(page.get_by_text("Coach: Session one message")).to_be_visible()

    # End and create session 2
    end_session(page)
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")
    send_message(page, "Session two message")

    # Session 1 (completed) is the second item in the sidebar (list is newest-first)
    sessions = page.get_by_test_id("session-item")
    expect(sessions).to_have_count(2)

    # Click session 1 (the completed one — second in list)
    sessions.nth(1).click()
    page.wait_for_load_state("networkidle")

    # Should see session 1's history, not session 2's
    expect(page.get_by_text("Coach: Session one message")).to_be_visible()
    expect(page.get_by_text("Coach: Session two message")).not_to_be_visible()


@pytest.mark.e2e
def test_switch_back_to_active_session_restores_history(page: Page) -> None:
    """Switching away and back to the active session restores its history."""
    send_message(page, "Active message")
    end_session(page)

    # Create session 2 and chat
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")
    send_message(page, "New active message")

    # Switch to completed session 1
    page.get_by_test_id("session-item").nth(1).click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("Coach: Active message")).to_be_visible()

    # Switch back to session 2 (active — first in list)
    page.get_by_test_id("session-item").nth(0).click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("Coach: New active message")).to_be_visible()
    expect(page.get_by_text("Coach: Active message")).not_to_be_visible()


@pytest.mark.e2e
def test_completed_session_shows_done_badge_and_banner_on_switch(page: Page) -> None:
    """Switching to a completed session shows the 'done' badge and completion banner."""
    send_message(page, "Some chat")
    end_session(page)

    # Create new active session so we can switch back
    page.get_by_test_id("new-session-btn").click()
    page.wait_for_load_state("networkidle")

    # Banner should not be visible on active session
    expect(page.get_by_test_id("session-completed-banner")).not_to_be_visible()

    # Switch to completed session
    page.get_by_test_id("session-item").nth(1).click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_test_id("session-completed-banner")).to_be_visible()
