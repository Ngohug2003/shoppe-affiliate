from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.tags import ADMIN_AFFILIATE_TAG, PUBLIC_AFFILIATE_TAG
from app.controllers.admin.affiliate_catalog_controller import (
    AdminAffiliateCatalogController,
)
from app.controllers.public.affiliate_catalog_controller import (
    PublicAffiliateCatalogController,
)
from app.core.config import get_settings
from app.db.session import get_db_session
from app.middlewares.auth import require_admin
from app.models import User
from app.providers.affiliate import build_affiliate_provider
from app.schemas.requests.affiliate_catalog import AffiliateProductImportRequest
from app.schemas.responses.affiliate_catalog import (
    AffiliateProductResponse,
    AffiliateShopResponse,
)
from app.services.affiliate_catalog_service import AffiliateCatalogService

router = APIRouter()
settings = get_settings()
catalog_service = AffiliateCatalogService(build_affiliate_provider(settings))
admin_catalog_controller = AdminAffiliateCatalogController(catalog_service)
public_catalog_controller = PublicAffiliateCatalogController(catalog_service)


@router.post(
    "/affiliate-products",
    response_model=AffiliateProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=[ADMIN_AFFILIATE_TAG],
)
async def import_affiliate_product(
    payload: AffiliateProductImportRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_admin)],
) -> AffiliateProductResponse:
    return await admin_catalog_controller.import_product(session, payload)


@router.get(
    "/affiliate-shops",
    response_model=list[AffiliateShopResponse],
    tags=[PUBLIC_AFFILIATE_TAG],
)
async def list_affiliate_shops(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AffiliateShopResponse]:
    return await public_catalog_controller.list_affiliate_shops(session)


@router.get(
    "/affiliate-shops/{shop_id}/products",
    response_model=list[AffiliateProductResponse],
    tags=[PUBLIC_AFFILIATE_TAG],
)
async def list_affiliate_products_by_shop_id(
    shop_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AffiliateProductResponse]:
    return await public_catalog_controller.list_affiliate_products_by_shop_id(
        session, shop_id
    )
