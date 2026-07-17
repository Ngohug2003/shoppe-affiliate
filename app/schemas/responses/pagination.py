from typing import Protocol, Self

from app.schemas.base import ApiResponseSchema


class PaginationSource(Protocol):
    @property
    def page(self) -> int: ...

    @property
    def per_page(self) -> int: ...

    @property
    def total(self) -> int: ...

    @property
    def total_pages(self) -> int: ...


class PaginatedResponse[ResponseT](ApiResponseSchema):
    items: list[ResponseT]
    page: int
    per_page: int
    total: int
    total_pages: int

    @classmethod
    def from_page(cls, page: PaginationSource, items: list[ResponseT]) -> Self:
        return cls(
            items=items,
            page=page.page,
            per_page=page.per_page,
            total=page.total,
            total_pages=page.total_pages,
        )
