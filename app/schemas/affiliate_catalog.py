from pydantic import BaseModel, Field


class AffiliateProductImportRequest(BaseModel):
    url: str = Field(min_length=10, max_length=4096)


class AffiliateProductResponse(BaseModel):
    shop_id: str
    item_id: str
    title: str
    image_url: str
    product_url: str
    affiliate_url: str
    metadata_source: str


class AffiliateShopResponse(BaseModel):
    shop_id: str
    product_count: int
