from __future__ import annotations

from secrets import compare_digest

from fastapi import BackgroundTasks, HTTPException, status

from app.schemas.telegram import TelegramUpdate, TelegramWebhookResponse
from app.services.telegram_webhook_service import TelegramWebhookService


class TelegramWebhookController:
    def __init__(self, service: TelegramWebhookService) -> None:
        self.service = service

    def receive_update(
        self,
        update: TelegramUpdate,
        supplied_secret: str | None,
        background_tasks: BackgroundTasks,
    ) -> TelegramWebhookResponse:
        if not self.service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram webhook is not configured",
            )
        if supplied_secret is None or not compare_digest(
            supplied_secret, self.service.secret
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Telegram webhook secret",
            )
        background_tasks.add_task(self.service.process_update, update)
        return TelegramWebhookResponse()
