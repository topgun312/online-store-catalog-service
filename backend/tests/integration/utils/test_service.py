from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from src.api.v1.services import ProductService
from src.schemas.filter import ProductFilters
from tests.fixtures import FakeObjectStorage, FakeProductService

FAKE_JPEG = b'\xff\xd8\xff\xe0fake-jpeg'
ELECTRONICS_CATEGORY_ID = UUID('0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e')


@pytest.fixture
def product_service(transaction_session: AsyncSession) -> ProductService:
    return FakeProductService(transaction_session)


@pytest.fixture
def product_service_with_storage(transaction_session: AsyncSession) -> tuple[ProductService, FakeObjectStorage]:
    storage = FakeObjectStorage()
    return FakeProductService(transaction_session, storage), storage


class TestProductService:

    @pytest.mark.usefixtures('setup_products')
    async def test_create_product(
        self,
        product_service_with_storage: tuple[ProductService, FakeObjectStorage],
    ) -> None:
        service, storage = product_service_with_storage

        payload = await service.create_product(title='Iphone 16', file_bytes=FAKE_JPEG, content_type='image/jpeg')

        assert payload.title == 'Iphone 16'
        assert len(storage.objects) == 1
        ((key, (_data, content_type)),) = storage.objects.items()
        assert payload.image_url == FakeObjectStorage.FAKE_PRESIGN_URL.format(key=key)
        assert content_type == 'image/jpeg'

    @pytest.mark.usefixtures('setup_products')
    async def test_get_product_by_id(
        self,
        product_service: ProductService,
        first_product: dict,
    ) -> None:
        payload = await product_service.get_product_by_id(first_product['id'])
        assert payload.id == first_product['id']
        assert payload.title == first_product['title']

    @pytest.mark.usefixtures('setup_products')
    async def test_get_product_by_id_not_found(
        self,
        product_service: ProductService,
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await product_service.get_product_by_id(uuid4())
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.usefixtures('setup_products')
    async def test_get_products_by_filters(
        self,
        product_service: ProductService,
    ) -> None:
        payloads, meta = await product_service.get_products_by_filters(ProductFilters(page=1, per_page=10))

        assert meta.total == 3
        assert len(payloads) == 3

    @pytest.mark.usefixtures('setup_products')
    async def test_get_products_by_filters_with_category(
        self,
        product_service: ProductService,
    ) -> None:
        payloads, meta = await product_service.get_products_by_filters(
            ProductFilters(page=1, per_page=10, category='electronics'),
        )

        assert meta.total == 2
        assert len(payloads) == 2
        assert all(payload.category_id == ELECTRONICS_CATEGORY_ID for payload in payloads)
        assert all(payload.category_name == 'Электроника' for payload in payloads)

    @pytest.mark.usefixtures('setup_products')
    async def test_get_products_by_filters_with_category_id(
        self,
        product_service: ProductService,
    ) -> None:
        payloads, meta = await product_service.get_products_by_filters(
            ProductFilters(page=1, per_page=10, category=str(ELECTRONICS_CATEGORY_ID)),
        )

        assert meta.total == 2
        assert len(payloads) == 2

    @pytest.mark.usefixtures('setup_products')
    async def test_get_products_by_filters_with_missing_category(
        self,
        product_service: ProductService,
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await product_service.get_products_by_filters(ProductFilters(page=1, per_page=10, category='missing'))
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.usefixtures('setup_products')
    async def test_create_product_with_category(
        self,
        product_service_with_storage: tuple[ProductService, FakeObjectStorage],
    ) -> None:
        service, _storage = product_service_with_storage

        payload = await service.create_product(
            title='Iphone 17',
            file_bytes=FAKE_JPEG,
            content_type='image/jpeg',
            category_id=ELECTRONICS_CATEGORY_ID,
        )

        assert payload.category_id == ELECTRONICS_CATEGORY_ID
        assert payload.category_name == 'Электроника'

    @pytest.mark.usefixtures('setup_products')
    async def test_create_product_with_missing_category(
        self,
        product_service_with_storage: tuple[ProductService, FakeObjectStorage],
    ) -> None:
        service, storage = product_service_with_storage

        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(
                title='Iphone 17',
                file_bytes=FAKE_JPEG,
                content_type='image/jpeg',
                category_id=uuid4(),
            )

        assert exc_info.value.status_code == HTTP_404_NOT_FOUND
        assert storage.objects == {}

    @pytest.mark.usefixtures('setup_products')
    async def test_update_product_category(
        self,
        product_service: ProductService,
        first_product: dict,
    ) -> None:
        payload = await product_service.update_product(
            product_id=first_product['id'],
            title=None,
            file_bytes=None,
            content_type=None,
            remove_category=True,
        )
        assert payload.category_id is None
        assert payload.category_name is None

        payload = await product_service.update_product(
            product_id=first_product['id'],
            title=None,
            file_bytes=None,
            content_type=None,
            category_id=ELECTRONICS_CATEGORY_ID,
        )
        assert payload.category_id == ELECTRONICS_CATEGORY_ID
        assert payload.category_name == 'Электроника'

    @pytest.mark.usefixtures('setup_products')
    async def test_update_product_title_only(
        self,
        product_service_with_storage: tuple[ProductService, FakeObjectStorage],
        first_product: dict,
    ) -> None:
        service, storage = product_service_with_storage

        payload = await service.update_product(
            product_id=first_product['id'],
            title='New title',
            file_bytes=None,
            content_type=None,
        )

        assert payload.title == 'New title'
        assert payload.image_url == FakeObjectStorage.FAKE_PRESIGN_URL.format(key=first_product['image_key'])
        assert storage.deleted_keys == []

    @pytest.mark.usefixtures('setup_products')
    async def test_update_product_with_file_deletes_old_object(
        self,
        product_service_with_storage: tuple[ProductService, FakeObjectStorage],
        first_product: dict,
    ) -> None:
        service, storage = product_service_with_storage
        old_key = first_product['image_key']
        storage.objects[old_key] = (b'old', 'image/jpeg')

        payload = await service.update_product(
            product_id=first_product['id'],
            title=None,
            file_bytes=FAKE_JPEG,
            content_type='image/jpeg',
        )

        assert payload.image_url != FakeObjectStorage.FAKE_PRESIGN_URL.format(key=old_key)
        assert old_key in storage.deleted_keys

    @pytest.mark.usefixtures('setup_products')
    async def test_delete_product_removes_record_and_object(
        self,
        product_service_with_storage: tuple[ProductService, FakeObjectStorage],
        first_product: dict,
    ) -> None:
        service, storage = product_service_with_storage
        old_key = first_product['image_key']
        storage.objects[old_key] = (b'old', 'image/jpeg')

        await service.delete_product(first_product['id'])

        assert old_key in storage.deleted_keys
        assert old_key not in storage.objects
        with pytest.raises(HTTPException) as exc_info:
            await service.get_product_by_id(first_product['id'])
        assert exc_info.value.status_code == HTTP_404_NOT_FOUND
