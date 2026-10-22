from abc import ABC, abstractmethod


class AbstractObjectStorage(ABC):
    """Interface for object storage of product images."""

    async def start(self) -> None:  # noqa: B027
        ...

    async def stop(self) -> None:  # noqa: B027
        ...

    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def presign_url(self, key: str, expires_sec: int = 3600) -> str:
        raise NotImplementedError

    @abstractmethod
    async def healthcheck(self) -> bool:
        raise NotImplementedError
