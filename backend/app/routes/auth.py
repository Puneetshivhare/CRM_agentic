"""
app/routes/auth.py — Authentication API endpoints.

Endpoints:
  POST /api/auth/signup  → Create user account
  POST /api/auth/login   → Authenticate and receive JWT
  GET  /api/auth/me      → Return current user info (requires JWT)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.auth import AuthUser

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Request / Response models ─────────────────────────────────────────────────

class SignupRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 characters)",
    )


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Returned token and user info after successful signup or login."""

    token: str = Field(..., description="JWT access token")
    user_id: int
    email: str
    message: str = "Success"


class MeResponse(BaseModel):
    """Current authenticated user's profile."""

    user_id: int
    email: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def signup(
    request: SignupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """
    Create a new user account and return a JWT token.

    - Validates email uniqueness
    - Hashes the password using bcrypt
    - Returns a JWT token on success
    """
    # Check if email already registered
    existing = db.query(AuthUser).filter(AuthUser.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = AuthUser(
        email=request.email,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: user_id=%s email=%s", user.user_id, user.email)

    token = create_access_token(user_id=user.user_id, email=user.email)
    return AuthResponse(
        token=token,
        user_id=user.user_id,
        email=user.email,
        message="Account created successfully",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and receive JWT token",
)
async def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """
    Authenticate a user with email + password.

    Returns a JWT token valid for `settings.jwt_expire_minutes` minutes.
    Always returns 401 on any failure to prevent user enumeration.
    """
    user: AuthUser | None = (
        db.query(AuthUser).filter(AuthUser.email == request.email).first()
    )

    # Constant-time check (avoids timing-based enumeration)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("User logged in: user_id=%s", user.user_id)

    token = create_access_token(user_id=user.user_id, email=user.email)
    return AuthResponse(token=token, user_id=user.user_id, email=user.email)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user",
)
async def me(
    user_info: Annotated[dict, Depends(get_current_user)],
) -> MeResponse:
    """
    Return the currently authenticated user's info.

    Requires a valid Bearer token in the Authorization header.
    """
    return MeResponse(user_id=user_info["user_id"], email=user_info["email"])
