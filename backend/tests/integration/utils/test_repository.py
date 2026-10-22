from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ProductModel
from src.repositories import ProductRepository
from src.schemas.filter import ProductFilters
from src.schemas.product import ProductDB
from src.utils.custom_types import AsyncFunc


class TestProductRepository:

    @staticmethod
    def __get_repo(session: AsyncSession) -> ProductRepository:
        return ProductRepository(session)

    @pytest.mark.usefixtures('setup_products')
    async def test_add_one_and_get_obj(
        self,
        transaction_session: AsyncSession,
        get_products: AsyncFunc,
    ) -> None:
        repo = self.__get_repo(transaction_session)
        new_product = {
            'title': 'Google Pixel 9',
            'image_key': 'products/pixel.jpg',
            'image_content_type': 'image/jpeg',
            'image_size_bytes': 300,
        }
        product: ProductModel = await repo.add_one_and_get_obj(**new_product)
        await transaction_session.flush()

        assert product.id is not None
        products_in_db = await get_products()
        assert len(products_in_db) == 4

    @pytest.mark.usefixtures('setup_products')
    async def test_get_by_filter_one_or_none(
        self,
        transaction_session: AsyncSession,
        first_product: dict,
    ) -> None:
        repo = self.__get_repo(transaction_session)
        product: ProductModel | None = await repo.get_by_filter_one_or_none(id=first_product['id'])

        assert product is not None
        product_data: ProductDB = product.to_schema()
        assert product_data.id == first_product['id']
        assert product_data.title == first_product['title']
        assert product_data.image_key == first_product['image_key']
        assert product_data.image_content_type == first_product['image_content_type']
        assert product_data.image_size_bytes == first_product['image_size_bytes']

    @pytest.mark.usefixtures('setup_products')
    async def test_get_products_by_filters_pagination(
        self,
        transaction_session: AsyncSession,
    ) -> None:
        repo = self.__get_repo(transaction_session)

        products, total = await repo.get_products_by_filters(ProductFilters(page=1, per_page=2))
        assert total == 3
        assert len(products) == 2

        products, total = await repo.get_products_by_filters(ProductFilters(page=2, per_page=2))
        assert total == 3
        assert len(products) == 1

    @pytest.mark.usefixtures('setup_products')
    async def test_get_products_by_filters_with_category_id(
        self,
        transaction_session: AsyncSession,
        first_product: dict,
    ) -> None:
        repo = self.__get_repo(transaction_session)

        products, total = await repo.get_products_by_filters(
            ProductFilters(page=1, per_page=10),
            category_id=first_product['category_id'],
        )
        assert total == 2
        assert len(products) == 2
        assert all(product.category_id == first_product['category_id'] for product in products)

        products, total = await repo.get_products_by_filters(
            ProductFilters(page=1, per_page=10),
            category_id=UUID('1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f'),
        )
        assert total == 0
        assert len(products) == 0

    @pytest.mark.usefixtures('setup_products')
    async def test_update_one_by_id(
        self,
        transaction_session: AsyncSession,
        first_product: dict,
    ) -> None:
        repo = self.__get_repo(transaction_session)
        updated: ProductModel | None = await repo.update_one_by_id(obj_id=first_product['id'], title='New title')
        await transaction_session.flush()

        assert updated is not None
        assert updated.title == 'New title'

    @pytest.mark.usefixtures('setup_products')
    async def test_delete_by_filter(
        self,
        transaction_session: AsyncSession,
        first_product: dict,
        get_products: AsyncFunc,
    ) -> None:
        repo = self.__get_repo(transaction_session)
        await repo.delete_by_filter(id=first_product['id'])
        await transaction_session.flush()

        products_in_db = await get_products()
        assert len(products_in_db) == 2
