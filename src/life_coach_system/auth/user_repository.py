"""User and anonymous-count persistence using SQLAlchemy Core."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.engine import Engine

from life_coach_system.persistence.tables import (
    anonymous_message_counts_table,
    oauth_accounts_table,
    users_table,
)

__all__ = ["UserRepository"]


class UserRepository:
    """CRUD operations for users, OAuth accounts, and anonymous message counts."""

    def __init__(self, *, engine: Engine) -> None:
        self._engine = engine

    def find_by_oauth(self, *, provider: str, provider_id: str) -> dict | None:
        """Find a user by OAuth provider + provider_id. Returns user dict or None."""
        query = (
            select(users_table)
            .join(oauth_accounts_table, oauth_accounts_table.c.user_id == users_table.c.id)
            .where(
                oauth_accounts_table.c.provider == provider,
                oauth_accounts_table.c.provider_id == provider_id,
            )
        )
        with self._engine.connect() as conn:
            row = conn.execute(query).first()
        if row is None:
            return None
        return row._asdict()

    def create_user(
        self,
        *,
        email: str | None,
        name: str | None,
        avatar_url: str | None,
        provider: str,
        provider_id: str,
    ) -> dict:
        """Create a new user with an associated OAuth account. Returns user dict."""
        now = datetime.now(timezone.utc)
        user_id = str(uuid.uuid4())
        oauth_id = str(uuid.uuid4())

        with self._engine.begin() as conn:
            conn.execute(
                users_table.insert().values(
                    id=user_id,
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                    created_at=now,
                    updated_at=now,
                )
            )
            conn.execute(
                oauth_accounts_table.insert().values(
                    id=oauth_id,
                    user_id=user_id,
                    provider=provider,
                    provider_id=provider_id,
                    created_at=now,
                )
            )

        return {
            "id": user_id,
            "email": email,
            "name": name,
            "avatar_url": avatar_url,
            "created_at": now,
            "updated_at": now,
        }

    def get_by_id(self, user_id: str) -> dict | None:
        """Return user dict by ID, or None."""
        with self._engine.connect() as conn:
            row = conn.execute(select(users_table).where(users_table.c.id == user_id)).first()
        if row is None:
            return None
        return row._asdict()

    def increment_anonymous_count(self, anonymous_id: str) -> int:
        """Increment and return the message count for an anonymous user."""
        now = datetime.now(timezone.utc)
        table = anonymous_message_counts_table

        with self._engine.begin() as conn:
            row = conn.execute(
                select(table.c.message_count).where(table.c.anonymous_id == anonymous_id)
            ).first()

            if row is None:
                conn.execute(
                    table.insert().values(
                        anonymous_id=anonymous_id, message_count=1, updated_at=now
                    )
                )
                return 1

            new_count = row[0] + 1
            conn.execute(
                table.update()
                .where(table.c.anonymous_id == anonymous_id)
                .values(message_count=new_count, updated_at=now)
            )
            return new_count

    def get_anonymous_count(self, anonymous_id: str) -> int:
        """Return current message count for an anonymous user (0 if unknown)."""
        table = anonymous_message_counts_table
        with self._engine.connect() as conn:
            row = conn.execute(
                select(table.c.message_count).where(table.c.anonymous_id == anonymous_id)
            ).first()
        return row[0] if row else 0

    def delete_anonymous_count(self, anonymous_id: str) -> None:
        """Remove the anonymous message count (e.g. after migration to real user)."""
        table = anonymous_message_counts_table
        with self._engine.begin() as conn:
            conn.execute(table.delete().where(table.c.anonymous_id == anonymous_id))
