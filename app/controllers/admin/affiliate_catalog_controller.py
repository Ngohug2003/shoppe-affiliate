import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.requests.affiliate_catalog import AffiliateProductImportRequest
from app.schemas.responses.affiliate_catalog import AffiliateProductResponse
from app.services.affiliate_catalog_service import AffiliateCatalogService


class AdminAffiliateCatalogController:
    def __init__(self, service: AffiliateCatalogService) -> None:
        self.service = service

    async def import_product(
        self, session: AsyncSession, payload: AffiliateProductImportRequest
    ) -> AffiliateProductResponse:
        async with httpx.AsyncClient() as client:
            product = await self.service.import_product(
                session, payload.url, client=client
            )
        return AffiliateProductResponse.model_validate(product)
