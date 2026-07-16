from app.core.config import Settings
from app.providers.affiliate.base import AffiliateProvider
from app.providers.affiliate.mock_provider import MockAffiliateProvider
from app.providers.affiliate.official_provider import OfficialAffiliateProvider
from app.providers.affiliate.shopee_redirect_provider import ShopeeRedirectAffiliateProvider


def build_affiliate_provider(settings: Settings) -> AffiliateProvider:
    if settings.AFFILIATE_PROVIDER == "shopee_redirect":
        return ShopeeRedirectAffiliateProvider(settings)
    if settings.AFFILIATE_PROVIDER == "official":
        return OfficialAffiliateProvider(settings)
    return MockAffiliateProvider()
