from __future__ import annotations

import httpx
import structlog

from app.core.config import Settings
from app.core.exceptions import ApplicationError
from app.db.session import async_session_factory
from app.providers.affiliate import build_affiliate_provider
from app.schemas.responses.affiliate_catalog import AffiliateProductResponse
from app.schemas.telegram import TelegramApiResponse, TelegramUpdate
from app.services.affiliate_catalog_service import AffiliateCatalogService
from app.services.telegram_catalog_bot import (
    CatalogApiError,
    TelegramCatalogBot,
)

logger = structlog.get_logger(__name__)


class TelegramWebhookConfigurationError(RuntimeError):
    pass


class DirectCatalogImporter:
    def __init__(
        self,
        service: AffiliateCatalogService,
        client: httpx.AsyncClient,
    ) -> None:
        self.service = service
        self.client = client

    async def import_product(self, url: str) -> AffiliateProductResponse:
        try:
            async with async_session_factory() as session:
                product = await self.service.import_product(
                    session,
                    url,
                    client=self.client,
                )
        except ApplicationError as exc:
            raise CatalogApiError(str(exc)) from exc
        return AffiliateProductResponse(**product.__dict__)


class TelegramWebhookService:
    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.TELEGRAM_WEBHOOK_ENABLED
        self.token = settings.TELEGRAM_BOT_TOKEN.strip()
        self.secret = settings.TELEGRAM_WEBHOOK_SECRET.strip()
        self.webhook_url = (
            f"{str(settings.APP_BASE_URL).rstrip('/')}/api/v1/telegram/webhook"
        )
        self.polling_timeout_seconds = settings.TELEGRAM_POLLING_TIMEOUT_SECONDS
        self.catalog_service = AffiliateCatalogService(
            build_affiliate_provider(settings)
        )

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
            httpx.AsyncClient(timeout=90) as product_http_client,
            httpx.AsyncClient(timeout=30) as telegram_http_client,
        ):
            catalog_client = DirectCatalogImporter(
                self.catalog_service,
                product_http_client,
            )
            bot = TelegramCatalogBot(
                token=self.token,
                polling_timeout_seconds=self.polling_timeout_seconds,
                telegram_client=telegram_http_client,
                catalog_client=catalog_client,
            )
            await bot.handle_update(update)
