from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Page[ItemT]:
    items: list[ItemT]
    page: int
    per_page: int
    total: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.per_page - 1) // self.per_page

    def map[MappedItemT](
        self, mapper: Callable[[ItemT], MappedItemT]
    ) -> Page[MappedItemT]:
        return Page(
            items=[mapper(item) for item in self.items],
            page=self.page,
            per_page=self.per_page,
            total=self.total,
        )
