"""
Request and response Pydantic models for the Life Coach API.
"""

__all__ = [
    "ChatRequest",
    "ChatMessage",
    "ChatResponse",
    "SessionResponse",
]

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the client."""

    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    message: str = Field(..., min_length=1, description="User message text")


class ChatMessage(BaseModel):
    """Single message in conversation history."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatResponse(BaseModel):
    """Coach reply with session metadata."""

    reply: str
    phase: str
    detected_emotions: list[str]
    history: list[ChatMessage]


class SessionResponse(BaseModel):
    """Full session state returned to the client."""

    user_id: str
    user_name: str | None
    current_phase: str | None
    main_goal: str | None
    detected_emotions: list[str]
    history: list[ChatMessage]
    created_at: str
