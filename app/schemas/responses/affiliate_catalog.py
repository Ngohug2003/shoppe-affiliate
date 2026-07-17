from pydantic import Field

from app.schemas.base import ApiResponseSchema
from app.schemas.responses.pagination import PaginatedResponse


class AffiliateProductResponse(ApiResponseSchema):
    shop_id: str
    item_id: str
    title: str
    image_url: str
    product_url: str
    affiliate_url: str
    metadata_source: str


class AffiliateShopResponse(ApiResponseSchema):
    shop_id: str
    product_count: int


class PublicAffiliateProductResponse(ApiResponseSchema):
    id: int
    title: str
    url: str = Field(validation_alias="product_url")
    image_url: str
    affiliate_url: str


class PublicAffiliateProductListResponse(
    PaginatedResponse[PublicAffiliateProductResponse]
):
    pass
