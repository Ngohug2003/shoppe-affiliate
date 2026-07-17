from typing import Annotated, Any

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
from app.schemas.base import ApiResponse, success_response
from app.schemas.requests.affiliate_catalog import (
    AffiliateProductImportRequest,
    AffiliateProductListRequest,
)
from app.schemas.responses.affiliate_catalog import (
    AffiliateProductResponse,
    AffiliateShopResponse,
    PublicAffiliateProductListResponse,
)
from app.schemas.responses.error import ErrorResponse
from app.services.affiliate_catalog_service import AffiliateCatalogService

router = APIRouter()
settings = get_settings()
catalog_service = AffiliateCatalogService(build_affiliate_provider(settings))
admin_catalog_controller = AdminAffiliateCatalogController(catalog_service)
public_catalog_controller = PublicAffiliateCatalogController(catalog_service)
NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: {
        "model": ErrorResponse,
        "description": "Không tìm thấy dữ liệu affiliate",
    }
}


@router.post(
    "/affiliate-products",
    response_model=ApiResponse[AffiliateProductResponse],
    status_code=status.HTTP_201_CREATED,
    tags=[ADMIN_AFFILIATE_TAG],
)
async def import_affiliate_product(
    payload: AffiliateProductImportRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_admin)],
) -> ApiResponse[AffiliateProductResponse]:
    product = await admin_catalog_controller.import_product(session, payload)
    return success_response(product, code=status.HTTP_201_CREATED)


@router.get(
    "/affiliate-products",
    response_model=ApiResponse[PublicAffiliateProductListResponse],
    responses=NOT_FOUND_RESPONSE,
    tags=[PUBLIC_AFFILIATE_TAG],
)
async def list_all_affiliate_products(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[AffiliateProductListRequest, Depends()],
) -> ApiResponse[PublicAffiliateProductListResponse]:
    products = await public_catalog_controller.list_all_affiliate_products(
        session,
        page=query.page,
        per_page=query.per_page,
        title=query.title,
    )
    return success_response(products)


@router.get(
    "/affiliate-shops",
    response_model=ApiResponse[list[AffiliateShopResponse]],
    responses=NOT_FOUND_RESPONSE,
    tags=[PUBLIC_AFFILIATE_TAG],
)
async def list_affiliate_shops(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AffiliateShopResponse]]:
    shops = await public_catalog_controller.list_affiliate_shops(session)
    return success_response(shops)


@router.get(
    "/affiliate-shops/{shop_id}/products",
    response_model=ApiResponse[list[AffiliateProductResponse]],
    responses=NOT_FOUND_RESPONSE,
    tags=[PUBLIC_AFFILIATE_TAG],
)
async def list_affiliate_products_by_shop_id(
    shop_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AffiliateProductResponse]]:
    products = await public_catalog_controller.list_affiliate_products_by_shop_id(
        session, shop_id
    )
    return success_response(products)
