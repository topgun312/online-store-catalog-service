from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Result, func, select

from src.models import ProductModel
from src.schemas.filter import ProductFilters
from src.utils.repository import SqlAlchemyRepository


class ProductRepository(SqlAlchemyRepository[ProductModel]):

    _model = ProductModel

    async def get_products_by_filters(
        self,
        filters: ProductFilters,
        category_id: UUID | None = None,
    ) -> tuple[Sequence[ProductModel], int]:
        """Get a page of products and the total count."""
        count_query = select(func.count()).select_from(self._model)
        if category_id is not None:
            count_query = count_query.where(self._model.category_id == category_id)
        total: Result = await self._session.execute(count_query)
        total_count: int = total.scalar_one()

        query = select(self._model)
        if category_id is not None:
            query = query.where(self._model.category_id == category_id)
        query = (
            query.order_by(self._model.created_at.desc(), self._model.id)
            .offset(filters.offset)
            .limit(
                filters.limit,
            )
        )

        res: Result = await self._session.execute(query)
        return res.scalars().all(), total_count

    async def get_by_filter_one_or_none(self, **kwargs: Any) -> ProductModel | None:
        """Get a single product matching the filter."""
        query = select(self._model).filter_by(**kwargs).execution_options(populate_existing=True)
        res: Result = await self._session.execute(query)
        return res.unique().scalar_one_or_none()
