from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, Never, TypeVar
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import BaseModel

if TYPE_CHECKING:
    from sqlalchemy.engine import Result


class AbstractRepository(ABC):
    """Repository interface for generic persistence operations."""

    @abstractmethod
    async def add_one(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def add_one_and_get_id(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def add_one_and_get_obj(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def bulk_add(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def get_by_filter_one_or_none(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def get_by_filter_all(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def update_one_by_id(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_filter(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_ids(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self, *args: Any, **kwargs: Any) -> Never:
        raise NotImplementedError


M = TypeVar('M', bound=BaseModel)


class SqlAlchemyRepository(AbstractRepository, Generic[M]):
    """Generic SQLAlchemy repository implementation."""

    _model: type[M]

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a session."""
        self._session = session

    async def add_one(self, **kwargs: Any) -> None:
        """Insert a single row."""
        query = insert(self._model).values(**kwargs)
        await self._session.execute(query)

    async def add_one_and_get_id(self, **kwargs: Any) -> int | str | UUID:
        """Insert a row and return its ID."""
        query = insert(self._model).values(**kwargs).returning(self._model.id)
        obj_id: Result = await self._session.execute(query)
        return obj_id.scalar_one()

    async def add_one_and_get_obj(self, **kwargs: Any) -> M:
        """Insert a row and return the persisted object."""
        query = insert(self._model).values(**kwargs).returning(self._model)
        obj: Result = await self._session.execute(query)
        return obj.scalar_one()

    async def bulk_add(self, values: Sequence[dict[str, Any]]) -> None:
        """Insert many rows."""
        query = insert(self._model).values(values)
        await self._session.execute(query)

    async def get_by_filter_one_or_none(self, **kwargs: Any) -> M | None:
        """Get a single row matching the filter."""
        query = select(self._model).filter_by(**kwargs)
        res: Result = await self._session.execute(query)
        return res.unique().scalar_one_or_none()

    async def get_by_filter_all(self, **kwargs: Any) -> Sequence[M]:
        """Get all rows matching the filter."""
        query = select(self._model).filter_by(**kwargs)
        res: Result = await self._session.execute(query)
        return res.scalars().all()

    async def update_one_by_id(self, obj_id: int | str | UUID, **kwargs: Any) -> M | None:
        """Update a row by ID and return it."""
        query = update(self._model).filter(self._model.id == obj_id).values(**kwargs).returning(self._model)
        obj: Result | None = await self._session.execute(query)
        return obj.scalar_one_or_none()

    async def delete_by_filter(self, **kwargs: Any) -> None:
        """Delete rows matching the filter."""
        query = delete(self._model).filter_by(**kwargs)
        await self._session.execute(query)

    async def delete_by_ids(self, *args: int | str | UUID) -> None:
        """Delete rows by IDs."""
        query = delete(self._model).filter(self._model.id.in_(args))
        await self._session.execute(query)

    async def delete_all(self) -> None:
        """Delete all rows."""
        query = delete(self._model)
        await self._session.execute(query)
