import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from tests.constants import BASE_ENDPOINT_URL
from tests.fixtures import testing_cases
from tests.utils import RequestTestCase, prepare_payload


class TestCategoryRouter:

    @staticmethod
    @pytest.mark.usefixtures('setup_categories')
    @pytest.mark.parametrize('case', testing_cases.TEST_CATEGORY_ROUTE_CREATE_PARAMS)
    async def test_create(
        case: RequestTestCase,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(case.url, json=case.data)

        assert response.status_code == case.expected_status
        assert prepare_payload(response, ['id']) == case.expected_data
        if case.expected_status == HTTP_201_CREATED:
            assert response.json()['payload']['id']

    @staticmethod
    @pytest.mark.usefixtures('setup_categories')
    @pytest.mark.parametrize('case', testing_cases.TEST_CATEGORY_ROUTE_GET_PARAMS)
    async def test_get(
        case: RequestTestCase,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(case.url, headers=case.headers)

        assert response.status_code == case.expected_status
        if case.expected_status == HTTP_200_OK:
            assert prepare_payload(response, []) == case.expected_data
        else:
            assert response.json().get('payload') is None

    @staticmethod
    @pytest.mark.usefixtures('setup_categories')
    async def test_list(async_client: AsyncClient) -> None:
        response = await async_client.get(f'{BASE_ENDPOINT_URL}/category/')

        assert response.status_code == HTTP_200_OK
        payload = response.json()['payload']
        assert len(payload) == 3
        assert {item['name'] for item in payload} == {'Электроника', 'Одежда', 'Другое'}
        assert {item['slug'] for item in payload} == {'electronics', 'clothing', 'other'}

    @staticmethod
    async def test_list_without_categories(async_client: AsyncClient) -> None:
        response = await async_client.get(f'{BASE_ENDPOINT_URL}/category/')

        assert response.status_code == HTTP_200_OK
        assert response.json()['payload'] == []
