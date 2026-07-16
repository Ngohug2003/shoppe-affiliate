from __future__ import annotations

import asyncio

import httpx
import structlog
from pydantic import BaseModel, Field, ValidationError

from app.schemas.affiliate_catalog import AffiliateProductResponse
from app.utils.urls import extract_shopee_urls

logger = structlog.get_logger(__name__)


class CatalogApiError(RuntimeError):
    pass


class TelegramApiError(RuntimeError):
    pass


class _TokenResponse(BaseModel):
    access_token: str


class TelegramChat(BaseModel):
    id: int


class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None


class _TelegramResponse(BaseModel):
    ok: bool
    description: str | None = None


class _TelegramUpdatesResponse(_TelegramResponse):
    result: list[TelegramUpdate] = Field(default_factory=list)


class CatalogApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        admin_email: str,
        admin_password: str,
        client: httpx.AsyncClient,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.client = client
        self.access_token: str | None = None

    async def import_product(self, url: str) -> AffiliateProductResponse:
        if self.access_token is None:
            await self._authenticate()
        response = await self._post_product(url)
        if response.status_code == httpx.codes.UNAUTHORIZED:
            await self._authenticate()
            response = await self._post_product(url)
        if response.is_error:
            raise CatalogApiError(
                f"Catalog API returned HTTP {response.status_code}: {self._error_detail(response)}"
            )
        try:
            return AffiliateProductResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise CatalogApiError("Catalog API returned an invalid response") from exc

    async def _authenticate(self) -> None:
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/token",
                data={
                    "username": self.admin_email,
                    "password": self.admin_password,
                },
            )
        except httpx.HTTPError as exc:
            raise CatalogApiError("Catalog API authentication request failed") from exc
        if response.is_error:
            raise CatalogApiError(
                f"Catalog API authentication failed with HTTP {response.status_code}"
            )
        try:
            self.access_token = _TokenResponse.model_validate(response.json()).access_token
        except (ValueError, ValidationError) as exc:
            raise CatalogApiError("Catalog API authentication response is invalid") from exc

    async def _post_product(self, url: str) -> httpx.Response:
        try:
            return await self.client.post(
                f"{self.base_url}/api/v1/affiliate-products",
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={"url": url},
            )
        except httpx.HTTPError as exc:
            raise CatalogApiError("Catalog API product request failed") from exc

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            return "unknown error"
        return str(detail) if detail else "unknown error"


class TelegramCatalogBot:
    def __init__(
        self,
        *,
        token: str,
        polling_timeout_seconds: int,
        telegram_client: httpx.AsyncClient,
        catalog_client: CatalogApiClient,
    ) -> None:
        self.telegram_base_url = f"https://api.telegram.org/bot{token}"
        self.polling_timeout_seconds = polling_timeout_seconds
        self.telegram_client = telegram_client
        self.catalog_client = catalog_client
        self.offset: int | None = None

    async def run(self) -> None:
        await self._delete_webhook()
        logger.info("telegram_catalog_bot_started")
        while True:
            try:
                updates = await self._get_updates()
                for update in updates:
                    self.offset = update.update_id + 1
                    await self.handle_update(update)
            except asyncio.CancelledError:
                raise
            except (CatalogApiError, TelegramApiError) as exc:
                logger.warning(
                    "telegram_catalog_bot_iteration_failed",
                    error_type=type(exc).__name__,
                )
                await asyncio.sleep(3)

    async def handle_update(self, update: TelegramUpdate) -> None:
        if update.message is None or update.message.text is None:
            return
        chat_id = update.message.chat.id
        urls = extract_shopee_urls(update.message.text)
        if not urls:
            await self._send_message(chat_id, "Hãy gửi một link sản phẩm Shopee hợp lệ.")
            return

        for url in urls[:3]:
            try:
                product = await self.catalog_client.import_product(url)
            except CatalogApiError as exc:
                await self._send_message(chat_id, f"❌ Không thể thêm sản phẩm: {exc}")
                continue
            await self._send_message(chat_id, self._success_message(product))

    async def _delete_webhook(self) -> None:
        response = await self._post_telegram(
            "deleteWebhook", {"drop_pending_updates": False}
        )
        self._validate_telegram_response(response)

    async def _get_updates(self) -> list[TelegramUpdate]:
        payload: dict[str, object] = {
            "timeout": self.polling_timeout_seconds,
            "allowed_updates": ["message"],
        }
        if self.offset is not None:
            payload["offset"] = self.offset
        response = await self._post_telegram(
            "getUpdates",
            payload,
            request_timeout=self.polling_timeout_seconds + 10,
        )
        try:
            parsed = _TelegramUpdatesResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise TelegramApiError("Telegram getUpdates response is invalid") from exc
        if response.is_error or not parsed.ok:
            raise TelegramApiError(parsed.description or "Telegram getUpdates failed")
        return parsed.result

    async def _send_message(self, chat_id: int, text: str) -> None:
        response = await self._post_telegram(
            "sendMessage", {"chat_id": chat_id, "text": text}
        )
        self._validate_telegram_response(response)

    async def _post_telegram(
        self,
        method: str,
        payload: dict[str, object],
        *,
        request_timeout: float | None = None,
    ) -> httpx.Response:
        try:
            return await self.telegram_client.post(
                f"{self.telegram_base_url}/{method}",
                json=payload,
                timeout=request_timeout,
            )
        except httpx.HTTPError:
            raise TelegramApiError(f"Telegram {method} request failed") from None

    @staticmethod
    def _validate_telegram_response(response: httpx.Response) -> None:
        try:
            parsed = _TelegramResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise TelegramApiError("Telegram response is invalid") from exc
        if response.is_error or not parsed.ok:
            raise TelegramApiError(parsed.description or "Telegram request failed")

    @staticmethod
    def _success_message(product: AffiliateProductResponse) -> str:
        return (
            "✅ Đã thêm sản phẩm\n"
            f"Tên: {product.title}\n"
            f"Shop ID: {product.shop_id}\n"
            f"Product ID: {product.item_id}\n"
            f"Link affiliate: {product.affiliate_url}"
        )
