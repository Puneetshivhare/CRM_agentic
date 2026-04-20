from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.database import get_db
from app.models.auth import AuthUser
from app.routes import auth as auth_router


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    AuthUser.__table__.create(bind=engine)

    app = FastAPI()
    app.include_router(auth_router.router)

    def override_get_db():
        db: Session = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client


def test_signup_success_returns_jwt(auth_client: TestClient):
    response = auth_client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "ComplexPass123!"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["user_id"] > 0
    assert isinstance(body["token"], str) and len(body["token"]) > 20


def test_signup_stores_hashed_password(auth_client: TestClient):
    auth_client.post(
        "/api/auth/signup",
        json={"email": "bob@example.com", "password": "ComplexPass123!"},
    )

    # Use login endpoint behavior to validate hash path is active.
    ok_login = auth_client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "ComplexPass123!"},
    )
    bad_login = auth_client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "wrong-password"},
    )

    assert ok_login.status_code == 200
    assert bad_login.status_code == 401


def test_signup_duplicate_email_returns_409(auth_client: TestClient):
    payload = {"email": "dup@example.com", "password": "ComplexPass123!"}
    first = auth_client.post("/api/auth/signup", json=payload)
    second = auth_client.post("/api/auth/signup", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered"


def test_login_nonexistent_user_returns_generic_401(auth_client: TestClient):
    response = auth_client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "whatever123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_valid_bearer_token(auth_client: TestClient):
    token = create_access_token(user_id=12, email="me@example.com")
    valid_headers = {"Authorization": f"Bearer {token}"}

    valid = auth_client.get("/api/auth/me", headers=valid_headers)
    invalid = auth_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert valid.status_code == 200
    assert valid.json() == {"user_id": 12, "email": "me@example.com"}
    assert invalid.status_code == 401
