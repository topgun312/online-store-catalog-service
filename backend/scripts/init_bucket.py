import asyncio
import sys

from aiobotocore.session import get_session
from botocore.config import Config
from loguru import logger

from src.config import settings

CONFIG = Config(
    signature_version='s3v4',
    s3={'addressing_style': 'path'},
    retries={'max_attempts': 3, 'mode': 'standard'},
)

DOWNLOAD_POLICY = (
    '{"Version": "2012-10-17", "Statement": ['
    '{"Effect": "Allow", "Principal": {"AWS": ["*"]}, '
    f'"Action": ["s3:GetObject"], "Resource": ["arn:aws:s3:::{settings.S3_BUCKET}/*"]}}]}}'
)


async def main() -> int:
    """Create the images bucket and apply the anonymous download policy."""
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=CONFIG,
    ) as client:
        try:
            await client.head_bucket(Bucket=settings.S3_BUCKET)
            logger.info(f'bucket {settings.S3_BUCKET!r} already exists')
        except Exception:
            await client.create_bucket(Bucket=settings.S3_BUCKET)
            logger.info(f'bucket {settings.S3_BUCKET!r} created')

        try:
            await client.put_bucket_policy(Bucket=settings.S3_BUCKET, Policy=DOWNLOAD_POLICY)
            logger.info('anonymous download policy applied')
        except Exception as exc:
            logger.warning(f'could not set bucket policy: {exc}')
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
