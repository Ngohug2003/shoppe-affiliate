from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.providers.affiliate.base import AffiliateProvider, AffiliateResult
from app.repositories.product_repository import (
    AffiliateLinkRepository,
    ProductRepository,
)
from app.schemas.urls import ResolvedShopeeUrl
from app.services.affiliate_catalog_service import AffiliateCatalogService
from app.services.product_metadata_service import (
    ProductMetadata,
    ShopeeOpenGraphMetadataProvider,
)
from app.services.url_service import ShopeeUrlResolver


async def test_import_new_product_initializes_extra_data() -> None:
    session = AsyncMock(spec=AsyncSession)
    product_repository = AsyncMock(spec=ProductRepository)
    product_repository.get_by_shop_item.return_value = None
    affiliate_link_repository = AsyncMock(spec=AffiliateLinkRepository)
    affiliate_link_repository.get_matching.return_value = None

    def assign_product_id(_: AsyncSession, product: Product) -> None:
        product.id = uuid4()

    product_repository.add.side_effect = assign_product_id

    resolver = AsyncMock(spec=ShopeeUrlResolver)
    resolver.resolve.return_value = ResolvedShopeeUrl(
        original_url="https://vn.shp.ee/M8m7R4xS",
        resolved_url="https://shopee.vn/product/123/456",
        normalized_url="https://shopee.vn/product/123/456",
        shop_id="123",
        item_id="456",
    )
    metadata_provider = AsyncMock(spec=ShopeeOpenGraphMetadataProvider)
    metadata_provider.fetch.return_value = ProductMetadata(
        title="Sản phẩm thử nghiệm",
        image_url="https://down-vn.img.susercontent.com/file/image",
    )
    affiliate_provider = AsyncMock(spec=AffiliateProvider)
    affiliate_provider.generate_deep_link.return_value = AffiliateResult(
        affiliate_url="https://s.shopee.vn/an_redir?affiliate_id=1",
        provider="shopee_redirect",
    )
    service = AffiliateCatalogService(
        affiliate_provider,
        resolver=resolver,
        metadata_provider=metadata_provider,
        product_repository=product_repository,
        affiliate_link_repository=affiliate_link_repository,
    )

    async with httpx.AsyncClient() as client:
        result = await service.import_product(
            session,
            "https://vn.shp.ee/M8m7R4xS",
            client=client,
        )

    product = product_repository.add.call_args.args[1]
    assert isinstance(product, Product)
    assert product.url == "https://vn.shp.ee/M8m7R4xS"
    assert product.extra_data["metadata_source"] == "shopee_open_graph"
    assert result.item_id == "456"
    session.commit.assert_awaited_once()
