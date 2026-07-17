from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header

from app.constants.tags import PUBLIC_TELEGRAM_TAG
from app.controllers.public.telegram_webhook_controller import (
    PublicTelegramWebhookController,
)
from app.core.config import get_settings
from app.schemas.base import ApiResponse, success_response
from app.schemas.telegram import TelegramUpdate, TelegramWebhookResponse
from app.services.telegram_webhook_service import TelegramWebhookService

router = APIRouter(tags=[PUBLIC_TELEGRAM_TAG])
telegram_webhook_controller = PublicTelegramWebhookController(
    TelegramWebhookService(get_settings())
)


@router.post(
    "/telegram/webhook",
    response_model=ApiResponse[TelegramWebhookResponse],
)
async def receive_telegram_webhook(
    update: TelegramUpdate,
    background_tasks: BackgroundTasks,
    telegram_secret: Annotated[
        str | None,
        Header(alias="X-Telegram-Bot-Api-Secret-Token"),
    ] = None,
) -> ApiResponse[TelegramWebhookResponse]:
    response = telegram_webhook_controller.receive_update(
        update, telegram_secret, background_tasks
    )
    return success_response(response)
