from urllib.parse import parse_qs, urlsplit

import pytest

from app.core.config import Settings
from app.providers.affiliate import MockAffiliateProvider, ShopeeRedirectAffiliateProvider
from app.providers.affiliate.official_provider import AffiliateProviderError


async def test_mock_affiliate_provider_is_explicitly_non_production() -> None:
    result = await MockAffiliateProvider().generate_deep_link(
        "https://shopee.vn/product/1/2", "telegram", "sender", "message"
    )
    assert result.provider == "mock"
    assert result.affiliate_url.startswith("https://mock.invalid/")


async def test_shopee_redirect_provider_builds_documented_url() -> None:
    provider = ShopeeRedirectAffiliateProvider(
        Settings(AFFILIATE_PUBLISHER_ID="17334630385")
    )
    result = await provider.generate_deep_link(
        "https://shopee.vn/product/123/456?tracking=discarded",
        "telegram",
        "user 20",
        "message/100",
    )

    parsed = urlsplit(result.affiliate_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "s.shopee.vn"
    assert parsed.path == "/an_redir"
    assert parse_qs(parsed.query) == {
        "origin_link": ["https://shopee.vn/product/123/456"],
        "affiliate_id": ["17334630385"],
        "sub_id": ["telegram-user_20-message_100"],
    }
    assert result.provider == "shopee_redirect"


async def test_shopee_redirect_provider_requires_publisher_id() -> None:
    provider = ShopeeRedirectAffiliateProvider(Settings(AFFILIATE_PUBLISHER_ID=""))
    with pytest.raises(AffiliateProviderError, match="not configured"):
        await provider.generate_deep_link("https://shopee.vn/product/123/456")


async def test_shopee_redirect_provider_supports_category_landing() -> None:
    provider = ShopeeRedirectAffiliateProvider(
        Settings(AFFILIATE_PUBLISHER_ID="17334630385")
    )
    result = await provider.generate_deep_link(
        "https://shopee.vn/Fashion-Accessories-cat.11035853?utm_source=old"
    )
    query = parse_qs(urlsplit(result.affiliate_url).query)
    assert query["origin_link"] == [
        "https://shopee.vn/Fashion-Accessories-cat.11035853"
    ]
