# -*- coding: utf-8 -*-
"""
Memory Manager - manages coaching session state.
"""

from memory.schemas.session_state import SessionState
import copy

class MemoryManager:
    """
    Manages memory updates based on coach responses.
    """

    def create_empty_state(self, user_id: str) -> SessionState:
        """Initialize empty state for a new user."""
        return SessionState(
            user_id=user_id,
            user_name=None,
            conversation_history=[]
        )

    def update_from_output(self, state: SessionState, coach_output: dict) -> SessionState:
        """
        Main state update logic based on LLM analysis.
        Maps Structured Output to persistent session memory.
        """
        # 1. Create a safe copy of state (immutability)
        updated_state = state.model_copy(deep=True)

        # 2. Update user identity (LC-002)
        if "user_name" in coach_output and coach_output["user_name"]:
            updated_state.user_name = coach_output["user_name"]

        if "main_goal" in coach_output and coach_output["main_goal"]:
            updated_state.main_goal = coach_output["main_goal"]

        # 3. Manage coaching phase
        if "coaching_phase" in coach_output:
            updated_state.current_phase = coach_output["coaching_phase"]

        # 4. Accumulate detected emotions (LC-011)
        if "detected_emotions" in coach_output:
            for emotion in coach_output["detected_emotions"]:
                if emotion not in updated_state.detected_emotions:
                    updated_state.detected_emotions.append(emotion)

        # 5. Update quality counters (LC-004, LC-005)
        q_type = coach_output.get("question_type")
        if q_type == "OPEN":
            updated_state.open_questions_count += 1
        elif q_type == "PARAPHRASE":
            updated_state.paraphrases_count += 1

        # 6. Save response to dialog history
        # Note: key may be 'ai_response' or 'response' depending on the model
        final_text = coach_output.get("ai_response") or coach_output.get("response")
        if final_text:
            updated_state.conversation_history.append({
                "role": "assistant",
                "content": final_text
            })

        return updated_state

    def add_user_message(self, state: SessionState, message: str) -> SessionState:
        """Add a user message to conversation history."""
        updated_state = state.model_copy(deep=True)
        updated_state.conversation_history.append({
            "role": "user",
            "content": message
        })
        return updated_state

    def get_recent_history(self, state: SessionState, limit: int = 10) -> list[dict]:
        """Retrieve the last N messages as context."""
        return state.conversation_history[-limit:]
