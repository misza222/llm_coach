
"""
Persistence Backend Interface

Abstract interface for pluggable storage backends.
Implementations: InMemoryBackend (dev), RedisBackend (prod), PostgresBackend (future)

NOTE: This file is reusable — no modifications needed.
"""

from abc import ABC, abstractmethod
from typing import Optional


class PersistenceBackend(ABC):
    """
    Abstract interface for user state persistence.

    All backends must implement these methods to be compatible with CoachAgent.
    """

    @abstractmethod
    def save(self, user_id: str, state: dict) -> None:
        """
        Save user state.

        Args:
            user_id: Unique user identifier
            state: Complete state dict (session_state from memory/schemas)

        Raises:
            PersistenceError: If save operation fails
        """
        pass

    @abstractmethod
    def load(self, user_id: str) -> Optional[dict]:
        """
        Load user state.

        Args:
            user_id: Unique user identifier

        Returns:
            State dict if user exists, None if new user

        Raises:
            PersistenceError: If load operation fails
        """
        pass

    @abstractmethod
    def exists(self, user_id: str) -> bool:
        """
        Check if user state exists.

        Args:
            user_id: Unique user identifier

        Returns:
            True if user has saved state, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        """
        Delete user state.

        Args:
            user_id: Unique user identifier

        Raises:
            PersistenceError: If user doesn't exist
        """
        pass

    @abstractmethod
    def list_users(self) -> list[str]:
        """
        List all user IDs with saved state.

        Returns:
            List of user_id strings
        """
        pass


class PersistenceError(Exception):
    """Raised when persistence operations fail."""
    pass
