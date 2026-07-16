from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel, Field


class AffiliateResult(BaseModel):
    affiliate_url: str
    provider: str
    campaign_id: str | None = None
    expires_at: datetime | None = None
    raw_response: dict[str, object] = Field(default_factory=dict)


class AffiliateProvider(ABC):
    @abstractmethod
    async def generate_deep_link(
        self,
        product_url: str,
        sub_id_1: str | None = None,
        sub_id_2: str | None = None,
        sub_id_3: str | None = None,
    ) -> AffiliateResult: ...
