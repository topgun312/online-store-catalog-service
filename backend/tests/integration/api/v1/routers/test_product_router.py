import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from tests.constants import BASE_ENDPOINT_URL
from tests.fixtures import FakeObjectStorage, testing_cases
from tests.utils import RequestTestCase, prepare_payload


class TestProductRouter:

    @staticmethod
    @pytest.mark.usefixtures('setup_categories')
    @pytest.mark.parametrize('case', testing_cases.TEST_PRODUCT_ROUTE_CREATE_PARAMS)
    async def test_create(
        case: RequestTestCase,
        async_client: AsyncClient,
        fake_storage: FakeObjectStorage,
    ) -> None:
        files = {'file': case.file} if case.file else None
        response = await async_client.post(case.url, data=case.data, files=files)

        assert response.status_code == case.expected_status
        assert prepare_payload(response, ['id', 'image_url', 'created_at']) == case.expected_data
        if case.expected_status == HTTP_201_CREATED:
            assert len(fake_storage.objects) == 1
            image_url = response.json()['payload']['image_url']
            assert image_url.startswith('http://minio.test/catalog-images/products/')

    @staticmethod
    @pytest.mark.usefixtures('setup_products')
    @pytest.mark.parametrize('case', testing_cases.TEST_PRODUCT_ROUTE_GET_PARAMS)
    async def test_get(
        case: RequestTestCase,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(case.url, headers=case.headers)

        assert response.status_code == case.expected_status
        if case.expected_status == HTTP_200_OK:
            assert prepare_payload(response, ['created_at']) == case.expected_data
        else:
            assert response.json().get('payload') is None

    @staticmethod
    @pytest.mark.usefixtures('setup_products')
    @pytest.mark.parametrize('case', testing_cases.TEST_PRODUCT_ROUTE_LIST_PARAMS)
    async def test_list(
        case: RequestTestCase,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(case.url, headers=case.headers)

        assert response.status_code == case.expected_status
        if case.expected_status == HTTP_200_OK:
            body = response.json()
            assert body['meta'] == case.expected_data['meta']
            assert len(body['payload']) == min(body['meta']['per_page'], body['meta']['total'])
            assert all('image_url' in item for item in body['payload'])
            assert all('category_id' in item and 'category_name' in item for item in body['payload'])
        else:
            assert response.json().get('payload') is None

    @staticmethod
    @pytest.mark.usefixtures('setup_products')
    @pytest.mark.parametrize('case', testing_cases.TEST_PRODUCT_ROUTE_UPDATE_PARAMS)
    async def test_update(
        case: RequestTestCase,
        async_client: AsyncClient,
    ) -> None:
        files = {'file': case.file} if case.file else None
        response = await async_client.put(case.url, data=case.data, files=files)

        assert response.status_code == case.expected_status
        if case.expected_status == HTTP_200_OK:
            assert prepare_payload(response, ['created_at']) == case.expected_data

    @staticmethod
    @pytest.mark.usefixtures('setup_products')
    async def test_update_with_file_replaces_storage_object(
        async_client: AsyncClient,
        fake_storage: FakeObjectStorage,
        first_product: dict,
    ) -> None:
        old_key = first_product['image_key']
        fake_storage.objects[old_key] = (b'old-bytes', 'image/jpeg')

        response = await async_client.put(
            f'{BASE_ENDPOINT_URL}/product/{first_product["id"]}',
            data={'title': 'Iphone 15 Ultra'},
            files={'file': ('new.jpg', b'\xff\xd8\xff\xe0new-bytes', 'image/jpeg')},
        )

        assert response.status_code == HTTP_200_OK
        body = response.json()['payload']
        assert body['title'] == 'Iphone 15 Ultra'
        assert old_key not in body['image_url']
        assert old_key in fake_storage.deleted_keys

    @staticmethod
    @pytest.mark.usefixtures('setup_products')
    async def test_delete(
        async_client: AsyncClient,
        fake_storage: FakeObjectStorage,
        first_product: dict,
    ) -> None:
        old_key = first_product['image_key']
        fake_storage.objects[old_key] = (b'old-bytes', 'image/jpeg')

        response = await async_client.delete(
            f'{BASE_ENDPOINT_URL}/product/{first_product["id"]}',
        )

        assert response.status_code == HTTP_204_NO_CONTENT
        assert old_key in fake_storage.deleted_keys
        assert old_key not in fake_storage.objects

        get_response = await async_client.get(f'{BASE_ENDPOINT_URL}/product/{first_product["id"]}')
        assert get_response.status_code == HTTP_404_NOT_FOUND
