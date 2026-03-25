"""
Memory Manager - manages coaching session state.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.memory.schemas.user_profile import (
    CompletedSessionSummary,
    UserProfile,
)

if TYPE_CHECKING:
    from life_coach_system.persistence.backend import PersistenceBackend

_MAX_TITLE_LENGTH = 60
_MAX_PROFILE_INSIGHTS = 20
# Placeholder replaced by auto-generated title once user starts talking
_DEFAULT_TITLE = "New session"
# Fixed title for a user's very first session — never auto-replaced
_FIRST_SESSION_TITLE = "Introduction"


class MemoryManager:
    """
    Manages memory updates based on coach responses.
    """

    def create_empty_state(self, user_id: str, *, is_first: bool = False) -> SessionState:
        """Initialize empty state for a new session.

        Args:
            user_id: Owner of the session.
            is_first: When True, uses a fixed "Introduction" title that is never
                auto-replaced. Subsequent sessions use a placeholder title that
                gets replaced once the user starts talking.
        """
        title = _FIRST_SESSION_TITLE if is_first else _DEFAULT_TITLE
        return SessionState(
            user_id=user_id,
            user_name=None,
            conversation_history=[],
            title=title,
        )

    def update_from_output(
        self, state: SessionState, coach_output: dict
    ) -> tuple[SessionState, bool]:
        """
        Main state update logic based on LLM analysis.
        Maps Structured Output to persistent session memory.

        Returns (updated_state, is_closing) where is_closing indicates
        the coach has entered the CLOSING phase.
        """
        # 1. Create a safe copy of state (immutability)
        updated_state = state.model_copy(deep=True)

        # 2. Update user identity (LC-002)
        if "user_name" in coach_output and coach_output["user_name"]:
            updated_state.user_name = coach_output["user_name"]

        if "main_goal" in coach_output and coach_output["main_goal"]:
            updated_state.main_goal = coach_output["main_goal"]

        # 3. Auto-generate title from main_goal when first set (replaces default placeholder)
        if updated_state.main_goal and updated_state.title in (None, _DEFAULT_TITLE):
            updated_state.title = updated_state.main_goal[:_MAX_TITLE_LENGTH]

        # 4. Manage coaching phase
        is_closing = False
        if "coaching_phase" in coach_output:
            updated_state.current_phase = coach_output["coaching_phase"]
            if coach_output["coaching_phase"] == "CLOSING":
                is_closing = True

        # 5. Accumulate detected emotions (LC-011)
        if "detected_emotions" in coach_output:
            for emotion in coach_output["detected_emotions"]:
                if emotion not in updated_state.detected_emotions:
                    updated_state.detected_emotions.append(emotion)

        # 6. Update quality counters (LC-004, LC-005)
        q_type = coach_output.get("question_type")
        if q_type == "OPEN":
            updated_state.open_questions_count += 1
        elif q_type == "PARAPHRASE":
            updated_state.paraphrases_count += 1

        # 7. Save response to dialog history
        final_text = coach_output.get("ai_response") or coach_output.get("response")
        if final_text:
            updated_state.conversation_history.append({"role": "assistant", "content": final_text})

        return updated_state, is_closing

    def add_user_message(self, state: SessionState, message: str) -> SessionState:
        """Add a user message to conversation history."""
        updated_state = state.model_copy(deep=True)
        updated_state.conversation_history.append({"role": "user", "content": message})

        # Auto-generate title from first user message if still at default placeholder
        if updated_state.title in (None, _DEFAULT_TITLE):
            updated_state.title = message[:_MAX_TITLE_LENGTH]

        return updated_state

    def complete_session(self, state: SessionState) -> SessionState:
        """Mark a session as completed."""
        updated_state = state.model_copy(deep=True)
        updated_state.status = "COMPLETED"
        updated_state.completed_at = datetime.now().isoformat()
        return updated_state

    def get_recent_history(self, state: SessionState, *, limit: int = 10) -> list[dict]:
        """Retrieve the last N messages as context."""
        return state.conversation_history[-limit:]

    def build_cross_session_context(
        self,
        user_id: str,
        storage: PersistenceBackend,
        *,
        max_past_sessions: int = 3,
    ) -> dict[str, Any]:
        """Build cross-session context for the system prompt.

        Loads the user profile and summaries of recent completed sessions
        so the coach can provide continuity across sessions.
        """
        profile_dict = storage.load_user_profile(user_id)

        # Collect completed session summaries (most recent first)
        session_summaries = storage.list_sessions(user_id)
        completed_summaries: list[dict] = []
        for summary in session_summaries:
            if summary.get("status") != "COMPLETED":
                continue
            if len(completed_summaries) >= max_past_sessions:
                break
            state_dict = storage.load(summary["session_id"])
            if state_dict is None:
                continue
            completed_summaries.append(
                CompletedSessionSummary(
                    session_id=state_dict.get("session_id", ""),
                    title=state_dict.get("title"),
                    main_goal=state_dict.get("main_goal"),
                    key_insights=state_dict.get("key_insights", []),
                    action_plan=state_dict.get("action_plan"),
                    detected_emotions=state_dict.get("detected_emotions", []),
                    final_phase=state_dict.get("current_phase"),
                    completed_at=state_dict.get("completed_at"),
                ).model_dump()
            )

        return {
            "user_profile": profile_dict,
            "past_sessions": completed_summaries,
        }

    def update_user_profile(
        self,
        user_id: str,
        storage: PersistenceBackend,
        completed_state: SessionState,
    ) -> None:
        """Materialize cross-session user profile after session completion.

        Merges data from the completed session into the accumulated profile
        and persists it via the storage backend.
        """
        existing = storage.load_user_profile(user_id)
        if existing is not None:
            profile = UserProfile(**existing)
        else:
            profile = UserProfile(user_id=user_id)

        # Carry forward user_name (latest wins)
        if completed_state.user_name:
            profile.user_name = completed_state.user_name

        # Merge emotions (deduplicated union)
        existing_emotions = set(profile.all_time_emotions)
        for emotion in completed_state.detected_emotions:
            if emotion not in existing_emotions:
                profile.all_time_emotions.append(emotion)
                existing_emotions.add(emotion)

        # Append insights, cap at max
        for insight in completed_state.key_insights:
            if insight not in profile.all_time_insights:
                profile.all_time_insights.append(insight)
        profile.all_time_insights = profile.all_time_insights[-_MAX_PROFILE_INSIGHTS:]

        # Last session data
        profile.last_session_goal = completed_state.main_goal
        profile.last_session_action_plan = completed_state.action_plan
        profile.completed_session_count += 1
        profile.updated_at = datetime.now().isoformat()

        storage.save_user_profile(user_id, profile.model_dump())
