from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True, autoincrement=True
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str] = mapped_column(String(64))
    affiliate_url: Mapped[str] = mapped_column(Text)
    provider_campaign_id: Mapped[str | None] = mapped_column(String(255))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_response: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
