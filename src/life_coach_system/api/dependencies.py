"""
FastAPI dependency providers (singletons via lru_cache).
"""

__all__ = [
    "get_coach",
    "get_storage",
    "get_memory_manager",
    "get_current_user",
    "get_user_repository",
    "get_oauth",
]

from functools import lru_cache

from fastapi import Cookie

from life_coach_system._logging import get_logger
from life_coach_system.auth.jwt import decode_access_token
from life_coach_system.auth.oauth import OAuth, create_oauth
from life_coach_system.auth.user_repository import UserRepository
from life_coach_system.config import settings
from life_coach_system.engine.coach import CoachAgent
from life_coach_system.exceptions import AuthenticationError
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
        from life_coach_system.persistence.sql_backend import SqlBackend

        log.info("persistence_backend", backend="sql", url=settings.database_url.split("@")[-1])
        return SqlBackend(database_url=settings.database_url)

    log.info("persistence_backend", backend="in_memory")
    return InMemoryBackend()


@lru_cache(maxsize=1)
def get_memory_manager() -> MemoryManager:
    """Return the singleton MemoryManager instance."""
    return MemoryManager()


@lru_cache(maxsize=1)
def get_oauth() -> OAuth:
    """Return the singleton Authlib OAuth instance."""
    return create_oauth(settings)


@lru_cache(maxsize=1)
def get_user_repository() -> UserRepository:
    """Return the singleton UserRepository (requires SQL backend)."""
    if settings.database_url is None:
        # For in-memory mode, create a SQLite in-memory engine for auth tables.
        # StaticPool ensures all connections share the same underlying database.
        from sqlalchemy import create_engine
        from sqlalchemy.pool import StaticPool

        from life_coach_system.persistence.tables import metadata

        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        metadata.create_all(engine)
        return UserRepository(engine=engine)

    from life_coach_system.persistence.sql_backend import SqlBackend

    storage = get_storage()
    if isinstance(storage, SqlBackend):
        return UserRepository(engine=storage._engine)

    # Fallback: create engine from database_url
    from sqlalchemy import create_engine

    from life_coach_system.persistence.tables import metadata

    engine = create_engine(settings.database_url)
    metadata.create_all(engine)
    return UserRepository(engine=engine)


def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> dict | None:
    """Extract and decode the JWT from the cookie. Returns None for anonymous users."""
    if access_token is None:
        return None
    try:
        return decode_access_token(access_token)
    except AuthenticationError:
        return None
