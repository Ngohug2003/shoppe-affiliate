from pydantic import BaseModel, Field


class TelegramChat(BaseModel):
    id: int


class TelegramDocument(BaseModel):
    file_id: str
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str | None = None
    document: TelegramDocument | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None


class TelegramApiResponse(BaseModel):
    ok: bool
    description: str | None = None


class TelegramUpdatesResponse(TelegramApiResponse):
    result: list[TelegramUpdate] = Field(default_factory=list)


class TelegramFile(BaseModel):
    file_path: str


class TelegramFileResponse(TelegramApiResponse):
    result: TelegramFile | None = None


class TelegramWebhookResponse(BaseModel):
    ok: bool = True
