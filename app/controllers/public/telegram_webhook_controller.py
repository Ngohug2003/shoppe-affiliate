from __future__ import annotations

from fastapi import BackgroundTasks

from app.schemas.telegram import TelegramUpdate, TelegramWebhookResponse
from app.services.telegram_webhook_service import TelegramWebhookService


class PublicTelegramWebhookController:
    def __init__(self, service: TelegramWebhookService) -> None:
        self.service = service

    def receive_update(
        self,
        update: TelegramUpdate,
        supplied_secret: str | None,
        background_tasks: BackgroundTasks,
    ) -> TelegramWebhookResponse:
        self.service.validate_webhook_secret(supplied_secret)
        background_tasks.add_task(self.service.process_update, update)
        return TelegramWebhookResponse()
