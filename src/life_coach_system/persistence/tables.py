"""
Shared SQLAlchemy table definitions for all SQL-backed storage.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

__all__ = [
    "metadata",
    "sessions_table",
    "users_table",
    "oauth_accounts_table",
    "anonymous_message_counts_table",
]

metadata = MetaData()

sessions_table = Table(
    "sessions",
    metadata,
    Column("user_id", String(255), primary_key=True),
    Column("state", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

users_table = Table(
    "users",
    metadata,
    Column("id", String(255), primary_key=True),
    Column("email", String(255), nullable=True),
    Column("name", String(255), nullable=True),
    Column("avatar_url", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

oauth_accounts_table = Table(
    "oauth_accounts",
    metadata,
    Column("id", String(255), primary_key=True),
    Column("user_id", String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("provider", String(50), nullable=False),
    Column("provider_id", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),
)

anonymous_message_counts_table = Table(
    "anonymous_message_counts",
    metadata,
    Column("anonymous_id", String(255), primary_key=True),
    Column("message_count", Integer, nullable=False, default=0),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
