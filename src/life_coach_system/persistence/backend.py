"""
Persistence Backend Interface

Structural protocol for pluggable storage backends.
Implementations: InMemoryBackend (dev), RedisBackend (prod), PostgresBackend (future)
"""

from typing import Protocol, runtime_checkable

# Re-export PersistenceError from the central exceptions module so that existing
# code importing it from this module keeps working without changes.
from life_coach_system.exceptions import PersistenceError  # noqa: F401

__all__ = ["PersistenceBackend", "PersistenceError"]


@runtime_checkable
class PersistenceBackend(Protocol):
    """
    Structural interface for user state persistence.

    Any class that implements save/load/exists/delete/list_users
    with matching signatures satisfies this protocol — no inheritance needed.
    """

    def save(self, user_id: str, state: dict) -> None:
        """Save user state, overwriting any existing entry."""
        ...

    def load(self, user_id: str) -> dict | None:
        """Return state dict for user_id, or None if no state exists."""
        ...

    def exists(self, user_id: str) -> bool:
        """Return True if user has saved state, False otherwise."""
        ...

    def delete(self, user_id: str) -> None:
        """Delete user state. Raises PersistenceError if user doesn't exist."""
        ...

    def list_users(self) -> list[str]:
        """Return list of all user_id strings with saved state."""
        ...
