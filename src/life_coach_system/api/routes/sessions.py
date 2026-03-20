"""
Session management endpoints — list, get, create, end, delete, export.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from life_coach_system._logging import get_logger
from life_coach_system.api.dependencies import get_memory_manager, get_storage
from life_coach_system.api.schemas import (
    ChatMessage,
    SessionListResponse,
    SessionResponse,
    SessionSummary,
)
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.backend import PersistenceBackend

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/{user_id}", response_model=SessionListResponse)
def list_sessions(
    user_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> SessionListResponse:
    """List all sessions for a user."""
    summaries = storage.list_sessions(user_id)
    return SessionListResponse(
        sessions=[SessionSummary(**s) for s in summaries],
    )


@router.get("/{user_id}/{session_id}", response_model=SessionResponse)
def get_session(
    user_id: str,
    session_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> SessionResponse:
    """Load a specific session's full state."""
    state_dict = storage.load(session_id)
    if state_dict is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = SessionState(**state_dict)
    if state.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=state.session_id,
        user_id=state.user_id,
        user_name=state.user_name,
        current_phase=state.current_phase,
        main_goal=state.main_goal,
        status=state.status,
        title=state.title,
        detected_emotions=state.detected_emotions,
        history=[
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in state.conversation_history
        ],
        created_at=state.created_at,
    )


@router.post("/{user_id}/new", response_model=SessionResponse)
def create_new_session(
    user_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> SessionResponse:
    """Create a new session, completing the current active one if it exists."""
    # Complete any active session
    active = storage.find_active_session(user_id)
    if active is not None:
        active_state = SessionState(**active)
        completed = memory_manager.complete_session(active_state)
        storage.save(completed.session_id, completed.model_dump())
        log.info("session_auto_completed", session_id=completed.session_id)

    # Create new session
    state = memory_manager.create_empty_state(user_id)
    storage.save(state.session_id, state.model_dump())
    log.info("session_created", user_id=user_id, session_id=state.session_id)

    return SessionResponse(
        session_id=state.session_id,
        user_id=state.user_id,
        user_name=state.user_name,
        current_phase=state.current_phase,
        main_goal=state.main_goal,
        status=state.status,
        title=state.title,
        detected_emotions=state.detected_emotions,
        history=[],
        created_at=state.created_at,
    )


@router.post("/{user_id}/{session_id}/end")
def end_session(
    user_id: str,
    session_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> dict[str, str]:
    """Explicitly complete a session."""
    state_dict = storage.load(session_id)
    if state_dict is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = SessionState(**state_dict)
    if state.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    if state.status == "COMPLETED":
        return {"status": "already_completed"}

    completed = memory_manager.complete_session(state)
    storage.save(completed.session_id, completed.model_dump())
    log.info("session_ended", session_id=session_id)
    return {"status": "completed"}


@router.delete("/{user_id}/{session_id}")
def delete_session(
    user_id: str,
    session_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> dict[str, str]:
    """Delete a specific session."""
    state_dict = storage.load(session_id)
    if state_dict is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = SessionState(**state_dict)
    if state.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    storage.delete(session_id)
    log.info("session_deleted", session_id=session_id)
    return {"status": "deleted"}


@router.get("/{user_id}/{session_id}/export")
def export_session(
    user_id: str,
    session_id: str,
    *,
    storage: PersistenceBackend = Depends(get_storage),
) -> Response:
    """Download a specific session as a JSON file."""
    state_dict = storage.load(session_id)
    if state_dict is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = SessionState(**state_dict)
    if state.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    content = json.dumps(state_dict, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="session_{session_id}.json"',
        },
    )
