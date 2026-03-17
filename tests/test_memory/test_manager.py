"""Tests for MemoryManager session state management."""

from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState


def test_create_empty_state_returns_session_state_with_empty_history(
    manager: MemoryManager,
) -> None:
    """create_empty_state() returns a SessionState with no conversation messages."""
    state = manager.create_empty_state("test_user")
    assert isinstance(state, SessionState)
    assert state.conversation_history == []


def test_add_user_message_appends_message_with_role_user(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """add_user_message() appends a dict with role='user' to conversation_history."""
    updated = manager.add_user_message(empty_state, "Hello coach!")
    assert len(updated.conversation_history) == 1
    assert updated.conversation_history[0] == {"role": "user", "content": "Hello coach!"}


def test_update_from_output_updates_coaching_phase(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """update_from_output() stores the coaching_phase from coach output."""
    output = {
        "coaching_phase": "EXPLORATION",
        "response": "Let's explore that.",
    }
    updated = manager.update_from_output(empty_state, output)
    assert updated.current_phase == "EXPLORATION"


def test_update_from_output_accumulates_emotions_without_duplicates(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """Emotions are accumulated across calls; duplicates are ignored."""
    state = manager.update_from_output(
        empty_state, {"detected_emotions": ["fear", "joy"], "response": "ok"}
    )
    state = manager.update_from_output(
        state, {"detected_emotions": ["joy", "hope"], "response": "ok"}
    )
    assert state.detected_emotions == ["fear", "joy", "hope"]


def test_update_from_output_increments_open_questions_count(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """open_questions_count increases by 1 for each OPEN question type."""
    output = {"question_type": "OPEN", "response": "What do you think?"}
    updated = manager.update_from_output(empty_state, output)
    assert updated.open_questions_count == 1


def test_update_from_output_increments_paraphrases_count(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """paraphrases_count increases by 1 for each PARAPHRASE question type."""
    output = {"question_type": "PARAPHRASE", "response": "I hear that you feel..."}
    updated = manager.update_from_output(empty_state, output)
    assert updated.paraphrases_count == 1


def test_get_recent_history_with_limit_returns_last_n_messages(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """get_recent_history() returns at most `limit` messages from the end."""
    state = empty_state
    for i in range(5):
        state = manager.add_user_message(state, f"message {i}")

    recent = manager.get_recent_history(state, limit=3)
    assert len(recent) == 3
    assert recent[-1]["content"] == "message 4"
    assert recent[0]["content"] == "message 2"
