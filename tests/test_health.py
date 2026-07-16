from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import health
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client


def test_live_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"]


def test_openapi_exposes_affiliate_catalog(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/affiliate-products" in paths
    assert "/api/v1/affiliate-shops" in paths
    assert "/api/v1/affiliate-shops/{shop_id}/products" in paths


def test_ready_when_dependencies_are_available(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def available() -> bool:
        return True

    monkeypatch.setattr(
        health.health_controller.service, "is_postgres_ready", available
    )

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {"postgres": "ok"},
    }


def test_ready_returns_503_when_postgres_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unavailable() -> bool:
        return False

    monkeypatch.setattr(
        health.health_controller.service, "is_postgres_ready", unavailable
    )

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["dependencies"]["postgres"] == "unavailable"
