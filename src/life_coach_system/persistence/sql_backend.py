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
from life_coach_system.persistence.tables import metadata, sessions_table, user_profiles_table

__all__ = ["SqlBackend"]


class SqlBackend:
    """
    SQL-backed persistence that satisfies the PersistenceBackend protocol.

    Stores session state as JSON text in a ``sessions`` table, keyed by session_id.
    SQLite for development, PostgreSQL for production — determined by the
    connection URL passed at construction time.
    """

    def __init__(self, *, database_url: str) -> None:
        connect_args: dict = {}
        if database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self._engine: Engine = create_engine(database_url, connect_args=connect_args)
        metadata.create_all(self._engine)

    def save(self, session_id: str, state: dict) -> None:
        """Save session state, overwriting any existing entry."""
        now = datetime.now(timezone.utc)
        state_json = json.dumps(state, ensure_ascii=False, default=str)

        # Extract denormalized columns from state for query-ability
        user_id = state.get("user_id", "")
        status = state.get("status", "ACTIVE")
        title = state.get("title")
        completed_at_str = state.get("completed_at")
        completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None

        with self._engine.begin() as connection:
            existing = connection.execute(
                select(sessions_table.c.session_id).where(sessions_table.c.session_id == session_id)
            ).first()

            if existing:
                connection.execute(
                    sessions_table.update()
                    .where(sessions_table.c.session_id == session_id)
                    .values(
                        state=state_json,
                        user_id=user_id,
                        status=status,
                        title=title,
                        completed_at=completed_at,
                        updated_at=now,
                    )
                )
            else:
                connection.execute(
                    sessions_table.insert().values(
                        session_id=session_id,
                        user_id=user_id,
                        status=status,
                        title=title,
                        completed_at=completed_at,
                        state=state_json,
                        created_at=now,
                        updated_at=now,
                    )
                )

    def load(self, session_id: str) -> dict | None:
        """Return state dict for session_id, or None if not found."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(sessions_table.c.state).where(sessions_table.c.session_id == session_id)
            ).first()

        if row is None:
            return None
        return json.loads(row[0])

    def exists(self, session_id: str) -> bool:
        """Return True if session exists."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(sessions_table.c.session_id).where(sessions_table.c.session_id == session_id)
            ).first()
        return row is not None

    def delete(self, session_id: str) -> None:
        """Delete session state. Raises PersistenceError if not found."""
        with self._engine.begin() as connection:
            result = connection.execute(
                sessions_table.delete().where(sessions_table.c.session_id == session_id)
            )
            if result.rowcount == 0:
                raise PersistenceError(f"Session {session_id} does not exist")

    def list_sessions(self, user_id: str) -> list[dict]:
        """Return summary dicts for all sessions owned by user_id, newest first."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(
                    sessions_table.c.session_id,
                    sessions_table.c.title,
                    sessions_table.c.status,
                    sessions_table.c.state,
                    sessions_table.c.created_at,
                    sessions_table.c.updated_at,
                )
                .where(sessions_table.c.user_id == user_id)
                .order_by(sessions_table.c.updated_at.desc())
            ).fetchall()

        results = []
        for row in rows:
            # Extract current_phase from the JSON state
            state = json.loads(row[3])
            results.append(
                {
                    "session_id": row[0],
                    "title": row[1],
                    "status": row[2],
                    "current_phase": state.get("current_phase", "INTRODUCTION"),
                    "created_at": row[4].isoformat() if row[4] else "",
                    "updated_at": row[5].isoformat() if row[5] else "",
                }
            )
        return results

    def find_active_session(self, user_id: str) -> dict | None:
        """Return the full state dict of the user's active session, or None."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(sessions_table.c.state)
                .where(sessions_table.c.user_id == user_id)
                .where(sessions_table.c.status == "ACTIVE")
                .order_by(sessions_table.c.updated_at.desc())
                .limit(1)
            ).first()

        if row is None:
            return None
        return json.loads(row[0])

    def save_user_profile(self, user_id: str, profile_dict: dict) -> None:
        """Save or overwrite the cross-session user profile."""
        now = datetime.now(timezone.utc)
        profile_json = json.dumps(profile_dict, ensure_ascii=False, default=str)

        with self._engine.begin() as connection:
            existing = connection.execute(
                select(user_profiles_table.c.user_id).where(
                    user_profiles_table.c.user_id == user_id
                )
            ).first()

            if existing:
                connection.execute(
                    user_profiles_table.update()
                    .where(user_profiles_table.c.user_id == user_id)
                    .values(profile=profile_json, updated_at=now)
                )
            else:
                connection.execute(
                    user_profiles_table.insert().values(
                        user_id=user_id, profile=profile_json, updated_at=now
                    )
                )

    def load_user_profile(self, user_id: str) -> dict | None:
        """Return the user profile dict, or None if not found."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(user_profiles_table.c.profile).where(
                    user_profiles_table.c.user_id == user_id
                )
            ).first()

        if row is None:
            return None
        return json.loads(row[0])
