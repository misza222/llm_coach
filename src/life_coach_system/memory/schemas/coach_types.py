"""
Coach-specific types and enums.

This module contains types specific to the coaching process.
"""

from enum import Enum

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Lifecycle status of a coaching session."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class CoachingPhase(str, Enum):
    """Phases of the coaching process."""

    INTRODUCTION = "INTRODUCTION"
    CONTEXT_GATHERING = "CONTEXT_GATHERING"
    EXPLORATION = "EXPLORATION"
    DEEPENING = "DEEPENING"
    REDIRECTING = "REDIRECTING"
    SUMMARIZING = "SUMMARIZING"
    ACTION_PLANNING = "ACTION_PLANNING"
    CLOSING = "CLOSING"


class QuestionType(str, Enum):
    """Type of question or intervention used by the Coach."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARAPHRASE = "PARAPHRASE"
    DEEPENING = "DEEPENING"
    NONE = "NONE"


class CoachResponseAnalysis(BaseModel):
    """
    Structured analysis of the Coach's response (Structured Output).

    Enforces a thinking process (Chain of Thought) before generating a response.
    """

    # STEP 1: THINKING (Chain of Thought)
    analysis_summary: str = Field(
        ...,
        description=(
            "Internal monologue. Analyze what the user said, "
            "how they feel, and whether they are asking for direct advice."
        ),
    )

    # STEP 2: STATE DIAGNOSIS
    coaching_phase: CoachingPhase = Field(
        ..., description="Current phase of the coaching process based on the conversation so far."
    )

    detected_emotions: list[str] = Field(
        default_factory=list,
        description="List of emotions detected in the user's message (LC-011).",
    )

    question_type: QuestionType = Field(
        ..., description="Category of intervention/question you intend to use (LC-004, LC-005)."
    )

    # STEP 3: ACTION (Response)
    ai_response: str = Field(
        ...,
        description=(
            "Final response to the user. MUST comply with Prime Directive (LC-003: no advice)."
        ),
    )
