from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.auth import get_current_user
from app.controllers.affiliate_catalog_controller import AffiliateCatalogController
from app.controllers.auth_controller import AuthController
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import User
from app.providers.affiliate import build_affiliate_provider
from app.schemas.affiliate_catalog import (
    AffiliateProductImportRequest,
    AffiliateProductResponse,
    AffiliateShopResponse,
)
from app.services.affiliate_catalog_service import AffiliateCatalogService

router = APIRouter(tags=["affiliate catalog"])
settings = get_settings()
catalog_controller = AffiliateCatalogController(
    AffiliateCatalogService(build_affiliate_provider(settings))
)


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return AuthController.require_admin(current_user)


@router.post(
    "/affiliate-products",
    response_model=AffiliateProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_affiliate_product(
    payload: AffiliateProductImportRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_admin)],
) -> AffiliateProductResponse:
    return await catalog_controller.import_product(session, payload)


@router.get("/affiliate-shops", response_model=list[AffiliateShopResponse])
async def list_affiliate_shops(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AffiliateShopResponse]:
    return await catalog_controller.list_shops(session)


@router.get(
    "/affiliate-shops/{shop_id}/products",
    response_model=list[AffiliateProductResponse],
)
async def list_affiliate_products(
    shop_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AffiliateProductResponse]:
    return await catalog_controller.list_products(session, shop_id)
