from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

from app.core.exceptions import ApplicationError
from app.utils.urls import ensure_public_host, validate_shopee_url

_ALLOWED_IMAGE_SUFFIXES = (".susercontent.com", ".shopeeusercontent.com")
_CRAWLER_USER_AGENT = (
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
)


class ProductMetadataError(ApplicationError):
    pass


@dataclass(frozen=True)
class ProductMetadata:
    title: str
    image_url: str
    source: str = "shopee_open_graph"


class _OpenGraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "meta":
            return
        values = {key.lower(): value for key, value in attrs if value is not None}
        property_name = values.get("property") or values.get("name")
        content = values.get("content")
        if property_name in {"og:title", "og:image"} and content:
            self.values[property_name] = unescape(content).strip()


class ShopeeOpenGraphMetadataProvider:
    def __init__(self, *, max_response_bytes: int = 512 * 1024) -> None:
        self.max_response_bytes = max_response_bytes

    async def fetch(
        self, product_url: str, *, client: httpx.AsyncClient
    ) -> ProductMetadata:
        hostname = validate_shopee_url(product_url)
        await ensure_public_host(hostname)
        try:
            async with client.stream(
                "GET",
                product_url,
                headers={"User-Agent": _CRAWLER_USER_AGENT},
                follow_redirects=False,
                timeout=15,
            ) as response:
                response.raise_for_status()
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > self.max_response_bytes:
                        raise ProductMetadataError("Shopee metadata response is too large")
        except httpx.HTTPError as exc:
            raise ProductMetadataError("Shopee metadata request failed") from exc

        parser = _OpenGraphParser()
        parser.feed(content.decode("utf-8", errors="replace"))
        title = parser.values.get("og:title", "")[:500]
        image_url = parser.values.get("og:image", "")
        if not title or not self._is_allowed_image(image_url):
            raise ProductMetadataError("Shopee product title or image was not found")
        return ProductMetadata(title=title, image_url=image_url)

    @staticmethod
    def _is_allowed_image(image_url: str) -> bool:
        try:
            parsed = urlsplit(image_url)
            port = parsed.port
        except ValueError:
            return False
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        return (
            parsed.scheme == "https"
            and port in (None, 443)
            and not parsed.username
            and not parsed.password
            and any(hostname.endswith(suffix) for suffix in _ALLOWED_IMAGE_SUFFIXES)
        )
