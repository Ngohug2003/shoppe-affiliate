from __future__ import annotations

from urllib.parse import urljoin

import httpx

from app.core.exceptions import InvalidShopeeUrlError, ShopeeUrlResolutionError
from app.schemas.urls import ResolvedShopeeUrl
from app.utils.urls import (
    SHORT_SHOPEE_HOSTS,
    ensure_public_host,
    normalize_shopee_landing_url,
    normalize_shopee_url,
    validate_shopee_url,
)

_REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class ShopeeUrlResolver:
    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        max_redirects: int = 5,
        max_response_bytes: int = 64 * 1024,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_redirects = max_redirects
        self.max_response_bytes = max_response_bytes

    async def resolve(
        self, url: str, *, client: httpx.AsyncClient | None = None
    ) -> ResolvedShopeeUrl:
        current_url = url
        original_url = url
        owns_client = client is None
        http_client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds),
            follow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ShopeeAffiliateBot/1.0)"},
        )
        try:
            for redirect_count in range(self.max_redirects + 1):
                hostname = validate_shopee_url(current_url)
                try:
                    normalized = normalize_shopee_url(current_url)
                except InvalidShopeeUrlError:
                    normalized = None
                if normalized is not None:
                    return ResolvedShopeeUrl(
                        original_url=original_url,
                        resolved_url=current_url,
                        normalized_url=normalized.normalized_url,
                        shop_id=normalized.shop_id,
                        item_id=normalized.item_id,
                    )
                if hostname not in SHORT_SHOPEE_HOSTS:
                    landing = normalize_shopee_landing_url(current_url)
                    return ResolvedShopeeUrl(
                        original_url=original_url,
                        resolved_url=current_url,
                        normalized_url=landing.normalized_url,
                    )
                await ensure_public_host(hostname)
                try:
                    response = await http_client.get(
                        current_url,
                        follow_redirects=False,
                        headers={
                            "User-Agent": "Mozilla/5.0 (compatible; ShopeeAffiliateBot/1.0)"
                        },
                    )
                except httpx.HTTPError as exc:
                    raise ShopeeUrlResolutionError("Shopee URL request failed") from exc

                if response.status_code in _REDIRECT_STATUSES:
                    if redirect_count == self.max_redirects:
                        raise ShopeeUrlResolutionError("Too many Shopee URL redirects")
                    location = response.headers.get("location")
                    if not location:
                        raise ShopeeUrlResolutionError("Shopee redirect is missing Location")
                    current_url = urljoin(current_url, location)
                    validate_shopee_url(current_url)
                    continue

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise ShopeeUrlResolutionError("Shopee URL returned an error") from exc
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.max_response_bytes:
                    raise ShopeeUrlResolutionError("Shopee URL response is too large")
                if len(response.content) > self.max_response_bytes:
                    raise ShopeeUrlResolutionError("Shopee URL response is too large")

                normalized = normalize_shopee_url(current_url)
                return ResolvedShopeeUrl(
                    original_url=original_url,
                    resolved_url=current_url,
                    normalized_url=normalized.normalized_url,
                    shop_id=normalized.shop_id,
                    item_id=normalized.item_id,
                )
        except InvalidShopeeUrlError:
            raise
        finally:
            if owns_client:
                await http_client.aclose()

        raise ShopeeUrlResolutionError("Shopee URL could not be resolved")
