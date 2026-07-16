"""create products table

Revision ID: 002
Revises: 001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("shop_id", sa.String(length=64), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("price", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="VND", nullable=False),
        sa.Column("is_affiliate", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "extra_data",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "item_id"),
    )
    op.create_index("ix_products_is_affiliate", "products", ["is_affiliate"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_products_is_affiliate", table_name="products")
    op.drop_table("products")
