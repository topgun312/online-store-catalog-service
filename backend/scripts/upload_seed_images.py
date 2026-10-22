import asyncio
import colorsys
import sys
from io import BytesIO

from aiobotocore.session import get_session
from botocore.config import Config
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from src.config import settings

IMAGES_COUNT = 20
IMAGE_WIDTH = 600
IMAGE_HEIGHT = 400
KEY_TEMPLATE = 'products/test/seed-{index:04d}.jpg'
FONT_SIZE = 64
JPEG_QUALITY = 90
TEXT_COLOR = (20, 20, 20)

CONFIG = Config(
    signature_version='s3v4',
    s3={'addressing_style': 'path'},
    retries={'max_attempts': 3, 'mode': 'standard'},
)


def build_image(index: int) -> bytes:
    """Generate a placeholder image with a unique background color and label."""
    red, green, blue = colorsys.hsv_to_rgb((index % 24) / 24, 0.6, 0.9)
    background = (round(red * 255), round(green * 255), round(blue * 255))

    image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), background)
    draw = ImageDraw.Draw(image)
    text = f'Product {index}'
    font = ImageFont.load_default(size=FONT_SIZE)

    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    position = (
        (IMAGE_WIDTH - (right - left)) / 2 - left,
        (IMAGE_HEIGHT - (bottom - top)) / 2 - top,
    )
    draw.text(position, text, fill=TEXT_COLOR, font=font)

    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=JPEG_QUALITY)
    return buffer.getvalue()


def build_images() -> list[tuple[str, bytes]]:
    """Generate all placeholder images."""
    return [(KEY_TEMPLATE.format(index=index), build_image(index)) for index in range(1, IMAGES_COUNT + 1)]


async def upload_images(images: list[tuple[str, bytes]]) -> None:
    """Store the generated images in the object storage."""
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
        except Exception:
            logger.info('bucket {bucket!r} not found, creating...', bucket=settings.S3_BUCKET)
            await client.create_bucket(Bucket=settings.S3_BUCKET)

        for key, data in images:
            await client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType='image/jpeg')
            logger.info('uploaded {key} ({size} bytes)', key=key, size=len(data))


async def main() -> int:
    logger.info('generating {n} placeholder images...', n=IMAGES_COUNT)
    images = build_images()
    await upload_images(images)
    logger.info('uploaded {n} generated images to bucket {bucket!r}', n=len(images), bucket=settings.S3_BUCKET)
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
