"""
app/auth.py — JWT authentication helpers.

Provides:
  - `hash_password()`      → bcrypt password hashing
  - `verify_password()`    → bcrypt comparison
  - `create_access_token()` → JWT creation
  - `verify_token()`       → JWT validation (FastAPI dependency)
  - `get_current_user()`   → Convenience dependency wrapping verify_token
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger("agentic_crm")

# ── Password hashing ──────────────────────────────────────────────────────────
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The user-supplied plain-text password.

    Returns:
        A bcrypt hash string safe to store in the database.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain-text password against a stored bcrypt hash.

    Args:
        plain_password:  The password supplied at login.
        hashed_password: The stored bcrypt hash from the database.

    Returns:
        True if they match, False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT token creation ────────────────────────────────────────────────────────
def create_access_token(user_id: int, email: str) -> str:
    """
    Create a signed JWT access token.

    The token embeds `user_id` and `email` as custom claims.
    Expiry is controlled by `settings.jwt_expire_minutes`.

    Args:
        user_id: The authenticated user's primary key.
        email:   The authenticated user's email address.

    Returns:
        A signed JWT string to be returned to the client.
    """
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload: dict = {
        "sub": str(user_id),       # standard JWT subject claim
        "user_id": user_id,        # convenience claim used inside routes
        "email": email,
        "exp": expires_at,
        "iat": datetime.now(tz=timezone.utc),
    }
    try:
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return token
    except Exception as exc:
        logger.error("Failed to create JWT token for user_id=%s: %s", user_id, exc)
        raise


# ── JWT verification (FastAPI dependency) ─────────────────────────────────────
_http_bearer = HTTPBearer()


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_http_bearer)],
) -> dict:
    """
    FastAPI dependency — decode and validate a Bearer JWT token.

    Raises:
        HTTPException 401: If the token is missing, expired, or tampered with.

    Returns:
        A dict containing `user_id` (int) and `email` (str).
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: int | None = payload.get("user_id")
        email: str | None = payload.get("email")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"user_id": int(user_id), "email": email}

    except JWTError as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    user_info: Annotated[dict, Depends(verify_token)],
) -> dict:
    """
    Convenience dependency — returns the validated user dict from the JWT.

    Usage:
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    return user_info
