from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from pydantic import UUID4
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.api.v1.services.product import ProductService
from src.schemas.filter import ProductFilters
from src.schemas.product import (
    CreateProductResponse,
    ProductPayload,
    ProductResponse,
    ProductsListResponse,
)
from src.utils.form_data import parse_optional_uuid, read_upload_file

router = APIRouter(prefix='/product')


@router.post(
    path='/',
    status_code=HTTP_201_CREATED,
)
async def create_product(
    title: str = Form(..., min_length=1, max_length=255),
    file: UploadFile = File(...),
    category_id: str | None = Form(default=None),
    service: ProductService = Depends(),
) -> CreateProductResponse:
    """Create a new product with an uploaded image."""
    file_bytes = await read_upload_file(file)
    created: ProductPayload = await service.create_product(
        title=title,
        file_bytes=file_bytes,
        content_type=file.content_type,
        category_id=parse_optional_uuid(category_id, field_name='category_id'),
    )
    return CreateProductResponse(payload=created)


@router.get(
    path='/',
    status_code=HTTP_200_OK,
)
async def get_products_by_filters(
    filters: ProductFilters = Depends(),
    service: ProductService = Depends(),
) -> ProductsListResponse:
    """Get a paginated list of products filtered by category."""
    products, meta = await service.get_products_by_filters(filters)
    return ProductsListResponse(payload=products, meta=meta)


@router.get(
    path='/{product_id}',
    status_code=HTTP_200_OK,
)
async def get_product(
    product_id: UUID4,
    service: ProductService = Depends(),
) -> ProductResponse:
    """Get a product by ID."""
    product: ProductPayload = await service.get_product_by_id(product_id)
    return ProductResponse(payload=product)


@router.get(
    path='/{product_id}/image/',
    status_code=HTTP_200_OK,
)
async def get_product_image(
    product_id: UUID4,
    service: ProductService = Depends(),
) -> Response:
    """Serve the product image bytes."""
    data, content_type = await service.get_product_image(product_id)
    return Response(
        content=data,
        media_type=content_type,
        headers={'Cache-Control': 'public, max-age=3600, immutable'},
    )


@router.put(
    path='/{product_id}',
    status_code=HTTP_200_OK,
)
async def update_product(
    product_id: UUID4,
    *,
    title: str | None = Form(default=None, min_length=1, max_length=255),
    file: UploadFile | None = File(default=None),
    category_id: str | None = Form(default=None),
    remove_category: bool = Form(default=False),
    service: ProductService = Depends(),
) -> ProductResponse:
    """Update the product title, image and/or category."""
    file_bytes: bytes | None = None
    if file is not None:
        file_bytes = await read_upload_file(file)
    updated: ProductPayload = await service.update_product(
        product_id=product_id,
        title=title,
        file_bytes=file_bytes,
        content_type=file.content_type if file is not None else None,
        category_id=parse_optional_uuid(category_id, field_name='category_id'),
        remove_category=remove_category,
    )
    return ProductResponse(payload=updated)


@router.delete(
    path='/{product_id}',
    status_code=HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: UUID4,
    service: ProductService = Depends(),
) -> None:
    """Delete a product together with its image."""
    await service.delete_product(product_id)
