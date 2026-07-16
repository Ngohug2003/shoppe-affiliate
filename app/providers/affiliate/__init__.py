from app.providers.affiliate.base import AffiliateProvider, AffiliateResult
from app.providers.affiliate.factory import build_affiliate_provider
from app.providers.affiliate.mock_provider import MockAffiliateProvider
from app.providers.affiliate.official_provider import OfficialAffiliateProvider
from app.providers.affiliate.shopee_redirect_provider import ShopeeRedirectAffiliateProvider

__all__ = [
    "AffiliateProvider",
    "AffiliateResult",
    "build_affiliate_provider",
    "MockAffiliateProvider",
    "OfficialAffiliateProvider",
    "ShopeeRedirectAffiliateProvider",
]
