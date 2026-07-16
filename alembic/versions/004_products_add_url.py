"""add original submitted URL to products

Revision ID: 004
Revises: 003
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("url", sa.Text(), nullable=True))
    op.execute(sa.text("UPDATE products SET url = normalized_url WHERE url IS NULL"))
    op.alter_column("products", "url", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    op.drop_column("products", "url")
