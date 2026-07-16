from __future__ import annotations

import httpx
import structlog

from app.core.config import Settings
from app.schemas.telegram import TelegramApiResponse, TelegramUpdate
from app.services.telegram_catalog_bot import CatalogApiClient, TelegramCatalogBot

logger = structlog.get_logger(__name__)


class TelegramWebhookConfigurationError(RuntimeError):
    pass


class TelegramWebhookService:
    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.TELEGRAM_WEBHOOK_ENABLED
        self.token = settings.TELEGRAM_BOT_TOKEN.strip()
        self.secret = settings.TELEGRAM_WEBHOOK_SECRET.strip()
        self.webhook_url = (
            f"{str(settings.APP_BASE_URL).rstrip('/')}/api/v1/telegram/webhook"
        )
        self.catalog_base_url = str(settings.CATALOG_API_BASE_URL)
        self.admin_email = settings.ADMIN_EMAIL
        self.admin_password = settings.ADMIN_PASSWORD
        self.polling_timeout_seconds = settings.TELEGRAM_POLLING_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.token) and bool(self.secret)

    async def register(self) -> bool:
        if not self.enabled:
            return False
        if not self.token or not self.secret:
            raise TelegramWebhookConfigurationError(
                "Telegram webhook requires TELEGRAM_BOT_TOKEN and "
                "TELEGRAM_WEBHOOK_SECRET"
            )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{self.token}/setWebhook",
                json={
                    "url": self.webhook_url,
                    "secret_token": self.secret,
                    "allowed_updates": ["message"],
                    "drop_pending_updates": False,
                },
            )
        try:
            payload = TelegramApiResponse.model_validate(response.json())
        except ValueError as exc:
            raise TelegramWebhookConfigurationError(
                "Telegram setWebhook returned an invalid response"
            ) from exc
        if response.is_error or not payload.ok:
            raise TelegramWebhookConfigurationError(
                payload.description or "Telegram setWebhook failed"
            )
        logger.info("telegram_webhook_registered", webhook_url=self.webhook_url)
        return True

    async def process_update(self, update: TelegramUpdate) -> None:
        if not self.is_configured:
            logger.warning("telegram_webhook_update_skipped_not_configured")
            return
        async with (
            httpx.AsyncClient(timeout=90) as catalog_http_client,
            httpx.AsyncClient(timeout=30) as telegram_http_client,
        ):
            catalog_client = CatalogApiClient(
                base_url=self.catalog_base_url,
                admin_email=self.admin_email,
                admin_password=self.admin_password,
                client=catalog_http_client,
            )
            bot = TelegramCatalogBot(
                token=self.token,
                polling_timeout_seconds=self.polling_timeout_seconds,
                telegram_client=telegram_http_client,
                catalog_client=catalog_client,
            )
            await bot.handle_update(update)
