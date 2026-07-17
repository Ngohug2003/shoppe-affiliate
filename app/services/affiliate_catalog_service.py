from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AffiliateProductsNotFoundError,
    AffiliateShopProductsNotFoundError,
    AffiliateShopsNotFoundError,
    ShopeeProductUrlRequiredError,
)
from app.core.pagination import Page
from app.models import AffiliateLink, Product
from app.providers.affiliate.base import AffiliateProvider
from app.repositories.product_repository import (
    AffiliateLinkRepository,
    ProductRepository,
    ProductWithAffiliateUrl,
)
from app.services.product_metadata_service import ShopeeOpenGraphMetadataProvider
from app.services.url_service import ShopeeUrlResolver


@dataclass(frozen=True)
class AffiliateCatalogProduct:
    id: int
    shop_id: str
    item_id: str
    title: str
    image_url: str
    product_url: str
    affiliate_url: str
    metadata_source: str


@dataclass(frozen=True)
class AffiliateShopSummary:
    shop_id: str
    product_count: int


class AffiliateCatalogService:
    def __init__(
        self,
        affiliate_provider: AffiliateProvider,
        *,
        resolver: ShopeeUrlResolver | None = None,
        metadata_provider: ShopeeOpenGraphMetadataProvider | None = None,
        product_repository: ProductRepository | None = None,
        affiliate_link_repository: AffiliateLinkRepository | None = None,
    ) -> None:
        self.affiliate_provider = affiliate_provider
        self.resolver = resolver or ShopeeUrlResolver()
        self.metadata_provider = metadata_provider or ShopeeOpenGraphMetadataProvider()
        self.product_repository = product_repository or ProductRepository()
        self.affiliate_link_repository = (
            affiliate_link_repository or AffiliateLinkRepository()
        )

    async def import_product(
        self,
        session: AsyncSession,
        product_url: str,
        *,
        client: httpx.AsyncClient,
    ) -> AffiliateCatalogProduct:
        resolved = await self.resolver.resolve(product_url, client=client)
        if resolved.shop_id is None or resolved.item_id is None:
            raise ShopeeProductUrlRequiredError
        metadata = await self.metadata_provider.fetch(
            resolved.normalized_url, client=client
        )
        affiliate = await self.affiliate_provider.generate_deep_link(
            resolved.normalized_url, "catalog", resolved.shop_id, resolved.item_id
        )

        product = await self.product_repository.get_by_shop_item(
            session,
            shop_id=resolved.shop_id,
            item_id=resolved.item_id,
        )
        if product is None:
            product = Product(
                shop_id=resolved.shop_id,
                item_id=resolved.item_id,
                url=product_url,
                normalized_url=resolved.normalized_url,
            )
            self.product_repository.add(session, product)
        product.url = product_url
        product.normalized_url = resolved.normalized_url
        product.name = metadata.title
        product.image_url = metadata.image_url
        product.is_affiliate = True
        product.extra_data = {
            **(product.extra_data or {}),
            "metadata_source": metadata.source,
            "metadata_fetched_at": datetime.now(UTC).isoformat(),
        }
        await session.flush()

        existing_link = await self.affiliate_link_repository.get_matching(
            session,
            product_id=product.id,
            provider=affiliate.provider,
            affiliate_url=affiliate.affiliate_url,
        )
        if existing_link is None:
            self.affiliate_link_repository.add(
                session,
                AffiliateLink(
                    product_id=product.id,
                    provider=affiliate.provider,
                    affiliate_url=affiliate.affiliate_url,
                    provider_campaign_id=affiliate.campaign_id,
                    expires_at=affiliate.expires_at,
                    raw_response=affiliate.raw_response,
                )
            )
        await session.commit()
        return AffiliateCatalogProduct(
            id=product.id,
            shop_id=product.shop_id,
            item_id=product.item_id,
            title=metadata.title,
            image_url=metadata.image_url,
            product_url=product.normalized_url,
            affiliate_url=affiliate.affiliate_url,
            metadata_source=metadata.source,
        )

    async def list_affiliate_shops(
        self, session: AsyncSession
    ) -> list[AffiliateShopSummary]:
        rows = await self.product_repository.list_affiliate_shop_counts(session)
        if not rows:
            raise AffiliateShopsNotFoundError
        return [
            AffiliateShopSummary(shop_id=shop_id, product_count=product_count)
            for shop_id, product_count in rows
        ]

    async def list_affiliate_products_by_shop_id(
        self, session: AsyncSession, shop_id: str
    ) -> list[AffiliateCatalogProduct]:
        rows = await self.product_repository.list_affiliate_products_by_shop_id(
            session, shop_id
        )
        if not rows:
            raise AffiliateShopProductsNotFoundError(shop_id)
        return self._build_affiliate_products(rows)

    async def list_all_affiliate_products(
        self,
        session: AsyncSession,
        *,
        page: int,
        per_page: int,
        title: str | None,
    ) -> Page[AffiliateCatalogProduct]:
        rows = await self.product_repository.list_all_affiliate_products(
            session,
            page=page,
            per_page=per_page,
            title=title,
        )
        if not rows.items:
            raise AffiliateProductsNotFoundError(page=page, total=rows.total)
        return rows.map(self._build_affiliate_product)

    @staticmethod
    def _build_affiliate_products(
        rows: list[ProductWithAffiliateUrl],
    ) -> list[AffiliateCatalogProduct]:
        return [
            AffiliateCatalogService._build_affiliate_product(row) for row in rows
        ]

    @staticmethod
    def _build_affiliate_product(
        row: ProductWithAffiliateUrl,
    ) -> AffiliateCatalogProduct:
        product = row.product
        source = (product.extra_data or {}).get("metadata_source", "unknown")
        return AffiliateCatalogProduct(
            id=product.id,
            shop_id=product.shop_id,
            item_id=product.item_id,
            title=cast(str, product.name),
            image_url=cast(str, product.image_url),
            product_url=product.normalized_url,
            affiliate_url=row.affiliate_url,
            metadata_source=str(source),
        )
