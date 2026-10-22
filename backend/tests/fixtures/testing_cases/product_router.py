from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from tests.constants import BASE_ENDPOINT_URL
from tests.utils import RequestTestCase

FAKE_JPEG_BYTES = b'\xff\xd8\xff\xe0fake-jpeg-bytes'

PRODUCT_ID = '3d3e784f-646a-4ad4-979c-dca5dcea2a28'
PRODUCT_IMAGE_KEY = 'products/11111111-2222-3333-4444-555555555555.jpg'
FAKE_IMAGE_URL = f'http://minio.test/catalog-images/{PRODUCT_IMAGE_KEY}?X-Amz-Signature=fake'

ELECTRONICS_CATEGORY_ID = '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e'
CLOTHING_CATEGORY_ID = '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f'
NON_EXISTENT_CATEGORY_ID = '4d3e784f-646a-4ad4-979c-dca5dcea2a28'

FIRST_PRODUCT_CATEGORY_FIELDS = {
    'category_id': ELECTRONICS_CATEGORY_ID,
    'category_name': 'Электроника',
}

TEST_PRODUCT_ROUTE_CREATE_PARAMS: list[RequestTestCase] = [
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': 'Iphone 15'},
        file=('photo.jpg', FAKE_JPEG_BYTES, 'image/jpeg'),
        expected_status=HTTP_201_CREATED,
        expected_data={'title': 'Iphone 15', 'category_id': None, 'category_name': None},
        description='Positive case',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': 'Iphone 16', 'category_id': ELECTRONICS_CATEGORY_ID},
        file=('photo.jpg', FAKE_JPEG_BYTES, 'image/jpeg'),
        expected_status=HTTP_201_CREATED,
        expected_data={'title': 'Iphone 16', **FIRST_PRODUCT_CATEGORY_FIELDS},
        description='Positive case with category',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': 'Bad category', 'category_id': NON_EXISTENT_CATEGORY_ID},
        file=('photo.jpg', FAKE_JPEG_BYTES, 'image/jpeg'),
        expected_status=HTTP_404_NOT_FOUND,
        expected_data={},
        description='Non-existent category',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': 'Not uuid category', 'category_id': '1'},
        file=('photo.jpg', FAKE_JPEG_BYTES, 'image/jpeg'),
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Not valid category id',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': 'No file product'},
        file=None,
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Without file',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': ''},
        file=('photo.jpg', FAKE_JPEG_BYTES, 'image/jpeg'),
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Empty title',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/',
        data={'title': 'Bad type'},
        file=('notes.txt', b'plain text', 'text/plain'),
        expected_status=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        expected_data={},
        description='Unsupported content type',
    ),
]

TEST_PRODUCT_ROUTE_GET_PARAMS: list[RequestTestCase] = [
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        expected_status=HTTP_200_OK,
        expected_data={
            'id': PRODUCT_ID,
            'title': 'Iphone 15',
            'image_url': FAKE_IMAGE_URL,
            **FIRST_PRODUCT_CATEGORY_FIELDS,
        },
        description='Positive case',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/1',
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Not valid product id',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/4d3e784f-646a-4ad4-979c-dca5dcea2a28',
        expected_status=HTTP_404_NOT_FOUND,
        expected_data={},
        description='Non-existent product',
    ),
]

TEST_PRODUCT_ROUTE_UPDATE_PARAMS: list[RequestTestCase] = [
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        data={'title': 'Iphone 15 Pro'},
        file=None,
        expected_status=HTTP_200_OK,
        expected_data={
            'id': PRODUCT_ID,
            'title': 'Iphone 15 Pro',
            'image_url': FAKE_IMAGE_URL,
            **FIRST_PRODUCT_CATEGORY_FIELDS,
        },
        description='Update title only',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        data={'category_id': CLOTHING_CATEGORY_ID},
        file=None,
        expected_status=HTTP_200_OK,
        expected_data={
            'id': PRODUCT_ID,
            'title': 'Iphone 15',
            'image_url': FAKE_IMAGE_URL,
            'category_id': CLOTHING_CATEGORY_ID,
            'category_name': 'Одежда',
        },
        description='Update category only',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        data={'remove_category': 'true'},
        file=None,
        expected_status=HTTP_200_OK,
        expected_data={
            'id': PRODUCT_ID,
            'title': 'Iphone 15',
            'image_url': FAKE_IMAGE_URL,
            'category_id': None,
            'category_name': None,
        },
        description='Remove category',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        data={'category_id': CLOTHING_CATEGORY_ID, 'remove_category': 'true'},
        file=None,
        expected_status=HTTP_400_BAD_REQUEST,
        expected_data={},
        description='category_id and remove_category together',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        data={'category_id': NON_EXISTENT_CATEGORY_ID},
        file=None,
        expected_status=HTTP_404_NOT_FOUND,
        expected_data={},
        description='Update to non-existent category',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/4d3e784f-646a-4ad4-979c-dca5dcea2a28',
        data={'title': 'Ghost product'},
        file=None,
        expected_status=HTTP_404_NOT_FOUND,
        expected_data={},
        description='Non-existent product',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/{PRODUCT_ID}',
        data={},
        file=None,
        expected_status=HTTP_400_BAD_REQUEST,
        expected_data={},
        description='Nothing to update',
    ),
]

TEST_PRODUCT_ROUTE_LIST_PARAMS: list[RequestTestCase] = [
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/?page=1&per_page=2',
        expected_status=HTTP_200_OK,
        expected_data={
            'meta': {'page': 1, 'per_page': 2, 'total': 3},
        },
        description='Positive case with pagination',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/?category=electronics',
        expected_status=HTTP_200_OK,
        expected_data={
            'meta': {'page': 1, 'per_page': 100, 'total': 2},
        },
        description='Filter by category slug',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/?category={ELECTRONICS_CATEGORY_ID}',
        expected_status=HTTP_200_OK,
        expected_data={
            'meta': {'page': 1, 'per_page': 100, 'total': 2},
        },
        description='Filter by category id',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/?category=missing-slug',
        expected_status=HTTP_404_NOT_FOUND,
        expected_data={},
        description='Filter by non-existent category',
    ),
    RequestTestCase(
        url=f'{BASE_ENDPOINT_URL}/product/?per_page=0',
        expected_status=HTTP_422_UNPROCESSABLE_ENTITY,
        expected_data={},
        description='Not valid per_page',
    ),
]
