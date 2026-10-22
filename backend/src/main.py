import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI

from src.api import router
from src.metadata import DESCRIPTION, TAG_METADATA, TITLE, VERSION
from src.storage import object_storage


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await object_storage.start()
    yield
    await object_storage.stop()


def create_fast_api_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    load_dotenv(find_dotenv('.env'))
    env_name = os.getenv('MODE', 'DEV')

    fastapi_app = FastAPI(
        title=TITLE,
        description=DESCRIPTION,
        version=VERSION,
        openapi_tags=TAG_METADATA,
        lifespan=lifespan,
        **({'docs_url': None, 'redoc_url': None} if env_name == 'PROD' else {}),
    )

    fastapi_app.include_router(router, prefix='/api')
    return fastapi_app


app = create_fast_api_app()
