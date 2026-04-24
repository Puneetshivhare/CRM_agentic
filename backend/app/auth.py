"""
app/auth.py — JWT authentication helpers using Authlib.

Provides:
  - `hash_password()`      → bcrypt password hashing
  - `verify_password()`    → bcrypt comparison
  - `create_access_token()` → JWT creation (Authlib)
  - `verify_token()`       → JWT validation (FastAPI dependency using Authlib)
  - `get_current_user()`   → Convenience dependency wrapping verify_token
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from authlib.jose import jwt, JoseError
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
    """Hash a plain-text password using bcrypt."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare a plain-text password against a stored bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT token creation (Authlib) ──────────────────────────────────────────────
def create_access_token(user_id: int, email: str) -> str:
    """Create a signed JWT access token using Authlib."""
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_expire_minutes)
    
    header = {"alg": settings.jwt_algorithm}
    payload = {
        "iss": "agentic-crm",
        "sub": str(user_id),
        "user_id": user_id,
        "email": email,
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),
    }
    
    try:
        token = jwt.encode(header, payload, settings.jwt_secret_key)
        return token.decode("utf-8") if isinstance(token, bytes) else token
    except Exception as exc:
        logger.error("Failed to create JWT token for user_id=%s: %s", user_id, exc)
        raise


# ── JWT verification (FastAPI dependency) ─────────────────────────────────────
_http_bearer = HTTPBearer()


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_http_bearer)],
) -> dict:
    """FastAPI dependency — decode and validate a Bearer JWT token using Authlib."""
    token = credentials.credentials
    try:
        # Authlib jwt.decode takes key and optional algorithms
        claims = jwt.decode(token, settings.jwt_secret_key)
        
        # Verify basic claims manually as simple Authlib doesn't auto-verify 'exp' without extra config
        claims.validate()
        
        user_id = claims.get("user_id")
        email = claims.get("email")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"user_id": int(user_id), "email": email}

    except JoseError as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    user_info: Annotated[dict, Depends(verify_token)],
) -> dict:
    """Convenience dependency — returns the validated user dict from the JWT."""
    return user_info
