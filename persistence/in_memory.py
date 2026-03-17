"""
InMemory Persistence Backend

Simple in-memory storage for development and testing.
State is lost on app restart - use only for dev/testing.

NOTE: This file is reusable — no modifications needed.
"""

from typing import Optional
from .backend import PersistenceBackend, PersistenceError
import copy


class InMemoryBackend(PersistenceBackend):
    """
    Store user state in memory (dict).

    Advantages:
    - Fast (no I/O)
    - Simple (no setup needed)
    - Good for development and testing

    Disadvantages:
    - State lost on restart
    - Not suitable for production
    - No multi-process support
    """

    def __init__(self):
        """Initialize empty storage."""
        self._storage: dict[str, dict] = {}

    def save(self, user_id: str, state: dict) -> None:
        """Save user state to memory."""
        # Deep copy to avoid reference issues
        self._storage[user_id] = copy.deepcopy(state)

    def load(self, user_id: str) -> Optional[dict]:
        """Load user state from memory."""
        state = self._storage.get(user_id)

        if state is None:
            return None

        # Return deep copy to avoid mutations affecting stored state
        return copy.deepcopy(state)

    def exists(self, user_id: str) -> bool:
        """Check if user has saved state."""
        return user_id in self._storage

    def delete(self, user_id: str) -> None:
        """Delete user state."""
        if not self.exists(user_id):
            raise PersistenceError(f"User {user_id} does not exist")

        del self._storage[user_id]

    def list_users(self) -> list[str]:
        """List all user IDs."""
        return list(self._storage.keys())

    def clear_all(self) -> None:
        """Clear all stored data (useful for testing)."""
        self._storage.clear()

    def get_storage_size(self) -> int:
        """Get number of users in storage."""
        return len(self._storage)
