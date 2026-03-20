"""
InMemory Persistence Backend

Simple in-memory storage for development and testing.
State is lost on app restart - use only for dev/testing.
"""

import copy

from life_coach_system.exceptions import PersistenceError


class InMemoryBackend:
    """
    Store session state in memory (dict), keyed by session_id.

    Satisfies the PersistenceBackend protocol via structural subtyping —
    no explicit inheritance required.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._storage: dict[str, dict] = {}

    def save(self, session_id: str, state: dict) -> None:
        """Save session state to memory."""
        self._storage[session_id] = copy.deepcopy(state)

    def load(self, session_id: str) -> dict | None:
        """Load session state from memory."""
        state = self._storage.get(session_id)
        if state is None:
            return None
        return copy.deepcopy(state)

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self._storage

    def delete(self, session_id: str) -> None:
        """Delete session state. Raises PersistenceError if not found."""
        if not self.exists(session_id):
            raise PersistenceError(f"Session {session_id} does not exist")
        del self._storage[session_id]

    def list_sessions(self, user_id: str) -> list[dict]:
        """Return summary dicts for all sessions owned by user_id, newest first."""
        results = []
        for state in self._storage.values():
            if state.get("user_id") == user_id:
                results.append(
                    {
                        "session_id": state.get("session_id", ""),
                        "title": state.get("title"),
                        "status": state.get("status", "ACTIVE"),
                        "current_phase": state.get("current_phase", "INTRODUCTION"),
                        "created_at": state.get("created_at", ""),
                        "updated_at": state.get("updated_at", state.get("created_at", "")),
                    }
                )
        # Sort by updated_at descending
        results.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        return results

    def find_active_session(self, user_id: str) -> dict | None:
        """Return the full state dict of the user's active session, or None."""
        for state in self._storage.values():
            if state.get("user_id") == user_id and state.get("status", "ACTIVE") == "ACTIVE":
                return copy.deepcopy(state)
        return None

    def clear_all(self) -> None:
        """Clear all stored data (useful for testing)."""
        self._storage.clear()

    def get_storage_size(self) -> int:
        """Get number of sessions in storage."""
        return len(self._storage)
