from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from tests.constants import BASE_ENDPOINT_URL
from tests.utils import RequestTestCase

ELECTRONICS_CATEGORY_ID = '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e'

TEST_CATEGORY_ROUTE_CREATE_PARAMS: list[RequestTestCase] = [
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/',
        data={'name': 'Книги'},
        expected_status=HTTP_201_CREATED,
        expected_data={'name': 'Книги', 'slug': 'книги'},
        description='Positive case (slug is generated from the name)',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/',
        data={'name': 'Игрушки', 'slug': 'toys'},
        expected_status=HTTP_201_CREATED,
        expected_data={'name': 'Игрушки', 'slug': 'toys'},
        description='Positive case with explicit slug',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/',
        data={'name': 'Одежда'},
        expected_status=HTTP_409_CONFLICT,
        expected_data={},
        description='Duplicate name',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/',
        data={'name': 'Бытовая техника', 'slug': 'electronics'},
        expected_status=HTTP_409_CONFLICT,
        expected_data={},
        description='Duplicate slug',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/',
        data={'name': ''},
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Empty name',
    ),
]

TEST_CATEGORY_ROUTE_GET_PARAMS: list[RequestTestCase] = [
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/{ELECTRONICS_CATEGORY_ID}',
        expected_status=HTTP_200_OK,
        expected_data={'id': ELECTRONICS_CATEGORY_ID, 'name': 'Электроника', 'slug': 'electronics'},
        description='Positive case',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/1',
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Not valid category id',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/category/4d3e784f-646a-4ad4-979c-dca5dcea2a28',
        expected_status=HTTP_404_NOT_FOUND,
        expected_data={},
        description='Non-existent category',
    ),
]
