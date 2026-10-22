"""The package contains various data used in tests."""

__all__ = [
    'FakeBaseService',
    'FakeObjectStorage',
    'FakeUnitOfWork',
    'ProductService',
    'db_mocks',
    'testing_cases',
]

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.services import ProductService
from src.repositories import CategoryRepository, ProductRepository
from src.storage.base import AbstractObjectStorage
from src.utils.service import BaseService
from src.utils.unit_of_work import UnitOfWork
from tests.fixtures import db_mocks, testing_cases


class FakeUnitOfWork(UnitOfWork):
    """Test class for overriding the standard UnitOfWork.
    Provides isolation using transactions at the level of a single TestCase.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self._session = session

    async def __aenter__(self) -> None:
        self.category = CategoryRepository(self._session)
        self.product = ProductRepository(self._session)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._session.flush()


class FakeObjectStorage(AbstractObjectStorage):
    """In-memory object storage for tests (no MinIO required)."""

    FAKE_PRESIGN_URL = 'http://minio.test/catalog-images/{key}?X-Amz-Signature=fake'

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.deleted_keys: list[str] = []

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    async def get(self, key: str) -> bytes:
        return self.objects[key][0]

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)
        self.deleted_keys.append(key)

    async def presign_url(self, key: str, expires_sec: int = 3600) -> str:
        return self.FAKE_PRESIGN_URL.format(key=key)

    async def healthcheck(self) -> bool:
        return True


class FakeBaseService(BaseService):
    """Base service bound to a FakeUnitOfWork."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.uow = FakeUnitOfWork(session)


class FakeProductService(ProductService):
    """Product service bound to a FakeUnitOfWork + FakeObjectStorage."""

    def __init__(self, session: AsyncSession, storage: FakeObjectStorage | None = None) -> None:
        self.uow = FakeUnitOfWork(session)
        self.storage = storage or FakeObjectStorage()
