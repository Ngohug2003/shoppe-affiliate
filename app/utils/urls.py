from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core.exceptions import InvalidShopeeUrlError
from app.schemas.urls import NormalizedShopeeUrl

SHORT_SHOPEE_HOSTS = frozenset({"s.shopee.vn", "vn.shp.ee"})
ALLOWED_SHOPEE_HOSTS = frozenset(
    {"shopee.vn", "www.shopee.vn", *SHORT_SHOPEE_HOSTS}
)
_URL_PATTERN = re.compile(
    r"https://(?:vn\.shp\.ee|s\.shopee\.vn|(?:www\.)?shopee\.vn)/[^\s<>\"']+",
    flags=re.IGNORECASE,
)
_PRODUCT_PATH_PATTERN = re.compile(r"^/product/(\d+)/(\d+)/?$")
_OPAANLP_PATH_PATTERN = re.compile(r"^/opaanlp/(\d+)/(\d+)/?$")
_ITEM_MARKER_PATTERN = re.compile(r"(?:^|[-/])i\.(\d+)\.(\d+)(?:$|[/?])")
_TRAILING_PUNCTUATION = ".,;:!?)]}"
_TRACKING_QUERY_KEYS = frozenset({"mmp_pid", "uls_trackid"})


def extract_shopee_urls(message: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in _URL_PATTERN.finditer(message):
        url = match.group(0).rstrip(_TRAILING_PUNCTUATION)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def validate_shopee_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise InvalidShopeeUrlError("Malformed Shopee URL") from exc

    hostname = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.scheme.lower() != "https":
        raise InvalidShopeeUrlError("Shopee URL must use HTTPS")
    if hostname not in ALLOWED_SHOPEE_HOSTS:
        raise InvalidShopeeUrlError("Shopee URL hostname is not allowed")
    if parsed.username or parsed.password:
        raise InvalidShopeeUrlError("Credentials are not allowed in Shopee URLs")
    if port not in (None, 443):
        raise InvalidShopeeUrlError("Custom ports are not allowed in Shopee URLs")
    return hostname


def _is_forbidden_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )


async def ensure_public_host(hostname: str) -> None:
    loop = asyncio.get_running_loop()
    try:
        records = await loop.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise InvalidShopeeUrlError("Shopee hostname could not be resolved") from exc
    addresses = {record[4][0] for record in records}
    if not addresses or any(_is_forbidden_ip(address) for address in addresses):
        raise InvalidShopeeUrlError("Shopee hostname resolved to a forbidden IP address")


def normalize_shopee_url(url: str) -> NormalizedShopeeUrl:
    validate_shopee_url(url)
    parsed = urlsplit(url)
    path_match = _PRODUCT_PATH_PATTERN.match(parsed.path)
    opaanlp_match = _OPAANLP_PATH_PATTERN.match(parsed.path)
    marker_match = _ITEM_MARKER_PATTERN.search(parsed.path)
    match = path_match or opaanlp_match or marker_match
    if match is None:
        raise InvalidShopeeUrlError("Shopee product identifiers were not found")
    shop_id, item_id = match.groups()
    return NormalizedShopeeUrl(
        original_url=url,
        normalized_url=f"https://shopee.vn/product/{shop_id}/{item_id}",
        shop_id=shop_id,
        item_id=item_id,
    )


def normalize_shopee_landing_url(url: str) -> NormalizedShopeeUrl:
    """Normalize any documented Shopee landing page and remove old tracking."""
    validate_shopee_url(url)
    try:
        return normalize_shopee_url(url)
    except InvalidShopeeUrlError:
        parsed = urlsplit(url)
        clean_query = urlencode(
            [
                (key, value)
                for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                if key.lower() not in _TRACKING_QUERY_KEYS
                and not key.lower().startswith("utm_")
            ]
        )
        normalized_url = urlunsplit(
            ("https", parsed.hostname or "shopee.vn", parsed.path or "/", clean_query, "")
        )
        return NormalizedShopeeUrl(original_url=url, normalized_url=normalized_url)
