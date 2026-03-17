"""Tests for JWT token creation and decoding."""

import pytest

from life_coach_system.auth.jwt import create_access_token, decode_access_token
from life_coach_system.exceptions import AuthenticationError


def test_roundtrip_token_contains_claims() -> None:
    token = create_access_token(
        user_id="user-123", email="a@b.com", name="Alice", provider="google"
    )
    claims = decode_access_token(token)
    assert claims["sub"] == "user-123"
    assert claims["email"] == "a@b.com"
    assert claims["name"] == "Alice"
    assert claims["provider"] == "google"


def test_token_contains_iat_and_exp() -> None:
    token = create_access_token(user_id="u1")
    claims = decode_access_token(token)
    assert "iat" in claims
    assert "exp" in claims
    assert claims["exp"] > claims["iat"]


def test_decode_invalid_token_raises_auth_error() -> None:
    with pytest.raises(AuthenticationError, match="Invalid token"):
        decode_access_token("not.a.valid.token")


def test_decode_tampered_token_raises_auth_error() -> None:
    token = create_access_token(user_id="u1")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(AuthenticationError):
        decode_access_token(tampered)


def test_optional_claims_default_to_none() -> None:
    token = create_access_token(user_id="u1")
    claims = decode_access_token(token)
    assert claims["email"] is None
    assert claims["name"] is None
    assert claims["provider"] is None
