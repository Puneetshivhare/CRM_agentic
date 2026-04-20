import os

import pytest
from fastapi.testclient import TestClient


# Provide deterministic defaults for tests so app settings can be imported
# without relying on developer-specific .env values.
os.environ.setdefault("DATABASE_URL", "postgresql://test_user:test_pass@localhost:5432/test_db")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-chars")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("BCRYPT_ROUNDS", "4")


@pytest.fixture
def main_client(monkeypatch):
    import app.main as main_module

    # Avoid real DB connectivity during test startup.
    monkeypatch.setattr(main_module, "check_db_connection", lambda: False)
    with TestClient(main_module.app) as client:
        yield client
