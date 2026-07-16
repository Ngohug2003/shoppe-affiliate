from __future__ import annotations

import re
from urllib.parse import urlencode

from app.core.config import Settings
from app.providers.affiliate.base import AffiliateProvider, AffiliateResult
from app.providers.affiliate.official_provider import AffiliateProviderError
from app.utils.urls import normalize_shopee_landing_url

_SAFE_SUB_ID = re.compile(r"[^A-Za-z0-9_]", flags=re.ASCII)


class ShopeeRedirectAffiliateProvider(AffiliateProvider):
    """Build Shopee's documented ``an_redir`` affiliate URL locally."""

    def __init__(self, settings: Settings) -> None:
        self.publisher_id = settings.AFFILIATE_PUBLISHER_ID.strip()

    async def generate_deep_link(
        self,
        product_url: str,
        sub_id_1: str | None = None,
        sub_id_2: str | None = None,
        sub_id_3: str | None = None,
    ) -> AffiliateResult:
        if not self.publisher_id:
            raise AffiliateProviderError("Shopee affiliate publisher ID is not configured")
        if not self.publisher_id.isdigit():
            raise AffiliateProviderError("Shopee affiliate publisher ID must contain only digits")

        normalized_url = normalize_shopee_landing_url(product_url).normalized_url
        sub_id = "-".join(
            self._sanitize_sub_id(value)
            for value in (sub_id_1, sub_id_2, sub_id_3)
            if value
        )
        query = {"origin_link": normalized_url, "affiliate_id": self.publisher_id}
        if sub_id:
            query["sub_id"] = sub_id

        return AffiliateResult(
            affiliate_url=f"https://s.shopee.vn/an_redir?{urlencode(query)}",
            provider="shopee_redirect",
            raw_response={"generated_locally": True},
        )

    @staticmethod
    def _sanitize_sub_id(value: str) -> str:
        return _SAFE_SUB_ID.sub("_", value.strip())[:64]
