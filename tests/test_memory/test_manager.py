"""Tests for MemoryManager session state management."""

from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend


def test_create_empty_state_returns_session_state_with_empty_history(
    manager: MemoryManager,
) -> None:
    """create_empty_state() returns a SessionState with no conversation messages."""
    state = manager.create_empty_state("test_user")
    assert isinstance(state, SessionState)
    assert state.conversation_history == []
    assert state.session_id  # auto-generated


def test_add_user_message_appends_message_with_role_user(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """add_user_message() appends a dict with role='user' to conversation_history."""
    updated = manager.add_user_message(empty_state, "Hello coach!")
    assert len(updated.conversation_history) == 1
    assert updated.conversation_history[0] == {"role": "user", "content": "Hello coach!"}


def test_add_user_message_replaces_default_title_with_first_message(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """First user message replaces the None/placeholder title."""
    updated = manager.add_user_message(empty_state, "I want to improve my career")
    assert updated.title == "I want to improve my career"


def test_create_empty_state_has_default_placeholder_title(manager: MemoryManager) -> None:
    """create_empty_state() sets title to 'New session' placeholder for subsequent sessions."""
    state = manager.create_empty_state("user-1")
    assert state.title == "New session"


def test_create_empty_state_with_is_first_uses_introduction_title(
    manager: MemoryManager,
) -> None:
    """create_empty_state(is_first=True) sets a fixed 'Introduction' title."""
    state = manager.create_empty_state("user-1", is_first=True)
    assert state.title == "Introduction"


def test_introduction_title_is_not_replaced_by_first_message(
    manager: MemoryManager,
) -> None:
    """The 'Introduction' title is never auto-replaced by user message content."""
    state = manager.create_empty_state("user-1", is_first=True)
    updated = manager.add_user_message(state, "I want to grow as a leader")
    assert updated.title == "Introduction"


def test_introduction_title_is_not_replaced_by_main_goal(
    manager: MemoryManager,
) -> None:
    """The 'Introduction' title is never auto-replaced when main_goal is extracted."""
    state = manager.create_empty_state("user-1", is_first=True)
    updated, _ = manager.update_from_output(
        state, {"main_goal": "Become a better leader", "response": "Great."}
    )
    assert updated.title == "Introduction"


def test_update_from_output_updates_coaching_phase(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """update_from_output() stores the coaching_phase from coach output."""
    output = {
        "coaching_phase": "EXPLORATION",
        "response": "Let's explore that.",
    }
    updated, is_closing = manager.update_from_output(empty_state, output)
    assert updated.current_phase == "EXPLORATION"
    assert is_closing is False


def test_update_from_output_detects_closing_phase(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """update_from_output() returns is_closing=True when phase is CLOSING."""
    output = {
        "coaching_phase": "CLOSING",
        "response": "Great session!",
    }
    updated, is_closing = manager.update_from_output(empty_state, output)
    assert updated.current_phase == "CLOSING"
    assert is_closing is True


def test_update_from_output_accumulates_emotions_without_duplicates(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """Emotions are accumulated across calls; duplicates are ignored."""
    state, _ = manager.update_from_output(
        empty_state, {"detected_emotions": ["fear", "joy"], "response": "ok"}
    )
    state, _ = manager.update_from_output(
        state, {"detected_emotions": ["joy", "hope"], "response": "ok"}
    )
    assert state.detected_emotions == ["fear", "joy", "hope"]


def test_update_from_output_increments_open_questions_count(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """open_questions_count increases by 1 for each OPEN question type."""
    output = {"question_type": "OPEN", "response": "What do you think?"}
    updated, _ = manager.update_from_output(empty_state, output)
    assert updated.open_questions_count == 1


def test_update_from_output_increments_paraphrases_count(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """paraphrases_count increases by 1 for each PARAPHRASE question type."""
    output = {"question_type": "PARAPHRASE", "response": "I hear that you feel..."}
    updated, _ = manager.update_from_output(empty_state, output)
    assert updated.paraphrases_count == 1


def test_update_from_output_auto_generates_title_from_main_goal(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """Title is auto-set from main_goal when first provided."""
    output = {
        "main_goal": "Get promoted to senior",
        "response": "Let's work on that.",
    }
    updated, _ = manager.update_from_output(empty_state, output)
    assert updated.title == "Get promoted to senior"


def test_complete_session_sets_status_and_timestamp(
    manager: MemoryManager, empty_state: SessionState
) -> None:
    """complete_session() sets status to COMPLETED with a timestamp."""
    completed = manager.complete_session(empty_state)
    assert completed.status == "COMPLETED"
    assert completed.completed_at is not None


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


# --- Cross-session context tests ---


def test_build_cross_session_context_returns_empty_for_new_user(
    manager: MemoryManager,
) -> None:
    """build_cross_session_context() returns empty profile and sessions for unknown user."""
    storage = InMemoryBackend()
    result = manager.build_cross_session_context("new_user", storage)
    assert result["user_profile"] is None
    assert result["past_sessions"] == []


def test_build_cross_session_context_includes_completed_sessions(
    manager: MemoryManager,
) -> None:
    """build_cross_session_context() returns summaries only for completed sessions."""
    storage = InMemoryBackend()
    # Save one completed and one active session
    storage.save(
        "s1",
        {
            "session_id": "s1",
            "user_id": "alice",
            "status": "COMPLETED",
            "title": "Career growth",
            "main_goal": "Get promoted",
            "key_insights": ["I need to be more visible"],
            "action_plan": "Speak up in meetings",
            "detected_emotions": ["determination"],
            "current_phase": "CLOSING",
            "completed_at": "2025-01-01T10:00:00",
            "created_at": "2025-01-01T09:00:00",
        },
    )
    storage.save(
        "s2",
        {
            "session_id": "s2",
            "user_id": "alice",
            "status": "ACTIVE",
            "title": "New session",
            "created_at": "2025-01-02T09:00:00",
        },
    )

    result = manager.build_cross_session_context("alice", storage)
    assert len(result["past_sessions"]) == 1
    assert result["past_sessions"][0]["main_goal"] == "Get promoted"


def test_build_cross_session_context_respects_max_past_sessions(
    manager: MemoryManager,
) -> None:
    """build_cross_session_context() limits returned sessions to max_past_sessions."""
    storage = InMemoryBackend()
    for i in range(5):
        storage.save(
            f"s{i}",
            {
                "session_id": f"s{i}",
                "user_id": "alice",
                "status": "COMPLETED",
                "created_at": f"2025-01-0{i + 1}T09:00:00",
            },
        )

    result = manager.build_cross_session_context("alice", storage, max_past_sessions=2)
    assert len(result["past_sessions"]) == 2


def test_update_user_profile_creates_profile_for_first_session(
    manager: MemoryManager,
) -> None:
    """update_user_profile() creates a new profile when none exists."""
    storage = InMemoryBackend()
    completed = SessionState(
        user_id="alice",
        user_name="Alice",
        main_goal="Get promoted",
        action_plan="Speak up",
        detected_emotions=["hope", "fear"],
        key_insights=["I hold back too much"],
        status="COMPLETED",
    )

    manager.update_user_profile("alice", storage, completed)

    profile = storage.load_user_profile("alice")
    assert profile is not None
    assert profile["user_name"] == "Alice"
    assert profile["completed_session_count"] == 1
    assert profile["last_session_goal"] == "Get promoted"
    assert set(profile["all_time_emotions"]) == {"hope", "fear"}
    assert "I hold back too much" in profile["all_time_insights"]


def test_update_user_profile_accumulates_across_sessions(
    manager: MemoryManager,
) -> None:
    """update_user_profile() merges data from multiple sessions."""
    storage = InMemoryBackend()

    session_1 = SessionState(
        user_id="alice",
        user_name="Alice",
        main_goal="Goal A",
        detected_emotions=["hope"],
        key_insights=["Insight 1"],
        status="COMPLETED",
    )
    manager.update_user_profile("alice", storage, session_1)

    session_2 = SessionState(
        user_id="alice",
        user_name="Alice W.",
        main_goal="Goal B",
        detected_emotions=["hope", "joy"],
        key_insights=["Insight 2"],
        status="COMPLETED",
    )
    manager.update_user_profile("alice", storage, session_2)

    profile = storage.load_user_profile("alice")
    assert profile is not None
    assert profile["user_name"] == "Alice W."  # latest wins
    assert profile["completed_session_count"] == 2
    assert profile["last_session_goal"] == "Goal B"
    # Emotions are deduplicated union
    assert set(profile["all_time_emotions"]) == {"hope", "joy"}
    # Insights accumulated
    assert "Insight 1" in profile["all_time_insights"]
    assert "Insight 2" in profile["all_time_insights"]
