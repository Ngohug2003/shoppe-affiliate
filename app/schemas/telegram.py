from pydantic import BaseModel, Field


class TelegramChat(BaseModel):
    id: int


class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None


class TelegramApiResponse(BaseModel):
    ok: bool
    description: str | None = None


class TelegramUpdatesResponse(TelegramApiResponse):
    result: list[TelegramUpdate] = Field(default_factory=list)


class TelegramWebhookResponse(BaseModel):
    ok: bool = True
