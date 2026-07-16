from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AffiliateLink, Product


@dataclass(frozen=True)
class ProductWithAffiliateUrl:
    product: Product
    affiliate_url: str


class ProductRepository:
    async def get_by_shop_item(
        self,
        session: AsyncSession,
        *,
        shop_id: str,
        item_id: str,
    ) -> Product | None:
        result = await session.execute(
            select(Product).where(
                Product.shop_id == shop_id,
                Product.item_id == item_id,
            )
        )
        return result.scalar_one_or_none()

    def add(self, session: AsyncSession, product: Product) -> None:
        session.add(product)

    async def list_affiliate_shop_counts(
        self, session: AsyncSession
    ) -> list[tuple[str, int]]:
        rows = (
            await session.execute(
                select(Product.shop_id, func.count(Product.id))
                .where(Product.is_affiliate.is_(True))
                .group_by(Product.shop_id)
                .order_by(Product.shop_id)
            )
        ).all()
        return [(shop_id, int(product_count)) for shop_id, product_count in rows]

    async def list_affiliate_products(
        self, session: AsyncSession, shop_id: str
    ) -> list[ProductWithAffiliateUrl]:
        latest_affiliate_url = (
            select(AffiliateLink.affiliate_url)
            .where(AffiliateLink.product_id == Product.id)
            .order_by(AffiliateLink.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        rows = (
            await session.execute(
                select(Product, latest_affiliate_url.label("affiliate_url"))
                .where(Product.shop_id == shop_id, Product.is_affiliate.is_(True))
                .order_by(Product.created_at.desc())
            )
        ).all()
        return [
            ProductWithAffiliateUrl(product=product, affiliate_url=str(affiliate_url))
            for product, affiliate_url in rows
            if affiliate_url
        ]


class AffiliateLinkRepository:
    async def get_matching(
        self,
        session: AsyncSession,
        *,
        product_id: UUID,
        provider: str,
        affiliate_url: str,
    ) -> AffiliateLink | None:
        result = await session.execute(
            select(AffiliateLink).where(
                AffiliateLink.product_id == product_id,
                AffiliateLink.provider == provider,
                AffiliateLink.affiliate_url == affiliate_url,
            )
        )
        return result.scalar_one_or_none()

    def add(self, session: AsyncSession, affiliate_link: AffiliateLink) -> None:
        session.add(affiliate_link)
