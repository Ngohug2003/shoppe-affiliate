from pydantic import BaseModel, Field


class AffiliateProductImportRequest(BaseModel):
    url: str = Field(min_length=10, max_length=4096)
