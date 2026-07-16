from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes import affiliate_catalog
from app.db.session import get_db_session
from app.main import app
from app.schemas.affiliate_catalog import (
    AffiliateProductResponse,
    AffiliateShopResponse,
)


def test_import_affiliate_product_requires_authentication() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/api/v1/affiliate-products",
            json={"url": "https://shopee.vn/product/123/456"},
        )

    assert response.status_code == 401


def test_catalog_read_endpoints_group_products_by_shop() -> None:
    session = AsyncMock(spec=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_session
    original_list_shops = affiliate_catalog.catalog_controller.list_shops
    original_list_products = affiliate_catalog.catalog_controller.list_products
    affiliate_catalog.catalog_controller.list_shops = AsyncMock(  # type: ignore[method-assign]
        return_value=[AffiliateShopResponse(shop_id="123", product_count=1)]
    )
    affiliate_catalog.catalog_controller.list_products = AsyncMock(  # type: ignore[method-assign]
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
    try:
        with TestClient(app, base_url="http://localhost") as client:
            shops = client.get("/api/v1/affiliate-shops")
            products = client.get("/api/v1/affiliate-shops/123/products")
    finally:
        app.dependency_overrides.clear()
        affiliate_catalog.catalog_controller.list_shops = original_list_shops  # type: ignore[method-assign]
        affiliate_catalog.catalog_controller.list_products = original_list_products  # type: ignore[method-assign]

    assert shops.json() == [{"shop_id": "123", "product_count": 1}]
    assert products.json()[0]["item_id"] == "456"
    assert products.json()[0]["metadata_source"] == "shopee_open_graph"
