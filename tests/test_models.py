from app.db.base import Base
from app.models import Product


def test_registers_catalog_tables() -> None:
    expected = {"users", "products", "affiliate_links"}
    assert expected == set(Base.metadata.tables)


def test_product_supports_affiliate_catalog_metadata() -> None:
    assert "url" in Product.__table__.columns
    assert "image_url" in Product.__table__.columns
    assert "is_affiliate" in Product.__table__.columns
