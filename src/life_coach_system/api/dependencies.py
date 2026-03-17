"""
FastAPI dependency providers (singletons via lru_cache).
"""

__all__ = ["get_coach", "get_storage", "get_memory_manager"]

from functools import lru_cache

from life_coach_system.engine.coach import CoachAgent
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.persistence.in_memory import InMemoryBackend


@lru_cache(maxsize=1)
def get_coach() -> CoachAgent:
    """Return the singleton CoachAgent instance."""
    return CoachAgent()


@lru_cache(maxsize=1)
def get_storage() -> InMemoryBackend:
    """Return the singleton InMemoryBackend instance."""
    return InMemoryBackend()


@lru_cache(maxsize=1)
def get_memory_manager() -> MemoryManager:
    """Return the singleton MemoryManager instance."""
    return MemoryManager()
