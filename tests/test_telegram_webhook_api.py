from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import telegram_webhook


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client


def configure_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    service = telegram_webhook.telegram_webhook_controller.service
    monkeypatch.setattr(service, "enabled", True)
    monkeypatch.setattr(service, "token", "test-token")
    monkeypatch.setattr(service, "secret", "test-secret")


def test_webhook_returns_503_when_not_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = telegram_webhook.telegram_webhook_controller.service
    monkeypatch.setattr(service, "enabled", False)

    response = client.post(
        "/api/v1/telegram/webhook",
        json={"update_id": 1},
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": {"code": 503, "message": "Telegram webhook chưa được cấu hình"},
        "data": None,
    }


def test_webhook_rejects_invalid_secret(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_webhook(monkeypatch)

    response = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        json={"update_id": 1},
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": {
            "code": 403,
            "message": "Telegram webhook secret không hợp lệ",
        },
        "data": None,
    }


def test_webhook_accepts_update_and_processes_it(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_webhook(monkeypatch)
    service = telegram_webhook.telegram_webhook_controller.service
    process_update = AsyncMock()
    monkeypatch.setattr(service, "process_update", process_update)
    payload = {
        "update_id": 1,
        "message": {
            "chat": {"id": 99},
            "text": "https://vn.shp.ee/cMvxmJNm",
        },
    }

    response = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": {"code": 200, "message": ""},
        "data": {"ok": True},
    }
    process_update.assert_awaited_once()
