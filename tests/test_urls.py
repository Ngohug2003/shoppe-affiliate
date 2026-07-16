from __future__ import annotations

import socket

import httpx
import pytest
import respx

from app.core.exceptions import InvalidShopeeUrlError
from app.services.url_service import ShopeeUrlResolver
from app.utils.urls import (
    ensure_public_host,
    extract_shopee_urls,
    normalize_shopee_landing_url,
    normalize_shopee_url,
)


def test_extract_shopee_urls_deduplicates_and_strips_punctuation() -> None:
    message = (
        "Xem https://s.shopee.vn/abc, và https://shopee.vn/product/123/456. "
        "Link mới https://vn.shp.ee/xAFCUhQT; lặp https://s.shopee.vn/abc"
    )
    assert extract_shopee_urls(message) == [
        "https://s.shopee.vn/abc",
        "https://shopee.vn/product/123/456",
        "https://vn.shp.ee/xAFCUhQT",
    ]


@pytest.mark.parametrize(
    ("url", "shop_id", "item_id"),
    [
        ("https://shopee.vn/product/123/456", "123", "456"),
        ("https://shopee.vn/opaanlp/123/456?credential_token=secret", "123", "456"),
        ("https://www.shopee.vn/san-pham-i.987.654?x=1", "987", "654"),
    ],
)
def test_normalize_shopee_url(url: str, shop_id: str, item_id: str) -> None:
    result = normalize_shopee_url(url)
    assert result.shop_id == shop_id
    assert result.item_id == item_id
    assert result.normalized_url == f"https://shopee.vn/product/{shop_id}/{item_id}"


def test_normalize_landing_url_removes_existing_affiliate_tracking() -> None:
    result = normalize_shopee_landing_url(
        "https://shopee.vn/Fashion-Accessories-cat.11035853"
        "?mmp_pid=an_old&utm_source=an_old&sortBy=pop#fragment"
    )
    assert result.normalized_url == (
        "https://shopee.vn/Fashion-Accessories-cat.11035853?sortBy=pop"
    )
    assert result.shop_id is None
    assert result.item_id is None


@pytest.mark.parametrize(
    "url",
    [
        "http://shopee.vn/product/1/2",
        "https://evil.example/product/1/2",
        "https://shopee.vn.evil.example/product/1/2",
        "https://user@shopee.vn/product/1/2",
        "https://shopee.vn:8443/product/1/2",
    ],
)
def test_normalize_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(InvalidShopeeUrlError):
        normalize_shopee_url(url)


async def test_public_host_rejects_localhost_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loop = __import__("asyncio").get_running_loop()

    async def private_getaddrinfo(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]

    monkeypatch.setattr(loop, "getaddrinfo", private_getaddrinfo)
    with pytest.raises(InvalidShopeeUrlError, match="forbidden IP"):
        await ensure_public_host("s.shopee.vn")


@respx.mock
async def test_resolve_short_url_checks_redirect_and_normalizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr("app.services.url_service.ensure_public_host", allow_public_host)
    respx.get("https://s.shopee.vn/abc").mock(
        return_value=httpx.Response(
            302, headers={"location": "https://shopee.vn/product/123/456"}
        )
    )
    result = await ShopeeUrlResolver().resolve("https://s.shopee.vn/abc")
    assert result.shop_id == "123"
    assert result.item_id == "456"


@respx.mock
async def test_resolve_vn_short_url_checks_redirect_and_normalizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr("app.services.url_service.ensure_public_host", allow_public_host)
    respx.get("https://vn.shp.ee/xAFCUhQT").mock(
        return_value=httpx.Response(
            302, headers={"location": "https://shopee.vn/product/1052042348/40551700226"}
        )
    )

    result = await ShopeeUrlResolver().resolve("https://vn.shp.ee/xAFCUhQT")
    assert result.shop_id == "1052042348"
    assert result.item_id == "40551700226"


@respx.mock
async def test_resolve_short_url_with_opaanlp_product_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr("app.services.url_service.ensure_public_host", allow_public_host)
    respx.get("https://s.shopee.vn/6L2tat0caA").mock(
        return_value=httpx.Response(
            301,
            headers={
                "location": (
                    "https://shopee.vn/opaanlp/1053911170/19985684219"
                    "?credential_token=secret&utm_source=other"
                )
            },
        )
    )

    result = await ShopeeUrlResolver().resolve("https://s.shopee.vn/6L2tat0caA")
    assert result.normalized_url == (
        "https://shopee.vn/product/1053911170/19985684219"
    )
    assert result.shop_id == "1053911170"
    assert result.item_id == "19985684219"


@respx.mock
async def test_resolve_short_url_accepts_category_landing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr("app.services.url_service.ensure_public_host", allow_public_host)
    respx.get("https://s.shopee.vn/category").mock(
        return_value=httpx.Response(
            301,
            headers={
                "location": (
                    "https://shopee.vn/Fashion-Accessories-cat.11035853"
                    "?mmp_pid=an_old&utm_source=an_old"
                )
            },
        )
    )

    result = await ShopeeUrlResolver().resolve("https://s.shopee.vn/category")
    assert result.normalized_url == "https://shopee.vn/Fashion-Accessories-cat.11035853"
    assert result.shop_id is None


@respx.mock
async def test_resolver_blocks_redirect_outside_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def allow_public_host(_: str) -> None:
        return None

    monkeypatch.setattr("app.services.url_service.ensure_public_host", allow_public_host)
    respx.get("https://s.shopee.vn/abc").mock(
        return_value=httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})
    )
    with pytest.raises(InvalidShopeeUrlError):
        await ShopeeUrlResolver().resolve("https://s.shopee.vn/abc")
