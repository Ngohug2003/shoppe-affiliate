import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.schemas.affiliate_catalog import (
    AffiliateProductImportRequest,
    AffiliateProductResponse,
    AffiliateShopResponse,
)
from app.services.affiliate_catalog_service import AffiliateCatalogService
from app.services.product_metadata_service import ProductMetadataError


class AffiliateCatalogController:
    def __init__(self, service: AffiliateCatalogService) -> None:
        self.service = service

    async def import_product(
        self, session: AsyncSession, payload: AffiliateProductImportRequest
    ) -> AffiliateProductResponse:
        try:
            async with httpx.AsyncClient() as client:
                product = await self.service.import_product(
                    session, payload.url, client=client
                )
        except ProductMetadataError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
            ) from exc
        except ApplicationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        return AffiliateProductResponse(**product.__dict__)

    async def list_shops(self, session: AsyncSession) -> list[AffiliateShopResponse]:
        shops = await self.service.list_shops(session)
        return [AffiliateShopResponse(**shop.__dict__) for shop in shops]

    async def list_products(
        self, session: AsyncSession, shop_id: str
    ) -> list[AffiliateProductResponse]:
        products = await self.service.list_products(session, shop_id)
        return [AffiliateProductResponse(**product.__dict__) for product in products]
