"""
Cross-session memory models — UserProfile and CompletedSessionSummary.

UserProfile accumulates facts across sessions so the coach can greet
the user by name and reference past work without loading every session.

CompletedSessionSummary is a lightweight projection of a finished session,
injected into the system prompt for continuity.
"""

from datetime import datetime

from pydantic import BaseModel, Field

__all__ = ["UserProfile", "CompletedSessionSummary"]


class CompletedSessionSummary(BaseModel):
    """Compact projection of a completed session for cross-session context."""

    session_id: str
    title: str | None = None
    main_goal: str | None = None
    key_insights: list[str] = Field(default_factory=list)
    action_plan: str | None = None
    detected_emotions: list[str] = Field(default_factory=list)
    final_phase: str | None = None
    completed_at: str | None = None


class UserProfile(BaseModel):
    """Accumulated cross-session knowledge about a user.

    Materialized at session completion (not on every turn) so it stays
    cheap and consistent.
    """

    user_id: str
    user_name: str | None = None
    completed_session_count: int = 0
    last_session_goal: str | None = None
    last_session_action_plan: str | None = None
    all_time_emotions: list[str] = Field(default_factory=list)
    all_time_insights: list[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
