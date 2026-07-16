from __future__ import annotations

import httpx

from app.core.config import Settings
from app.core.exceptions import ApplicationError
from app.providers.affiliate.base import AffiliateProvider, AffiliateResult


class AffiliateProviderError(ApplicationError):
    pass


class OfficialAffiliateProvider(AffiliateProvider):
    """Calls only the operator-provided official endpoint; no endpoint is inferred."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.client = client

    async def generate_deep_link(
        self,
        product_url: str,
        sub_id_1: str | None = None,
        sub_id_2: str | None = None,
        sub_id_3: str | None = None,
    ) -> AffiliateResult:
        if not all(
            (
                self.settings.AFFILIATE_API_BASE_URL,
                self.settings.AFFILIATE_API_KEY,
                self.settings.AFFILIATE_PUBLISHER_ID,
            )
        ):
            raise AffiliateProviderError("Official affiliate provider is not configured")
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.AFFILIATE_TIMEOUT_SECONDS)
        )
        try:
            response = await client.post(
                self.settings.AFFILIATE_API_BASE_URL,
                headers={"Authorization": f"Bearer {self.settings.AFFILIATE_API_KEY}"},
                json={
                    "publisher_id": self.settings.AFFILIATE_PUBLISHER_ID,
                    "product_url": product_url,
                    "sub_id_1": sub_id_1,
                    "sub_id_2": sub_id_2,
                    "sub_id_3": sub_id_3,
                },
            )
            response.raise_for_status()
            payload = response.json()
            affiliate_url = payload.get("affiliate_url")
            if not isinstance(affiliate_url, str):
                raise AffiliateProviderError("Official provider response has no affiliate_url")
            return AffiliateResult(
                affiliate_url=affiliate_url,
                provider="official",
                campaign_id=payload.get("campaign_id"),
                raw_response=payload,
            )
        except httpx.HTTPError as exc:
            raise AffiliateProviderError("Official affiliate request failed") from exc
        finally:
            if owns_client:
                await client.aclose()
