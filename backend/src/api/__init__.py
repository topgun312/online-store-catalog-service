__all__ = [
    'router',
]

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from src.api.v1.routers import v1_category_router, v1_product_router
from src.database.db import get_async_session
from src.metadata import ERRORS_MAP
from src.schemas.response import BaseResponse
from src.storage import AbstractObjectStorage, get_object_storage

router = APIRouter()
router.include_router(v1_product_router, prefix='/v1', tags=['Product | v1'])
router.include_router(v1_category_router, prefix='/v1', tags=['Category | v1'])


async def _check_backing_services(session: AsyncSession, storage: AbstractObjectStorage) -> None:
    """Check that PostgreSQL and MinIO are available."""

    async def check_postgres() -> None:
        try:
            await session.execute(text('SELECT 1'))
        except Exception as exc:
            logger.error(f'Health check failed with error: {exc}')
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=ERRORS_MAP.get('postgres')) from exc

    async def check_minio() -> None:
        if not await storage.healthcheck():
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=ERRORS_MAP.get('minio'))

    await asyncio.gather(
        check_postgres(),
        check_minio(),
    )


@router.get(
    path='/healthz/',
    tags=['healthz'],
    status_code=HTTP_200_OK,
)
async def health_check(
    session: AsyncSession = Depends(get_async_session),
    storage: AbstractObjectStorage = Depends(get_object_storage),
) -> BaseResponse:
    """Check readiness of PostgreSQL and MinIO."""
    await _check_backing_services(session=session, storage=storage)
    return BaseResponse()
