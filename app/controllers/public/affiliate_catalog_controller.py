from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.responses.affiliate_catalog import (
    AffiliateProductResponse,
    AffiliateShopResponse,
    PublicAffiliateProductListResponse,
    PublicAffiliateProductResponse,
)
from app.services.affiliate_catalog_service import AffiliateCatalogService


class PublicAffiliateCatalogController:
    def __init__(self, service: AffiliateCatalogService) -> None:
        self.service = service

    async def list_affiliate_shops(
        self, session: AsyncSession
    ) -> list[AffiliateShopResponse]:
        shops = await self.service.list_affiliate_shops(session)
        return [AffiliateShopResponse.model_validate(shop) for shop in shops]

    async def list_affiliate_products_by_shop_id(
        self, session: AsyncSession, shop_id: str
    ) -> list[AffiliateProductResponse]:
        products = await self.service.list_affiliate_products_by_shop_id(
            session, shop_id
        )
        return [AffiliateProductResponse.model_validate(product) for product in products]

    async def list_all_affiliate_products(
        self,
        session: AsyncSession,
        *,
        page: int,
        per_page: int,
        title: str | None,
    ) -> PublicAffiliateProductListResponse:
        products = await self.service.list_all_affiliate_products(
            session,
            page=page,
            per_page=per_page,
            title=title,
        )
        items = [
            PublicAffiliateProductResponse.model_validate(product)
            for product in products.items
        ]
        return PublicAffiliateProductListResponse.from_page(
            products,
            items,
        )
