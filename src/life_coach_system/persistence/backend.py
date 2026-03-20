"""
Persistence Backend Interface

Structural protocol for pluggable storage backends.
Implementations: InMemoryBackend (dev), SqlBackend (prod)
"""

from typing import Protocol, runtime_checkable

# Re-export PersistenceError from the central exceptions module so that existing
# code importing it from this module keeps working without changes.
from life_coach_system.exceptions import PersistenceError  # noqa: F401

__all__ = ["PersistenceBackend", "PersistenceError"]


@runtime_checkable
class PersistenceBackend(Protocol):
    """
    Structural interface for session state persistence.

    Sessions are keyed by session_id (not user_id). A user may own
    multiple sessions; use list_sessions / find_active_session to
    query by user.
    """

    def save(self, session_id: str, state: dict) -> None:
        """Save session state, overwriting any existing entry."""
        ...

    def load(self, session_id: str) -> dict | None:
        """Return state dict for session_id, or None if not found."""
        ...

    def exists(self, session_id: str) -> bool:
        """Return True if session exists, False otherwise."""
        ...

    def delete(self, session_id: str) -> None:
        """Delete session state. Raises PersistenceError if not found."""
        ...

    def list_sessions(self, user_id: str) -> list[dict]:
        """Return summary dicts for all sessions owned by user_id, ordered by updated_at DESC."""
        ...

    def find_active_session(self, user_id: str) -> dict | None:
        """Return the full state dict of the user's active session, or None."""
        ...
