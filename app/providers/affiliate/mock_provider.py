from urllib.parse import urlencode

from app.providers.affiliate.base import AffiliateProvider, AffiliateResult


class MockAffiliateProvider(AffiliateProvider):
    async def generate_deep_link(
        self,
        product_url: str,
        sub_id_1: str | None = None,
        sub_id_2: str | None = None,
        sub_id_3: str | None = None,
    ) -> AffiliateResult:
        query = urlencode(
            {
                "target": product_url,
                "sub_id_1": sub_id_1 or "",
                "sub_id_2": sub_id_2 or "",
                "sub_id_3": sub_id_3 or "",
            }
        )
        return AffiliateResult(
            affiliate_url=f"https://mock.invalid/affiliate?{query}",
            provider="mock",
            raw_response={"mock": True},
        )
