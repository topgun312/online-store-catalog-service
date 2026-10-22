from typing import Any

from aiobotocore.session import AioSession, get_session
from botocore.config import Config
from loguru import logger

from src.storage.base import AbstractObjectStorage


class MinioStorage(AbstractObjectStorage):
    """Object storage backed by MinIO S3."""

    __slots__ = (
        '_access_key',
        '_bucket',
        '_client',
        '_config',
        '_endpoint_url',
        '_presign_client',
        '_public_endpoint_url',
        '_region',
        '_secret_key',
        '_session',
    )

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        public_endpoint_url: str | None = None,
        region: str = 'us-east-1',
    ) -> None:
        """Initialize the storage client configuration."""
        self._endpoint_url = endpoint_url
        self._public_endpoint_url = public_endpoint_url or endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region
        self._session: AioSession = get_session()
        self._config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'},
            retries={'max_attempts': 3, 'mode': 'standard'},
        )
        self._client: Any = None
        self._presign_client: Any = None

    async def _create_client(self, endpoint_url: str) -> Any:
        """Create an S3 client for the given endpoint."""
        client_cm = self._session.create_client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
            config=self._config,
        )
        return await client_cm.__aenter__()

    async def start(self) -> None:
        """Open the S3 clients and ensure the bucket exists."""
        self._client = await self._create_client(self._endpoint_url)
        if self._public_endpoint_url == self._endpoint_url:
            self._presign_client = self._client
        else:
            self._presign_client = await self._create_client(self._public_endpoint_url)
        await self._ensure_bucket()

    async def stop(self) -> None:
        """Close the S3 clients."""
        for client in {id(self._client): self._client, id(self._presign_client): self._presign_client}.values():
            if client is not None:
                await client.__aexit__(None, None, None)
        self._client = None
        self._presign_client = None

    async def _ensure_bucket(self) -> None:
        """Create the bucket if it does not exist."""
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            logger.info(f'Bucket {self._bucket!r} not found, creating...')
            await self._client.create_bucket(Bucket=self._bucket)

    def _require_client(self) -> Any:
        """Return the S3 client or fail if the storage is not started."""
        if self._client is None:
            msg = 'MinioStorage is not started (call start() first)'
            raise RuntimeError(msg)
        return self._client

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store an object in the bucket."""
        await self._require_client().put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def get(self, key: str) -> bytes:
        """Read an object from the bucket."""
        response = await self._require_client().get_object(Bucket=self._bucket, Key=key)
        async with response['Body'] as stream:
            return await stream.read()

    async def delete(self, key: str) -> None:
        """Delete an object from the bucket."""
        await self._require_client().delete_object(Bucket=self._bucket, Key=key)

    async def presign_url(self, key: str, expires_sec: int = 3600) -> str:
        """Generate a presigned download URL for an object."""
        if self._presign_client is None:
            msg = 'MinioStorage is not started'
            raise RuntimeError(msg)
        url = self._presign_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._bucket, 'Key': key},
            ExpiresIn=expires_sec,
        )
        if hasattr(url, '__await__'):
            url = await url
        return url

    async def healthcheck(self) -> bool:
        """Check that the bucket is accessible."""
        try:
            await self._require_client().head_bucket(Bucket=self._bucket)
        except Exception as exc:
            logger.error(f'MinIO health check failed: {exc}')
            return False
        return True
