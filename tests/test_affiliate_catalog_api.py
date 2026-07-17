from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.main import app
from app.routes import affiliate_catalog
from app.schemas.responses.affiliate_catalog import (
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
    controller = affiliate_catalog.public_catalog_controller
    original_list_affiliate_shops = controller.list_affiliate_shops
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
    try:
        with TestClient(app, base_url="http://localhost") as client:
            shops = client.get("/api/v1/affiliate-shops")
            products = client.get("/api/v1/affiliate-shops/123/products")
    finally:
        app.dependency_overrides.clear()
        controller.list_affiliate_shops = original_list_affiliate_shops  # type: ignore[method-assign]
        controller.list_affiliate_products_by_shop_id = (  # type: ignore[method-assign]
            original_list_affiliate_products
        )

    assert shops.json() == [{"shop_id": "123", "product_count": 1}]
    assert products.json()[0]["item_id"] == "456"
    assert products.json()[0]["metadata_source"] == "shopee_open_graph"
