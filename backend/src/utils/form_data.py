from fastapi import HTTPException, UploadFile
from pydantic import UUID4
from starlette.status import HTTP_413_CONTENT_TOO_LARGE, HTTP_422_UNPROCESSABLE_CONTENT

from src.config import settings


async def read_upload_file(file: UploadFile) -> bytes:
    """Read the uploaded file and enforce the size limit."""
    file_bytes = await file.read(settings.MAX_IMAGE_SIZE_BYTES + 1)
    if len(file_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
        msg = f'Image is too large (max {settings.MAX_IMAGE_SIZE_BYTES} bytes)'
        raise HTTPException(status_code=HTTP_413_CONTENT_TOO_LARGE, detail=msg)
    return file_bytes


def parse_optional_uuid(value: str | None, field_name: str) -> UUID4 | None:
    """Parse an optional UUID form field."""
    if value is None or value == '':
        return None
    try:
        return UUID4(value)
    except ValueError:
        msg = f'Not valid {field_name}'
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_CONTENT, detail=msg) from None
