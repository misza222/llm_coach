"""Persistence package — pluggable storage backends for session state."""

from life_coach_system.persistence.backend import PersistenceBackend  # noqa: F401

__all__ = [
    "PersistenceBackend",
    "PersistenceError",
    "InMemoryBackend",
    "SqlBackend",
    "create_storage",
]


def create_storage(*, database_url: str | None = None) -> PersistenceBackend:
    """Create a storage backend based on the database URL.

    Args:
        database_url: DB connection string. None means in-memory (no persistence).
            ``sqlite:///path.db`` for SQLite, ``postgresql://...`` for PostgreSQL.
    """
    if database_url is not None:
        from life_coach_system.persistence.sql_backend import SqlBackend

        return SqlBackend(database_url=database_url)

    from life_coach_system.persistence.in_memory import InMemoryBackend

    return InMemoryBackend()
