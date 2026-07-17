from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.constants.tags import OPENAPI_TAGS
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import close_database
from app.routes import api_router
from app.services.telegram_webhook_service import (
    TelegramWebhookConfigurationError,
    TelegramWebhookService,
)

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application_started", environment=settings.APP_ENV)
    webhook_service = TelegramWebhookService(settings)
    try:
        await webhook_service.register()
    except (httpx.HTTPError, TelegramWebhookConfigurationError) as exc:
        logger.error(
            "telegram_webhook_registration_failed",
            error_type=type(exc).__name__,
        )
    yield
    await close_database()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="0.6.0",
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)

    @application.middleware("http")
    async def correlation_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        clear_contextvars()
        bind_contextvars(correlation_id=correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    application.include_router(api_router)
    return application


app = create_app()
