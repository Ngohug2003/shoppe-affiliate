from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.responses.affiliate_catalog import (
    AffiliateProductResponse,
    AffiliateShopResponse,
)
from app.services.affiliate_catalog_service import AffiliateCatalogService


class PublicAffiliateCatalogController:
    def __init__(self, service: AffiliateCatalogService) -> None:
        self.service = service

    async def list_affiliate_shops(
        self, session: AsyncSession
    ) -> list[AffiliateShopResponse]:
        shops = await self.service.list_affiliate_shops(session)
        return [AffiliateShopResponse(**shop.__dict__) for shop in shops]

    async def list_affiliate_products_by_shop_id(
        self, session: AsyncSession, shop_id: str
    ) -> list[AffiliateProductResponse]:
        products = await self.service.list_affiliate_products_by_shop_id(
            session, shop_id
        )
        return [AffiliateProductResponse(**product.__dict__) for product in products]
