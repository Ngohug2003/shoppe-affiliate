from pydantic import BaseModel, Field

from app.schemas.requests.pagination import PaginationRequest


class AffiliateProductImportRequest(BaseModel):
    url: str = Field(min_length=10, max_length=4096)


class AffiliateProductListRequest(PaginationRequest):
    title: str | None = Field(default=None, max_length=500)
