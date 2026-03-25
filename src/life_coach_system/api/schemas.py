"""
Request and response Pydantic models for the Life Coach API.
"""

__all__ = [
    "ChatRequest",
    "ChatMessage",
    "ChatResponse",
    "SessionResponse",
    "SessionSummary",
    "SessionListResponse",
    "UserInfo",
    "AuthStatusResponse",
]

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the client."""

    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    message: str = Field(..., min_length=1, description="User message text")
    session_id: str | None = Field(
        default=None, description="Target session; omit to use active or create new"
    )


class ChatMessage(BaseModel):
    """Single message in conversation history."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatResponse(BaseModel):
    """Coach reply with session metadata."""

    reply: str
    session_id: str
    status: str
    phase: str
    detected_emotions: list[str]
    main_goal: str | None = None
    user_name: str | None = None
    title: str | None = None
    history: list[ChatMessage]
    is_anonymous: bool = True
    remaining_messages: int | None = None
    is_closing: bool = False


class SessionSummary(BaseModel):
    """Lightweight session info for the sidebar list."""

    session_id: str
    title: str | None = None
    status: str = "ACTIVE"
    current_phase: str = "INTRODUCTION"
    created_at: str = ""
    updated_at: str = ""


class SessionListResponse(BaseModel):
    """List of session summaries for a user."""

    sessions: list[SessionSummary]


class SessionResponse(BaseModel):
    """Full session state returned to the client."""

    session_id: str
    user_id: str
    user_name: str | None
    current_phase: str | None
    main_goal: str | None
    status: str
    title: str | None
    detected_emotions: list[str]
    history: list[ChatMessage]
    created_at: str


class UserInfo(BaseModel):
    """Authenticated user info."""

    id: str
    email: str | None = None
    name: str | None = None
    provider: str | None = None


class AuthStatusResponse(BaseModel):
    """Response for /auth/me endpoint."""

    is_authenticated: bool
    user: UserInfo | None = None
