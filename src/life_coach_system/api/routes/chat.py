"""
Chat endpoint — send a message and get a coach reply.
"""

from fastapi import APIRouter, Depends

from life_coach_system._logging import get_logger
from life_coach_system.api.dependencies import (
    get_coach,
    get_current_user,
    get_memory_manager,
    get_storage,
    get_user_repository,
)
from life_coach_system.api.schemas import ChatMessage, ChatRequest, ChatResponse
from life_coach_system.auth.user_repository import UserRepository
from life_coach_system.config import settings
from life_coach_system.engine.coach import CoachAgent
from life_coach_system.exceptions import AnonymousLimitError, SessionCompletedError
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.backend import PersistenceBackend

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    *,
    coach: CoachAgent = Depends(get_coach),
    storage: PersistenceBackend = Depends(get_storage),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: dict | None = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> ChatResponse:
    """Send a user message and receive a coach response."""
    is_anonymous = current_user is None

    # Use authenticated user_id if available, otherwise the client-provided one
    if current_user is not None:
        user_id = current_user["sub"]
    else:
        user_id = request.user_id

    # Anonymous message gating
    remaining_messages: int | None = None
    if is_anonymous:
        current_count = user_repo.get_anonymous_count(user_id)
        if current_count >= settings.max_anonymous_messages:
            raise AnonymousLimitError(
                f"Anonymous message limit ({settings.max_anonymous_messages}) reached. "
                "Please sign in to continue."
            )
        remaining_messages = settings.max_anonymous_messages - current_count - 1

    # Resolve session: explicit session_id > active session > new session
    state: SessionState | None = None
    if request.session_id:
        stored = storage.load(request.session_id)
        if stored is not None:
            state = SessionState(**stored)
            if state.status == "COMPLETED":
                raise SessionCompletedError("Cannot send messages to a completed session.")
    else:
        active = storage.find_active_session(user_id)
        if active is not None:
            state = SessionState(**active)

    if state is None:
        state = memory_manager.create_empty_state(user_id)

    # Generate coach response
    response_text, updated_state, is_closing = coach.respond(request.message, state)

    # Persist updated state (keyed by session_id)
    storage.save(updated_state.session_id, updated_state.model_dump())

    # Increment anonymous count after successful response
    if is_anonymous:
        user_repo.increment_anonymous_count(user_id)

    log.info(
        "chat_response",
        user_id=user_id,
        session_id=updated_state.session_id,
        phase=updated_state.current_phase,
    )

    return ChatResponse(
        reply=response_text,
        session_id=updated_state.session_id,
        status=updated_state.status,
        phase=updated_state.current_phase or "INTRODUCTION",
        detected_emotions=updated_state.detected_emotions,
        main_goal=updated_state.main_goal,
        user_name=updated_state.user_name,
        title=updated_state.title,
        history=[
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in updated_state.conversation_history
        ],
        is_anonymous=is_anonymous,
        remaining_messages=remaining_messages,
        is_closing=is_closing,
    )
