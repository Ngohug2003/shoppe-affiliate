from __future__ import annotations

import asyncio
from pathlib import PurePosixPath
from typing import Protocol
from urllib.parse import quote

import httpx
import structlog
from pydantic import BaseModel, ValidationError

from app.schemas.base import ApiResponse
from app.schemas.responses.affiliate_catalog import AffiliateProductResponse
from app.schemas.telegram import (
    TelegramApiResponse,
    TelegramDocument,
    TelegramFileResponse,
    TelegramUpdate,
    TelegramUpdatesResponse,
)
from app.services.excel_import_service import ExcelImportError, ExcelShopeeUrlExtractor
from app.utils.urls import extract_shopee_urls

logger = structlog.get_logger(__name__)


class CatalogApiError(RuntimeError):
    pass


class TelegramApiError(RuntimeError):
    pass


class CatalogProductImporter(Protocol):
    async def import_product(self, url: str) -> AffiliateProductResponse: ...


class _TokenResponse(BaseModel):
    access_token: str


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
            payload = ApiResponse[AffiliateProductResponse].model_validate(
                response.json()
            )
        except (ValueError, ValidationError) as exc:
            raise CatalogApiError("Catalog API returned an invalid response") from exc
        if payload.data is None:
            raise CatalogApiError("Catalog API returned an empty product response")
        return payload.data

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
            payload = ApiResponse[_TokenResponse].model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise CatalogApiError("Catalog API authentication response is invalid") from exc
        if payload.data is None:
            raise CatalogApiError("Catalog API authentication response has no token")
        self.access_token = payload.data.access_token

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
            payload = response.json()
        except (ValueError, AttributeError):
            return "unknown error"
        status_payload = payload.get("status")
        if isinstance(status_payload, dict):
            message = status_payload.get("message")
            if message:
                return str(message)
        detail = payload.get("detail")
        return str(detail) if detail else "unknown error"


class TelegramCatalogBot:
    def __init__(
        self,
        *,
        token: str,
        polling_timeout_seconds: int,
        telegram_client: httpx.AsyncClient,
        catalog_client: CatalogProductImporter,
        excel_import_delay_seconds: float = 3.0,
        excel_max_file_bytes: int = 5 * 1024 * 1024,
        excel_max_links: int = 200,
        excel_max_cells: int = 100_000,
    ) -> None:
        self.token = token
        self.telegram_base_url = f"https://api.telegram.org/bot{token}"
        self.polling_timeout_seconds = polling_timeout_seconds
        self.telegram_client = telegram_client
        self.catalog_client = catalog_client
        self.excel_import_delay_seconds = excel_import_delay_seconds
        self.excel_max_file_bytes = excel_max_file_bytes
        self.excel_extractor = ExcelShopeeUrlExtractor(
            max_links=excel_max_links,
            max_cells=excel_max_cells,
        )
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
        if update.message is None:
            return
        chat_id = update.message.chat.id
        if update.message.document is not None:
            await self._handle_excel_document(chat_id, update.message.document)
            return
        if update.message.text is None:
            return
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

    async def _handle_excel_document(
        self, chat_id: int, document: TelegramDocument
    ) -> None:
        file_name = document.file_name or ""
        if not file_name.lower().endswith(".xlsx"):
            await self._send_message(
                chat_id,
                "❌ Chỉ hỗ trợ file Excel định dạng .xlsx.",
            )
            return
        if (
            document.file_size is not None
            and document.file_size > self.excel_max_file_bytes
        ):
            await self._send_message(
                chat_id,
                f"❌ File vượt quá giới hạn {self.excel_max_file_bytes // (1024 * 1024)} MB.",
            )
            return

        await self._send_message(chat_id, "📥 Đã nhận file Excel, đang kiểm tra link Shopee...")
        try:
            content = await self._download_telegram_file(document.file_id)
            extraction = await asyncio.to_thread(self.excel_extractor.extract, content)
        except (ExcelImportError, TelegramApiError) as exc:
            await self._send_message(chat_id, f"❌ Không thể đọc file Excel: {exc}")
            return

        if not extraction.urls:
            await self._send_message(
                chat_id,
                "❌ Không tìm thấy link Shopee nào trong file Excel.",
            )
            return

        notices: list[str] = []
        if extraction.link_limit_reached:
            notices.append("đã đạt giới hạn số link")
        if extraction.scan_limit_reached:
            notices.append("đã đạt giới hạn số ô quét")
        suffix = f" ({', '.join(notices)})" if notices else ""
        await self._send_message(
            chat_id,
            f"🔎 Tìm thấy {len(extraction.urls)} link. Bắt đầu thêm tuần tự{suffix}.",
        )

        succeeded = 0
        failed = 0
        total = len(extraction.urls)
        for index, url in enumerate(extraction.urls, start=1):
            try:
                product = await self.catalog_client.import_product(url)
            except CatalogApiError as exc:
                failed += 1
                await self._send_message(
                    chat_id,
                    f"❌ [{index}/{total}] {url}\nLỗi: {exc}",
                )
            else:
                succeeded += 1
                await self._send_message(
                    chat_id,
                    self._batch_success_message(product, index=index, total=total),
                )
            if index < total and self.excel_import_delay_seconds > 0:
                await asyncio.sleep(self.excel_import_delay_seconds)

        await self._send_message(
            chat_id,
            "🏁 Hoàn tất file Excel\n"
            f"✅ Thành công: {succeeded}\n"
            f"❌ Thất bại: {failed}\n"
            f"📦 Tổng cộng: {total}",
        )

    async def _download_telegram_file(self, file_id: str) -> bytes:
        response = await self._post_telegram("getFile", {"file_id": file_id})
        try:
            payload = TelegramFileResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise TelegramApiError("Telegram getFile trả về dữ liệu không hợp lệ") from exc
        if response.is_error or not payload.ok or payload.result is None:
            raise TelegramApiError(payload.description or "Telegram không trả về file_path")

        file_path = payload.result.file_path.lstrip("/")
        if ".." in PurePosixPath(file_path).parts:
            raise TelegramApiError("Telegram trả về file_path không hợp lệ")
        download_url = (
            f"https://api.telegram.org/file/bot{self.token}/{quote(file_path, safe='/')}"
        )
        content = bytearray()
        try:
            async with self.telegram_client.stream(
                "GET", download_url, timeout=60
            ) as download_response:
                download_response.raise_for_status()
                async for chunk in download_response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > self.excel_max_file_bytes:
                        raise ExcelImportError("File Excel vượt quá giới hạn dung lượng")
        except httpx.HTTPError as exc:
            raise TelegramApiError("Không thể tải file Excel từ Telegram") from exc
        return bytes(content)

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
            parsed = TelegramUpdatesResponse.model_validate(response.json())
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
            parsed = TelegramApiResponse.model_validate(response.json())
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

    @staticmethod
    def _batch_success_message(
        product: AffiliateProductResponse, *, index: int, total: int
    ) -> str:
        return (
            f"✅ [{index}/{total}] Đã thêm sản phẩm\n"
            f"Tên: {product.title}\n"
            f"Link affiliate: {product.affiliate_url}"
        )
