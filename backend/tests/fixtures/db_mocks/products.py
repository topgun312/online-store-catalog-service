from uuid import UUID

ELECTRONICS_CATEGORY_ID = UUID('0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e')

PRODUCTS = (
    {
        'id': UUID('3d3e784f-646a-4ad4-979c-dca5dcea2a28'),
        'title': 'Iphone 15',
        'image_key': 'products/11111111-2222-3333-4444-555555555555.jpg',
        'image_content_type': 'image/jpeg',
        'image_size_bytes': 1024,
        'category_id': ELECTRONICS_CATEGORY_ID,
    },
    {
        'id': UUID('bb929d29-a8ef-4a8e-b998-9998984d8fd6'),
        'title': 'Samsung Galaxy S24',
        'image_key': 'products/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.png',
        'image_content_type': 'image/png',
        'image_size_bytes': 2048,
        'category_id': ELECTRONICS_CATEGORY_ID,
    },
    {
        'id': UUID('d5621653-f72b-4124-98e6-79c5d9c2dc2b'),
        'title': 'Xiaomi 14',
        'image_key': 'products/99999999-8888-7777-6666-555555555555.webp',
        'image_content_type': 'image/webp',
        'image_size_bytes': 512,
        'category_id': None,
    },
)
