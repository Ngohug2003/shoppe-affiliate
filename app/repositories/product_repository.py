from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.pagination import Page
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

    async def list_affiliate_products_by_shop_id(
        self, session: AsyncSession, shop_id: str
    ) -> list[ProductWithAffiliateUrl]:
        return await self._list_affiliate_products(session, shop_id=shop_id)

    async def list_all_affiliate_products(
        self,
        session: AsyncSession,
        *,
        page: int,
        per_page: int,
        title: str | None,
    ) -> Page[ProductWithAffiliateUrl]:
        filters = self._affiliate_product_filters(title=title)
        total = int(
            (
                await session.execute(
                    select(func.count(Product.id)).where(*filters)
                )
            ).scalar_one()
        )
        items = await self._list_affiliate_products(
            session,
            filters=filters,
            offset=(page - 1) * per_page,
            limit=per_page,
        )
        return Page(items=items, page=page, per_page=per_page, total=total)

    @staticmethod
    def _affiliate_product_filters(
        *, title: str | None = None
    ) -> list[ColumnElement[bool]]:
        filters = [
            Product.is_affiliate.is_(True),
            Product.name.is_not(None),
            Product.image_url.is_not(None),
            exists(select(AffiliateLink.id).where(AffiliateLink.product_id == Product.id)),
        ]
        normalized_title = title.strip() if title else None
        if normalized_title:
            filters.append(Product.name.ilike(f"%{normalized_title}%"))
        return filters

    async def _list_affiliate_products(
        self,
        session: AsyncSession,
        *,
        shop_id: str | None = None,
        filters: Sequence[ColumnElement[bool]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[ProductWithAffiliateUrl]:
        latest_affiliate_url = (
            select(AffiliateLink.affiliate_url)
            .where(AffiliateLink.product_id == Product.id)
            .order_by(AffiliateLink.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        query = select(Product, latest_affiliate_url.label("affiliate_url")).where(
            *(
                filters
                if filters is not None
                else self._affiliate_product_filters()
            )
        )
        if shop_id is not None:
            query = query.where(Product.shop_id == shop_id)
        query = query.order_by(Product.created_at.desc())
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        rows = (await session.execute(query)).all()
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
        product_id: int,
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
