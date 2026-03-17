"""Tests for UserRepository CRUD and anonymous counting."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from life_coach_system.auth.user_repository import UserRepository
from life_coach_system.persistence.tables import metadata


@pytest.fixture()
def user_repo() -> UserRepository:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    metadata.create_all(engine)
    return UserRepository(engine=engine)


def test_create_and_find_user_by_oauth(user_repo: UserRepository) -> None:
    user = user_repo.create_user(
        email="alice@example.com",
        name="Alice",
        avatar_url="https://example.com/avatar.jpg",
        provider="google",
        provider_id="g-12345",
    )
    assert user["email"] == "alice@example.com"
    assert user["name"] == "Alice"
    assert user["id"]  # non-empty UUID

    found = user_repo.find_by_oauth(provider="google", provider_id="g-12345")
    assert found is not None
    assert found["id"] == user["id"]


def test_find_by_oauth_returns_none_for_unknown(user_repo: UserRepository) -> None:
    assert user_repo.find_by_oauth(provider="google", provider_id="nope") is None


def test_get_by_id(user_repo: UserRepository) -> None:
    user = user_repo.create_user(
        email="bob@example.com", name="Bob", avatar_url=None, provider="twitter", provider_id="t-1"
    )
    found = user_repo.get_by_id(user["id"])
    assert found is not None
    assert found["name"] == "Bob"


def test_get_by_id_returns_none_for_unknown(user_repo: UserRepository) -> None:
    assert user_repo.get_by_id("nonexistent-id") is None


def test_anonymous_count_starts_at_zero(user_repo: UserRepository) -> None:
    assert user_repo.get_anonymous_count("anon-1") == 0


def test_increment_anonymous_count(user_repo: UserRepository) -> None:
    assert user_repo.increment_anonymous_count("anon-1") == 1
    assert user_repo.increment_anonymous_count("anon-1") == 2
    assert user_repo.increment_anonymous_count("anon-1") == 3
    assert user_repo.get_anonymous_count("anon-1") == 3


def test_delete_anonymous_count(user_repo: UserRepository) -> None:
    user_repo.increment_anonymous_count("anon-1")
    user_repo.increment_anonymous_count("anon-1")
    user_repo.delete_anonymous_count("anon-1")
    assert user_repo.get_anonymous_count("anon-1") == 0


def test_delete_nonexistent_anonymous_count_is_noop(user_repo: UserRepository) -> None:
    # Should not raise
    user_repo.delete_anonymous_count("never-seen")
