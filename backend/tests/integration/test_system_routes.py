def test_root_endpoint_returns_docs_hint(main_client):
    response = main_client.get("/")

    assert response.status_code == 200
    assert "visit /docs" in response.json()["message"]


def test_health_endpoint_returns_degraded_when_db_unreachable(main_client):
    response = main_client.get("/health")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["database"] == "unreachable"


def test_health_endpoint_returns_ok_when_db_is_connected(main_client, monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "check_db_connection", lambda: True)
    response = main_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "connected"
