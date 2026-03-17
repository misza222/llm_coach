# -*- coding: utf-8 -*-
"""
Coach Agent - main coaching agent with Structured Output.
"""

from engine.client import call_llm
from engine.prompter import SystemPrompter
from memory.schemas.session_state import SessionState
from memory.schemas.coach_types import CoachResponseAnalysis, CoachingPhase
from memory.logic.manager import MemoryManager
from config import Config


class CoachAgent:
    """
    Main coaching agent.

    Uses:
    - SystemPrompter for dynamic system prompt construction
    - Structured Output (CoachResponseAnalysis) to enforce Chain of Thought
    """

    def __init__(self):
        """Initialize CoachAgent."""
        self.memory_manager = MemoryManager()
        self.prompter = SystemPrompter()

    def respond(self, user_message: str, state: SessionState) -> tuple[str, SessionState]:
        """
        Generate a coach response using Structured Output.
        """
        # 1. Add user message to history
        state = self.memory_manager.add_user_message(state, user_message)

        # 2. Retrieve recent message context
        recent_history = self.memory_manager.get_recent_history(
            state,
            limit=Config.MAX_HISTORY_MESSAGES
        )

        # 3. Build system prompt dynamically (inject state from memory)
        system_prompt = self.prompter.build_system_prompt(
            core={
                "coach_name": Config.COACH_NAME,
            },
            profile={
                "user_name": state.user_name,
                "main_goal": state.main_goal
            },
            session={
                "phase": getattr(state, 'current_phase', "INTRODUCTION"),
                "turn_count": len(state.conversation_history) // 2,
                "detected_emotions": state.detected_emotions
            },
            history=recent_history
        )

        # 4. Prepare message structure for API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_history)

        # 5. === STRUCTURED OUTPUT ===
        # Call LLM and expect a specific data model in return
        response: CoachResponseAnalysis = call_llm(
            messages,
            response_model=CoachResponseAnalysis
        )

        # 6. === STATE UPDATE ===
        # Map structured response to persistent session memory
        state = self.memory_manager.update_from_output(
            state,
            {
                "response": response.ai_response,
                "coaching_phase": response.coaching_phase.value,
                "detected_emotions": response.detected_emotions,
                "question_type": response.question_type.value,
                "analysis_summary": response.analysis_summary,
            }
        )

        if Config.DEBUG:
            print(f"[CoachAgent] Phase: {response.coaching_phase}")
            print(f"[CoachAgent] Thoughts: {response.analysis_summary[:50]}...")

        return response.ai_response, state
