from collections.abc import Sequence
from copy import deepcopy

import pytest
import pytest_asyncio
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import CategoryModel, ProductModel
from src.utils.custom_types import AsyncFunc
from tests import fixtures
from tests.utils import bulk_save_models


@pytest_asyncio.fixture
async def setup_categories(transaction_session: AsyncSession, categories: tuple[dict]) -> None:
    """Creates categories that will only exist within the session."""
    await bulk_save_models(transaction_session, CategoryModel, categories)


@pytest_asyncio.fixture
async def setup_products(setup_categories: None, transaction_session: AsyncSession, products: tuple[dict]) -> None:
    """Creates products that will only exist within the session."""
    await bulk_save_models(transaction_session, ProductModel, products)


@pytest_asyncio.fixture
def get_products(transaction_session: AsyncSession) -> AsyncFunc:
    """Returns products existing within the session."""

    async def _get_products() -> Sequence[ProductModel]:
        res: Result = await transaction_session.execute(select(ProductModel))
        return res.scalars().all()

    return _get_products


@pytest.fixture
def categories() -> tuple[dict]:
    return deepcopy(fixtures.db_mocks.CATEGORIES)


@pytest.fixture
def products() -> tuple[dict]:
    return deepcopy(fixtures.db_mocks.PRODUCTS)


@pytest.fixture
def first_product() -> dict:
    return deepcopy(fixtures.db_mocks.PRODUCTS[0])
