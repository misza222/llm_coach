"""
Session management endpoints — load, reset, export.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from life_coach_system._logging import get_logger
from life_coach_system.api.dependencies import get_storage
from life_coach_system.api.schemas import ChatMessage, SessionResponse
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.backend import PersistenceBackend

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/{user_id}", response_model=SessionResponse)
def get_session(
    user_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> SessionResponse:
    """Load session history and metadata for a user."""
    state_dict = storage.load(user_id)
    if state_dict is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = SessionState(**state_dict)
    return SessionResponse(
        user_id=state.user_id,
        user_name=state.user_name,
        current_phase=state.current_phase,
        main_goal=state.main_goal,
        detected_emotions=state.detected_emotions,
        history=[
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in state.conversation_history
        ],
        created_at=state.created_at,
    )


@router.post("/{user_id}/reset")
def reset_session(
    user_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> dict[str, str]:
    """Clear all state for a user."""
    if storage.exists(user_id):
        storage.delete(user_id)
    return {"status": "reset"}


@router.get("/{user_id}/export")
def export_session(
    user_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> Response:
    """Download conversation as a JSON file."""
    state_dict = storage.load(user_id)
    if state_dict is None:
        raise HTTPException(status_code=404, detail="Session not found")

    content = json.dumps(state_dict, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="session_{user_id}.json"',
        },
    )
