from __future__ import annotations

import asyncio

import httpx

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.telegram_catalog_bot import CatalogApiClient, TelegramCatalogBot


async def run() -> None:
    settings = get_settings()
    token = settings.TELEGRAM_BOT_TOKEN.strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    configure_logging(settings.LOG_LEVEL)

    async with (
        httpx.AsyncClient(timeout=30) as catalog_http_client,
        httpx.AsyncClient(
            timeout=settings.TELEGRAM_POLLING_TIMEOUT_SECONDS + 10
        ) as telegram_http_client,
    ):
        catalog_client = CatalogApiClient(
            base_url=str(settings.CATALOG_API_BASE_URL),
            admin_email=settings.ADMIN_EMAIL,
            admin_password=settings.ADMIN_PASSWORD,
            client=catalog_http_client,
        )
        bot = TelegramCatalogBot(
            token=token,
            polling_timeout_seconds=settings.TELEGRAM_POLLING_TIMEOUT_SECONDS,
            telegram_client=telegram_http_client,
            catalog_client=catalog_client,
            excel_import_delay_seconds=settings.TELEGRAM_EXCEL_IMPORT_DELAY_SECONDS,
            excel_max_file_bytes=settings.TELEGRAM_EXCEL_MAX_FILE_BYTES,
            excel_max_links=settings.TELEGRAM_EXCEL_MAX_LINKS,
            excel_max_cells=settings.TELEGRAM_EXCEL_MAX_CELLS,
        )
        await bot.run()


if __name__ == "__main__":
    asyncio.run(run())
