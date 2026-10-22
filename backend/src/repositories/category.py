from sqlalchemy import Result, select

from src.models import CategoryModel
from src.utils.repository import SqlAlchemyRepository


class CategoryRepository(SqlAlchemyRepository[CategoryModel]):

    _model = CategoryModel

    async def get_categories_ordered(self) -> list[CategoryModel]:
        """Get all categories ordered by name."""
        query = select(self._model).order_by(self._model.name)
        res: Result = await self._session.execute(query)
        return list(res.scalars().all())
