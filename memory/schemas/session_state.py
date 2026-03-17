# -*- coding: utf-8 -*-
"""
Session State Schema - current coaching session state.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SessionState(BaseModel):
    """
    Current coaching session state.
    Contains all fields required to satisfy criteria LC-001 through LC-014.
    """

    # Basic information
    user_id: str = Field(..., description="Unique user identifier")
    user_name: Optional[str] = Field(default=None, description="User name (LC-002)")
    conversation_history: List[dict] = Field(default_factory=list, description="History of messages")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Coaching process state
    current_phase: Optional[str] = Field(default="INTRODUCTION", description="Current phase (LC-002)")
    main_goal: Optional[str] = Field(default=None, description="User's main goal (LC-002)")

    # Qualitative analysis
    detected_emotions: List[str] = Field(default_factory=list, description="Detected emotions (LC-011)")
    key_insights: List[str] = Field(default_factory=list, description="User insights (LC-009)")
    action_plan: Optional[str] = Field(default=None, description="Action steps (LC-010)")

    # Technical metrics (useful for evaluation)
    paraphrases_count: int = Field(default=0, description="Counter for LC-005")
    open_questions_count: int = Field(default=0, description="Counter for LC-004")

    class Config:
        arbitrary_types_allowed = True
