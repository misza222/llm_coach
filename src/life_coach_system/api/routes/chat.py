"""
Chat endpoint — send a message and get a coach reply.
"""

from fastapi import APIRouter, Depends

from life_coach_system._logging import get_logger
from life_coach_system.api.dependencies import get_coach, get_memory_manager, get_storage
from life_coach_system.api.schemas import ChatMessage, ChatRequest, ChatResponse
from life_coach_system.engine.coach import CoachAgent
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    *,
    coach: CoachAgent = Depends(get_coach),
    storage: InMemoryBackend = Depends(get_storage),
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> ChatResponse:
    """Send a user message and receive a coach response."""
    user_id = request.user_id

    # Load or create session state
    if storage.exists(user_id):
        state = SessionState(**storage.load(user_id))
    else:
        state = memory_manager.create_empty_state(user_id)

    # Generate coach response
    response_text, updated_state = coach.respond(request.message, state)

    # Persist updated state
    storage.save(user_id, updated_state.model_dump())

    log.info("chat_response", user_id=user_id, phase=updated_state.current_phase)

    return ChatResponse(
        reply=response_text,
        phase=updated_state.current_phase or "INTRODUCTION",
        detected_emotions=updated_state.detected_emotions,
        history=[
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in updated_state.conversation_history
        ],
    )
