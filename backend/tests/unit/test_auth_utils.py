from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.auth import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.config import settings


def test_hash_password_and_verify_roundtrip():
    raw_password = "StrongP@ssword123!"
    hashed_password = hash_password(raw_password)

    assert hashed_password != raw_password
    assert verify_password(raw_password, hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_create_access_token_contains_expected_claims():
    token = create_access_token(user_id=42, email="user@example.com")
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "42"
    assert payload["user_id"] == 42
    assert payload["email"] == "user@example.com"
    assert payload["exp"] > datetime.now(tz=timezone.utc).timestamp()


@pytest.mark.asyncio
async def test_verify_token_returns_user_info_for_valid_token():
    token = create_access_token(user_id=7, email="valid@example.com")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user_info = await verify_token(credentials)

    assert user_info == {"user_id": 7, "email": "valid@example.com"}


@pytest.mark.asyncio
async def test_verify_token_rejects_missing_claims():
    bad_token = jwt.encode(
        {"sub": "1"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bad_token)

    with pytest.raises(HTTPException) as exc:
        await verify_token(credentials)

    assert exc.value.status_code == 401
    assert "Invalid token" in exc.value.detail


@pytest.mark.asyncio
async def test_verify_token_rejects_tampered_token():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="this.is.not.a.valid.jwt",
    )

    with pytest.raises(HTTPException) as exc:
        await verify_token(credentials)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"
