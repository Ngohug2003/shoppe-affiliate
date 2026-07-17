"""create affiliate_links table

Revision ID: 003
Revises: 002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "affiliate_links",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("affiliate_url", sa.Text(), nullable=False),
        sa.Column("provider_campaign_id", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "raw_response",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_affiliate_links_product_id",
        "affiliate_links",
        ["product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_affiliate_links_product_id", table_name="affiliate_links")
    op.drop_table("affiliate_links")
