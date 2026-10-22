import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv('.env'))


class Settings:
    """Application settings loaded from environment variables."""

    MODE: str = os.environ.get('MODE', 'DEV')
    LOG_TO_FILE: bool = os.environ.get('LOG_TO_FILE', '').lower() in {'1', 'true', 'yes'}
    LOG_FILE: str = os.environ.get('LOG_FILE', 'logs.json')

    DB_HOST: str = os.environ.get('DB_HOST', 'localhost')
    DB_PORT: int = int(os.environ.get('DB_PORT') or 5432)
    DB_USER: str = os.environ.get('DB_USER', 'postgres')
    DB_PASS: str = os.environ.get('DB_PASS', 'postgres')
    DB_NAME: str = os.environ.get('DB_NAME', 'catalog_db')
    DB_POOL_SIZE: int = int(os.environ.get('DB_POOL_SIZE') or 5)
    DB_MAX_OVERFLOW: int = int(os.environ.get('DB_MAX_OVERFLOW') or 10)
    DB_POOL_TIMEOUT: float = float(os.environ.get('DB_POOL_TIMEOUT') or 30)

    DB_URL: str = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    S3_ENDPOINT_URL: str = os.environ.get('S3_ENDPOINT_URL', 'http://localhost:9000')
    S3_PUBLIC_ENDPOINT_URL: str | None = os.environ.get('S3_PUBLIC_ENDPOINT_URL') or None
    S3_ACCESS_KEY: str = os.environ.get('S3_ACCESS_KEY', 'minioadmin')
    S3_SECRET_KEY: str = os.environ.get('S3_SECRET_KEY', 'minioadmin')
    S3_BUCKET: str = os.environ.get('S3_BUCKET', 'catalog-images')
    S3_REGION: str = os.environ.get('S3_REGION', 'us-east-1')

    IMAGE_URL_MODE: str = os.environ.get('IMAGE_URL_MODE', 'presign')
    PUBLIC_BASE_URL: str = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:8000')
    IMAGE_URL_TTL_SEC: int = int(os.environ.get('IMAGE_URL_TTL_SEC') or 3600)

    MAX_IMAGE_SIZE_BYTES: int = int(os.environ.get('MAX_IMAGE_SIZE_BYTES') or 5 * 1024 * 1024)
    ALLOWED_IMAGE_TYPES: frozenset[str] = frozenset(
        filter(
            None,
            os.environ.get('ALLOWED_IMAGE_TYPES', 'image/jpeg,image/png,image/webp').split(','),
        ),
    )


settings = Settings()
