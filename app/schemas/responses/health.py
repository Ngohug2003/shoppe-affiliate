from typing import Literal

from app.schemas.base import ApiResponseSchema


class LiveResponse(ApiResponseSchema):
    status: Literal["ok"]


class DependencyStatus(ApiResponseSchema):
    postgres: Literal["ok", "unavailable"]


class ReadyResponse(ApiResponseSchema):
    status: Literal["ready", "not_ready"]
    dependencies: DependencyStatus
