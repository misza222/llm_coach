"""
InMemory Persistence Backend

Simple in-memory storage for development and testing.
State is lost on app restart - use only for dev/testing.
"""

import copy

from life_coach_system.exceptions import PersistenceError


class InMemoryBackend:
    """
    Store user state in memory (dict).

    Satisfies the PersistenceBackend protocol via structural subtyping —
    no explicit inheritance required.

    Advantages:
    - Fast (no I/O)
    - Simple (no setup needed)
    - Good for development and testing

    Disadvantages:
    - State lost on restart
    - Not suitable for production
    - No multi-process support
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._storage: dict[str, dict] = {}

    def save(self, user_id: str, state: dict) -> None:
        """Save user state to memory."""
        # Deep copy to avoid reference issues when the caller mutates state later
        self._storage[user_id] = copy.deepcopy(state)

    def load(self, user_id: str) -> dict | None:
        """Load user state from memory."""
        state = self._storage.get(user_id)

        if state is None:
            return None

        # Return deep copy to prevent mutations from affecting stored state
        return copy.deepcopy(state)

    def exists(self, user_id: str) -> bool:
        """Check if user has saved state."""
        return user_id in self._storage

    def delete(self, user_id: str) -> None:
        """Delete user state. Raises PersistenceError if user doesn't exist."""
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
