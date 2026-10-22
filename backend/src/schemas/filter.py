from dataclasses import dataclass
from typing import Annotated

from fastapi import Query


@dataclass
class BaseFilter:
    page: Annotated[int, Query(ge=1)] = 1
    per_page: Annotated[int, Query(ge=1, le=100, description='Page size (max 100)')] = 100

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


@dataclass
class TypeFilter(BaseFilter):
    like: str = Query(default='')


@dataclass
class ProductFilters(BaseFilter):
    category: Annotated[str | None, Query(description='Category slug or id')] = None
