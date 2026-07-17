from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AffiliateProductsNotFoundError
from app.db.session import get_db_session
from app.main import app
from app.routes import affiliate_catalog
from app.schemas.responses.affiliate_catalog import (
    AffiliateProductResponse,
    AffiliateShopResponse,
    PublicAffiliateProductListResponse,
    PublicAffiliateProductResponse,
)


def test_import_affiliate_product_requires_authentication() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/api/v1/affiliate-products",
            json={"url": "https://shopee.vn/product/123/456"},
        )

    assert response.status_code == 401
    assert response.json() == {
        "status": {"code": 401, "message": "Not authenticated"},
        "data": None,
    }


def test_public_products_returns_clear_error_when_no_data() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_session
    service = affiliate_catalog.public_catalog_controller.service
    original_list_all_affiliate_products = service.list_all_affiliate_products
    service.list_all_affiliate_products = AsyncMock(  # type: ignore[method-assign]
        side_effect=AffiliateProductsNotFoundError(page=1, total=0)
    )
    try:
        with TestClient(app, base_url="http://localhost") as client:
            response = client.get("/api/v1/affiliate-products")
    finally:
        app.dependency_overrides.clear()
        service.list_all_affiliate_products = (  # type: ignore[method-assign]
            original_list_all_affiliate_products
        )

    assert response.status_code == 404
    assert response.json() == {
        "status": {
            "code": 404,
            "message": "Không tìm thấy sản phẩm affiliate phù hợp",
        },
        "data": None,
    }


def test_public_products_returns_structured_validation_error() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.get("/api/v1/affiliate-products?page=0")

    assert response.status_code == 422
    assert response.json()["status"] == {
        "code": 422,
        "message": "Dữ liệu gửi lên không hợp lệ",
    }
    assert response.json()["data"]["details"][0]["field"] == "query.page"


def test_catalog_read_endpoints_group_products_by_shop() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_session
    controller = affiliate_catalog.public_catalog_controller
    original_list_affiliate_shops = controller.list_affiliate_shops
    original_list_all_affiliate_products = controller.list_all_affiliate_products
    original_list_affiliate_products = (
        controller.list_affiliate_products_by_shop_id
    )
    controller.list_affiliate_shops = AsyncMock(  # type: ignore[method-assign]
        return_value=[AffiliateShopResponse(shop_id="123", product_count=1)]
    )
    controller.list_affiliate_products_by_shop_id = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            AffiliateProductResponse(
                shop_id="123",
                item_id="456",
                title="Sản phẩm",
                image_url="https://down-vn.img.susercontent.com/file/image",
                product_url="https://shopee.vn/product/123/456",
                affiliate_url="https://s.shopee.vn/an_redir?affiliate_id=1",
                metadata_source="shopee_open_graph",
            )
        ]
    )
    list_all_affiliate_products_mock = AsyncMock(
        return_value=PublicAffiliateProductListResponse(
            items=[
                PublicAffiliateProductResponse(
                    id=10,
                    title="Sản phẩm",
                    url="https://shopee.vn/product/123/456",
                    image_url="https://down-vn.img.susercontent.com/file/image",
                    affiliate_url="https://s.shopee.vn/an_redir?affiliate_id=1",
                )
            ],
            page=2,
            per_page=5,
            total=6,
            total_pages=2,
        )
    )
    controller.list_all_affiliate_products = (  # type: ignore[method-assign]
        list_all_affiliate_products_mock
    )
    try:
        with TestClient(app, base_url="http://localhost") as client:
            all_products = client.get(
                "/api/v1/affiliate-products?page=2&per_page=5&title=Sản phẩm"
            )
            shops = client.get("/api/v1/affiliate-shops")
            products = client.get("/api/v1/affiliate-shops/123/products")
    finally:
        app.dependency_overrides.clear()
        controller.list_affiliate_shops = original_list_affiliate_shops  # type: ignore[method-assign]
        controller.list_all_affiliate_products = original_list_all_affiliate_products  # type: ignore[method-assign]
        controller.list_affiliate_products_by_shop_id = (  # type: ignore[method-assign]
            original_list_affiliate_products
        )

    assert all_products.json() == {
        "status": {
            "code": 200,
            "message": "Lấy danh sách sản phẩm affiliate thành công",
        },
        "data": {
            "items": [
                {
                    "id": 10,
                    "title": "Sản phẩm",
                    "url": "https://shopee.vn/product/123/456",
                    "image_url": "https://down-vn.img.susercontent.com/file/image",
                    "affiliate_url": "https://s.shopee.vn/an_redir?affiliate_id=1",
                }
            ],
            "page": 2,
            "per_page": 5,
            "total": 6,
            "total_pages": 2,
        },
    }
    list_all_affiliate_products_mock.assert_awaited_once_with(
        session,
        page=2,
        per_page=5,
        title="Sản phẩm",
    )
    assert shops.json() == {
        "status": {
            "code": 200,
            "message": "Lấy danh sách cửa hàng affiliate thành công",
        },
        "data": [{"shop_id": "123", "product_count": 1}],
    }
    assert products.json()["data"][0]["item_id"] == "456"
    assert products.json()["data"][0]["metadata_source"] == "shopee_open_graph"
