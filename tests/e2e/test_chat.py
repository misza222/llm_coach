"""
End-to-end tests for chat interaction.

Covers: sending messages, receiving replies, input behaviour, empty state,
Enter-to-send, and completed-session behaviour.
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
# Empty state
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_empty_chat_shows_placeholder(page: Page) -> None:
    """A fresh session shows the placeholder message before any chat."""
    expect(page.get_by_text("Start a conversation with your coach.")).to_be_visible()


@pytest.mark.e2e
def test_send_button_disabled_when_input_empty(page: Page) -> None:
    """Send button is disabled when the input is empty."""
    send_btn = page.get_by_test_id("send-btn")
    expect(send_btn).to_be_disabled()


# ---------------------------------------------------------------------------
# Sending messages
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_send_message_shows_user_and_coach_messages(page: Page) -> None:
    """Sending a message displays both the user message and the coach reply."""
    send_message(page, "Hello coach")

    expect(page.get_by_text("Hello coach", exact=True)).to_be_visible()
    expect(page.get_by_text("Coach: Hello coach")).to_be_visible()


@pytest.mark.e2e
def test_placeholder_disappears_after_first_message(page: Page) -> None:
    """The empty-state placeholder is gone after the first message."""
    send_message(page, "Hi")

    expect(page.get_by_text("Start a conversation with your coach.")).not_to_be_visible()


@pytest.mark.e2e
def test_input_clears_after_sending(page: Page) -> None:
    """The input textarea is empty after sending a message."""
    send_message(page, "Some message")

    chat_input = page.get_by_test_id("chat-input")
    expect(chat_input).to_have_value("")


@pytest.mark.e2e
def test_multiple_messages_accumulate(page: Page) -> None:
    """Sending several messages builds up the conversation history."""
    send_message(page, "First")
    send_message(page, "Second")
    send_message(page, "Third")

    expect(page.get_by_text("Coach: First")).to_be_visible()
    expect(page.get_by_text("Coach: Second")).to_be_visible()
    expect(page.get_by_text("Coach: Third")).to_be_visible()


@pytest.mark.e2e
def test_send_via_enter_key(page: Page) -> None:
    """Pressing Enter (without Shift) sends the message."""
    page.get_by_test_id("chat-input").fill("Enter test")
    page.get_by_test_id("chat-input").press("Enter")
    page.wait_for_load_state("networkidle")

    expect(page.get_by_text("Coach: Enter test")).to_be_visible()


# ---------------------------------------------------------------------------
# Completed session
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_completed_session_shows_banner_with_start_link(page: Page) -> None:
    """After ending a session, the banner shows a 'Start a new session' link."""
    end_session(page)

    expect(page.get_by_test_id("session-completed-banner")).to_be_visible()
    expect(page.get_by_test_id("start-new-session-link")).to_be_visible()


@pytest.mark.e2e
def test_start_new_session_link_creates_session(page: Page) -> None:
    """Clicking the banner link creates a new session and clears the chat."""
    end_session(page)
    page.get_by_test_id("start-new-session-link").click()
    page.wait_for_load_state("networkidle")

    expect(page.get_by_test_id("session-completed-banner")).not_to_be_visible()
    expect(page.get_by_text("Start a conversation with your coach.")).to_be_visible()
    expect(page.get_by_test_id("session-item")).to_have_count(2)
