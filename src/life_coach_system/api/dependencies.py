"""
FastAPI dependency providers (singletons via lru_cache).
"""

__all__ = ["get_coach", "get_storage", "get_memory_manager"]

from functools import lru_cache

from life_coach_system._logging import get_logger
from life_coach_system.config import settings
from life_coach_system.engine.coach import CoachAgent
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.persistence.backend import PersistenceBackend
from life_coach_system.persistence.in_memory import InMemoryBackend

log = get_logger(__name__)


@lru_cache(maxsize=1)
def get_coach() -> CoachAgent:
    """Return the singleton CoachAgent instance."""
    return CoachAgent()


@lru_cache(maxsize=1)
def get_storage() -> PersistenceBackend:
    """Return the singleton storage backend based on config."""
    if settings.database_url is not None:
        # Import here to avoid pulling sqlalchemy when not needed
        from life_coach_system.persistence.sql_backend import SqlBackend

        log.info("persistence_backend", backend="sql", url=settings.database_url.split("@")[-1])
        return SqlBackend(database_url=settings.database_url)

    log.info("persistence_backend", backend="in_memory")
    return InMemoryBackend()


@lru_cache(maxsize=1)
def get_memory_manager() -> MemoryManager:
    """Return the singleton MemoryManager instance."""
    return MemoryManager()
