from pydantic import BaseModel


class NormalizedShopeeUrl(BaseModel):
    original_url: str
    normalized_url: str
    shop_id: str | None = None
    item_id: str | None = None


class ResolvedShopeeUrl(NormalizedShopeeUrl):
    resolved_url: str
