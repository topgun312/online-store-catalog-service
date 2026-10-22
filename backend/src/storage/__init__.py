__all__ = [
    'AbstractObjectStorage',
    'MinioStorage',
    'get_object_storage',
    'object_storage',
]

from src.config import settings
from src.storage.base import AbstractObjectStorage
from src.storage.minio import MinioStorage


def _build_storage() -> AbstractObjectStorage:
    """Build the application-wide storage instance."""
    return MinioStorage(
        endpoint_url=settings.S3_ENDPOINT_URL,
        public_endpoint_url=settings.S3_PUBLIC_ENDPOINT_URL,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket=settings.S3_BUCKET,
        region=settings.S3_REGION,
    )


object_storage: AbstractObjectStorage = _build_storage()


def get_object_storage() -> AbstractObjectStorage:
    """Provide the application-wide storage instance."""
    return object_storage
