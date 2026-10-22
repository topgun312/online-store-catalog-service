from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Never

from src.database.db import async_session_maker
from src.repositories import CategoryRepository, ProductRepository


class AbstractUnitOfWork(ABC):
    is_open: bool
    category: CategoryRepository
    product: ProductRepository

    @abstractmethod
    def __init__(self) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def flush(self) -> Never:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> Never:
        raise NotImplementedError


class UnitOfWork(AbstractUnitOfWork):
    """SQLAlchemy implementation of the unit of work."""

    __slots__ = (
        '_session',
        'category',
        'is_open',
        'product',
    )

    def __init__(self) -> None:
        """Mark the unit of work as closed."""
        self.is_open = False

    async def __aenter__(self) -> None:
        """Open a session and create the repositories."""
        self._session = async_session_maker()
        self.category = CategoryRepository(self._session)
        self.product = ProductRepository(self._session)
        self.is_open = True

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit on success, roll back on error and close the session."""
        if not exc_type:
            await self._session.commit()
        else:
            await self.rollback()
        await self._session.close()
        self.is_open = False

    async def flush(self) -> None:
        """Flush pending changes to the database."""
        await self._session.flush()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self._session.rollback()

    async def session_add(self, obj: Any) -> None:
        """Add an object to the session."""
        self._session.add(obj)

    async def session_refresh(self, obj: Any) -> None:
        """Refresh an object from the database."""
        await self._session.refresh(obj)

    def __getattr__(self, name: str) -> None:
        """Raise an informative error for a missing attribute."""
        err_msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
        if name in self.__slots__ and not self.is_open:
            err_msg = f"Attempting to access '{name}' with a closed UnitOfWork"
        raise AttributeError(err_msg)
