"""
End-to-end tests for session metadata display in the sidebar.

Covers: phase badge, detected emotions, and goal display.
The fake coach returns detected_emotions: ["curiosity"] on every reply
and extracts main_goal when the message starts with "My goal is ".
"""

import pytest
from playwright.sync_api import Page, expect


def send_message(page: Page, text: str) -> None:
    """Type a message and click Send, then wait for the reply."""
    page.get_by_test_id("chat-input").fill(text)
    page.get_by_test_id("send-btn").click()
    page.wait_for_load_state("networkidle")


# ---------------------------------------------------------------------------
# Phase badge
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_phase_shows_introduction_before_chat(page: Page) -> None:
    """Before any messages, the sidebar shows the Introduction phase badge."""
    # The word "Introduction" appears both as session title and phase badge.
    # Target the phase badge specifically (the indigo rounded-full span in the sidebar).
    phase_badge = page.locator("aside span.bg-indigo-100", has_text="Introduction")
    expect(phase_badge).to_be_visible()


@pytest.mark.e2e
def test_phase_updates_after_chat(page: Page) -> None:
    """After sending a message, the phase updates to Context Gathering."""
    send_message(page, "Hello")

    # The fake coach always returns CONTEXT_GATHERING
    expect(page.get_by_text("Context Gathering")).to_be_visible()


# ---------------------------------------------------------------------------
# Emotions
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_emotions_displayed_after_chat(page: Page) -> None:
    """After sending a message, detected emotions appear as badges."""
    send_message(page, "I feel worried")

    # The fake coach always returns ["curiosity"]
    expect(page.get_by_text("curiosity")).to_be_visible()


# ---------------------------------------------------------------------------
# Goal
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_goal_displayed_when_extracted(page: Page) -> None:
    """When the coach extracts a goal, it appears in the sidebar."""
    send_message(page, "My goal is get promoted to senior engineer")

    # The goal text also appears in the chat (user message + echo). Target the sidebar.
    sidebar_goal = page.locator("aside").get_by_text("get promoted to senior engineer")
    expect(sidebar_goal).to_be_visible()


@pytest.mark.e2e
def test_goal_not_shown_before_extraction(page: Page) -> None:
    """Before a goal is extracted, the Goal section is not shown."""
    # The word "Goal" appears as the section heading only when mainGoal is set.
    # With no messages sent, mainGoal is null so the heading shouldn't exist.
    # Send a normal message (no "My goal is" prefix) — goal stays empty.
    send_message(page, "Just chatting")

    # The sidebar shows "Phase" and "Emotions" but the "Goal" label
    # should not appear since mainGoal is still null.
    sidebar = page.locator("aside")
    expect(sidebar.get_by_text("Goal", exact=True)).not_to_be_visible()


# ---------------------------------------------------------------------------
# Closing prompt
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_closing_prompt_shown_when_coach_enters_closing(page: Page) -> None:
    """When the coach enters CLOSING phase, an amber prompt banner appears."""
    send_message(page, "please close")

    expect(page.get_by_text("Your coach has wrapped up this session.")).to_be_visible()
