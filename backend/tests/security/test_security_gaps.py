from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.routes import documents as documents_router
from app.routes import enrichment as enrichment_router
from app.routes import prospects as prospects_router


class _FakeQuery:
    def filter(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self

    def count(self):
        return 0

    def order_by(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self

    def offset(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self

    def limit(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return self

    def all(self):
        return []

    def first(self):
        return None


class _FakeDB:
    def query(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return _FakeQuery()

    def add(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def flush(self):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None

    def refresh(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def close(self):
        return None


def _client_for_router(router) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        db = _FakeDB()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.mark.xfail(
    reason="Known gap: prospects endpoints still use stubbed user_id and do not enforce JWT auth.",
    strict=False,
)
def test_prospects_list_requires_authentication():
    client = _client_for_router(prospects_router.router)

    response = client.get("/api/prospects")

    assert response.status_code == 401


@pytest.mark.xfail(
    reason="Known gap: documents endpoints do not enforce JWT auth yet.",
    strict=False,
)
def test_documents_list_requires_authentication():
    client = _client_for_router(documents_router.router)

    response = client.get("/api/documents")

    assert response.status_code == 401


@pytest.mark.xfail(
    reason="Known gap: enrichment trigger endpoint does not enforce JWT auth yet.",
    strict=False,
)
def test_enrichment_trigger_requires_authentication():
    client = _client_for_router(enrichment_router.router)

    response = client.post("/api/enrichment/trigger", json={"prospect_id": 123})

    assert response.status_code == 401


@pytest.mark.xfail(
    reason="Known gap: frontend stores JWT in localStorage; migrate to HttpOnly cookies for production.",
    strict=False,
)
def test_frontend_does_not_store_jwt_in_localstorage():
    repo_root = Path(__file__).resolve().parents[3]
    api_client_file = repo_root / "frontend" / "src" / "lib" / "api.ts"
    login_page_file = repo_root / "frontend" / "src" / "app" / "login" / "page.tsx"

    api_client_source = api_client_file.read_text(encoding="utf-8")
    login_page_source = login_page_file.read_text(encoding="utf-8")

    assert "localStorage" not in api_client_source
    assert "localStorage" not in login_page_source
