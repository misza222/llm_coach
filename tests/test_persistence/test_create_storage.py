"""Tests for the create_storage factory function."""

from life_coach_system.persistence import create_storage
from life_coach_system.persistence.in_memory import InMemoryBackend
from life_coach_system.persistence.sql_backend import SqlBackend


def test_create_storage_returns_in_memory_when_no_url() -> None:
    """create_storage() returns InMemoryBackend when database_url is None."""
    backend = create_storage(database_url=None)
    assert isinstance(backend, InMemoryBackend)


def test_create_storage_returns_sql_backend_for_sqlite(tmp_path) -> None:
    """create_storage() returns SqlBackend when given a SQLite URL."""
    db_path = tmp_path / "test.db"
    backend = create_storage(database_url=f"sqlite:///{db_path}")
    assert isinstance(backend, SqlBackend)
