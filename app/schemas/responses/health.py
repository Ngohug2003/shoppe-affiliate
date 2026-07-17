from typing import Literal

from pydantic import BaseModel


class LiveResponse(BaseModel):
    status: Literal["ok"]


class DependencyStatus(BaseModel):
    postgres: Literal["ok", "unavailable"]


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: DependencyStatus
