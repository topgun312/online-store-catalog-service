TAG_METADATA = [
    {
        'name': 'Product | v1',
        'description': 'Operations with catalog products v1.',
    },
    {
        'name': 'Category | v1',
        'description': 'Operations with product categories v1.',
    },
    {
        'name': 'healthz',
        'description': 'Standard health check.',
    },
]

TITLE = 'Online Store Catalog Service'
DESCRIPTION = (
    'Catalog microservice (FastAPI).\n\n'
    'Architecture - onion layers + Unit of Work, examples taken from the book - https://www.cosmicpython.com.'
)
VERSION = '0.1.0'

ERRORS_MAP = {
    'postgres': 'PostgreSQL connection failed',
    'minio': 'MinIO (S3) connection failed',
}
