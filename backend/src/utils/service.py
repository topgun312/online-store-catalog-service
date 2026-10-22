import functools
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Never, TypeVar, overload
from uuid import UUID

from fastapi import Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from src.utils.repository import AbstractRepository
from src.utils.unit_of_work import AbstractUnitOfWork, UnitOfWork

T = TypeVar('T', bound=Callable[..., Awaitable[Any]])


@overload
def transaction_mode(_func: T) -> T: ...


@overload
def transaction_mode(*, auto_flush: bool) -> Callable[[T], T]: ...


def transaction_mode(_func: T | None = None, *, auto_flush: bool = False) -> T | Callable[[T], T]:
    """Run a service method inside a unit-of-work transaction."""

    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def wrapper(self: AbstractService, *args: Any, **kwargs: Any) -> Any:
            if self.uow.is_open:
                res = await func(self, *args, **kwargs)
                if auto_flush:
                    await self.uow.flush()
                return res
            async with self.uow:
                return await func(self, *args, **kwargs)

        return wrapper

    if _func is None:
        return decorator
    return decorator(_func)


class AbstractService(ABC):
    uow: AbstractUnitOfWork

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


class BaseService(AbstractService):
    """Base service resolving its repository from the unit of work."""

    _repo: str | None = None

    def __init__(self, uow: UnitOfWork = Depends()) -> None:
        """Bind the service to a unit of work."""
        self.uow: UnitOfWork = uow
        if not hasattr(self, '_repo') or self._repo is None:
            err_msg = f"Attribute '_repo' is required for class {self.__class__.__name__}"
            raise AttributeError(err_msg)

    @transaction_mode
    async def add_one(self, **kwargs: Any) -> None:
        """Insert a single row."""
        await self._get_related_repo().add_one(**kwargs)

    @transaction_mode
    async def add_one_and_get_id(self, **kwargs: Any) -> int | str | UUID:
        """Insert a row and return its ID."""
        return await self._get_related_repo().add_one_and_get_id(**kwargs)

    @transaction_mode
    async def add_one_and_get_obj(self, **kwargs: Any) -> Any:
        """Insert a row and return the persisted object."""
        return await self._get_related_repo().add_one_and_get_obj(**kwargs)

    @transaction_mode
    async def bulk_add(self, values: Sequence[dict[str, Any]]) -> None:
        """Insert many rows."""
        await self._get_related_repo().bulk_add(values=values)

    @transaction_mode
    async def get_by_filter_one_or_none(self, **kwargs: Any) -> Any:
        """Get a single row matching the filter."""
        return await self._get_related_repo().get_by_filter_one_or_none(**kwargs)

    @transaction_mode
    async def get_by_filter_all(self, **kwargs: Any) -> Sequence[Any]:
        """Get all rows matching the filter."""
        return await self._get_related_repo().get_by_filter_all(**kwargs)

    @transaction_mode
    async def update_one_by_id(self, obj_id: int | str | UUID, **kwargs: Any) -> Any:
        """Update a row by ID and return it."""
        return await self._get_related_repo().update_one_by_id(obj_id=obj_id, **kwargs)

    @transaction_mode
    async def delete_by_filter(self, **kwargs: Any) -> None:
        """Delete rows matching the filter."""
        await self._get_related_repo().delete_by_filter(**kwargs)

    @transaction_mode
    async def delete_by_ids(self, *args: int | str | UUID) -> None:
        """Delete rows by IDs."""
        await self._get_related_repo().delete_by_ids(*args)

    @transaction_mode
    async def delete_all(self) -> None:
        """Delete all rows."""
        await self._get_related_repo().delete_all()

    @staticmethod
    def check_existence(obj: Any, details: str) -> None:
        """Raise a not-found error if the object is missing."""
        if not obj:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=details)

    def _get_related_repo(self) -> AbstractRepository:
        """Resolve the repository named by the _repo attribute."""
        return getattr(self.uow, self._repo)
