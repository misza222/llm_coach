"""
SQL persistence backend using SQLAlchemy Core.

Works with both SQLite (dev) and PostgreSQL (prod) — the DATABASE_URL
in config determines which engine is created.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine

from life_coach_system.exceptions import PersistenceError
from life_coach_system.persistence.tables import metadata, sessions_table

__all__ = ["SqlBackend"]


class SqlBackend:
    """
    SQL-backed persistence that satisfies the PersistenceBackend protocol.

    Stores session state as JSON text in a single ``sessions`` table.
    SQLite for development, PostgreSQL for production — determined by the
    connection URL passed at construction time.
    """

    def __init__(self, *, database_url: str) -> None:
        # SQLite needs check_same_thread=False for FastAPI's thread pool
        connect_args: dict = {}
        if database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self._engine: Engine = create_engine(database_url, connect_args=connect_args)
        metadata.create_all(self._engine)

    def save(self, user_id: str, state: dict) -> None:
        """Save user state, overwriting any existing entry."""
        now = datetime.now(timezone.utc)
        state_json = json.dumps(state, ensure_ascii=False, default=str)

        with self._engine.begin() as connection:
            existing = connection.execute(
                select(sessions_table.c.user_id).where(sessions_table.c.user_id == user_id)
            ).first()

            if existing:
                connection.execute(
                    sessions_table.update()
                    .where(sessions_table.c.user_id == user_id)
                    .values(state=state_json, updated_at=now)
                )
            else:
                connection.execute(
                    sessions_table.insert().values(
                        user_id=user_id,
                        state=state_json,
                        created_at=now,
                        updated_at=now,
                    )
                )

    def load(self, user_id: str) -> dict | None:
        """Return state dict for user_id, or None if no state exists."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(sessions_table.c.state).where(sessions_table.c.user_id == user_id)
            ).first()

        if row is None:
            return None
        return json.loads(row[0])

    def exists(self, user_id: str) -> bool:
        """Return True if user has saved state."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(sessions_table.c.user_id).where(sessions_table.c.user_id == user_id)
            ).first()
        return row is not None

    def delete(self, user_id: str) -> None:
        """Delete user state. Raises PersistenceError if user doesn't exist."""
        with self._engine.begin() as connection:
            result = connection.execute(
                sessions_table.delete().where(sessions_table.c.user_id == user_id)
            )
            if result.rowcount == 0:
                raise PersistenceError(f"User {user_id} does not exist")

    def list_users(self) -> list[str]:
        """Return list of all user_id strings with saved state."""
        with self._engine.connect() as connection:
            rows = connection.execute(select(sessions_table.c.user_id)).fetchall()
        return [row[0] for row in rows]
