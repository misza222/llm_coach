"""
Coach Agent - main coaching agent with Structured Output.
"""

from life_coach_system._logging import get_logger
from life_coach_system.config import settings
from life_coach_system.engine.client import call_llm
from life_coach_system.engine.prompter import SystemPrompter
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.coach_types import (  # noqa: F401
    CoachingPhase,
    CoachResponseAnalysis,
)
from life_coach_system.memory.schemas.session_state import SessionState

log = get_logger(__name__)


class CoachAgent:
    """
    Main coaching agent.

    Uses:
    - SystemPrompter for dynamic system prompt construction
    - Structured Output (CoachResponseAnalysis) to enforce Chain of Thought
    """

    def __init__(self) -> None:
        """Initialize CoachAgent."""
        self.memory_manager = MemoryManager()
        self.prompter = SystemPrompter()

    def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState, bool]:
        """
        Generate a coach response using Structured Output.

        Returns (response_text, updated_state, is_closing).
        """
        # 1. Add user message to history
        state = self.memory_manager.add_user_message(state, user_message)

        # 2. Retrieve recent message context
        recent_history = self.memory_manager.get_recent_history(
            state, limit=settings.max_history_messages
        )

        # 3. Build system prompt dynamically (inject state from memory)
        system_prompt = self.prompter.build_system_prompt(
            core={
                "coach_name": settings.coach_name,
            },
            profile={"user_name": state.user_name, "main_goal": state.main_goal},
            session={
                "phase": getattr(state, "current_phase", "INTRODUCTION"),
                "turn_count": len(state.conversation_history) // 2,
                "detected_emotions": state.detected_emotions,
            },
            history=recent_history,
        )

        # 4. Prepare message structure for API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_history)

        # 5. === STRUCTURED OUTPUT ===
        response: CoachResponseAnalysis = call_llm(messages, response_model=CoachResponseAnalysis)

        # 6. === STATE UPDATE ===
        state, is_closing = self.memory_manager.update_from_output(
            state,
            {
                "response": response.ai_response,
                "coaching_phase": response.coaching_phase.value,
                "detected_emotions": response.detected_emotions,
                "question_type": response.question_type.value,
                "analysis_summary": response.analysis_summary,
            },
        )

        if settings.debug:
            log.debug(
                "coach_response",
                phase=str(response.coaching_phase),
                thoughts=response.analysis_summary[:50],
            )

        return response.ai_response, state, is_closing
