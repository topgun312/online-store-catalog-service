from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException
from loguru import logger
from pydantic import UUID4
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_413_CONTENT_TOO_LARGE,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
)

from src.config import settings
from src.models import ProductModel
from src.schemas.product import PageMeta, ProductDB, ProductPayload
from src.storage import AbstractObjectStorage, get_object_storage
from src.utils.constans import CATEGORY_NOT_FOUND_MSG, PRODUCT_NOT_FOUND_MSG
from src.utils.service import BaseService, transaction_mode
from src.utils.unit_of_work import UnitOfWork

if TYPE_CHECKING:
    from src.models import CategoryModel
    from src.schemas.filter import ProductFilters

IMAGE_EXT_BY_CONTENT_TYPE = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
}


class ProductService(BaseService):
    """Business logic for catalog products."""

    _repo: str = 'product'

    def __init__(
        self,
        uow: UnitOfWork = Depends(),
        storage: AbstractObjectStorage = Depends(get_object_storage),
    ) -> None:
        """Initialize the service with a unit of work and object storage."""
        super().__init__(uow)
        self.storage = storage

    async def create_product(
        self,
        title: str,
        file_bytes: bytes,
        content_type: str,
        category_id: UUID4 | None = None,
    ) -> ProductPayload:
        """Create a product and store its image."""
        self._validate_image(file_bytes=file_bytes, content_type=content_type)
        if category_id is not None:
            await self._check_category_exists(category_id)

        image_key = self._build_image_key(content_type=content_type)
        await self.storage.put(key=image_key, data=file_bytes, content_type=content_type)
        try:
            created_id: UUID = await self._insert_product(
                title=title,
                image_key=image_key,
                content_type=content_type,
                file_size=len(file_bytes),
                category_id=category_id,
            )
        except Exception:
            await self._safe_delete_object(image_key)
            raise

        created = await self._get_product_model(product_id=created_id)
        return await self._to_payload(created)

    async def update_product(
        self,
        product_id: UUID4,
        title: str | None,
        file_bytes: bytes | None,
        content_type: str | None,
        *,
        category_id: UUID4 | None = None,
        remove_category: bool = False,
    ) -> ProductPayload:
        """Update product fields, replacing the image if provided."""
        if remove_category and category_id is not None:
            msg = 'Provide either category_id or remove_category, not both'
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=msg)

        has_changes = any((title is not None, file_bytes is not None, category_id is not None, remove_category))
        if not has_changes:
            msg = 'Nothing to update: provide a title, a file and/or a category'
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=msg)

        if category_id is not None:
            await self._check_category_exists(category_id)

        new_key: str | None = None
        if file_bytes is not None:
            self._validate_image(file_bytes=file_bytes, content_type=content_type)
            new_key = self._build_image_key(content_type=content_type)
            await self.storage.put(key=new_key, data=file_bytes, content_type=content_type)

        try:
            old_key = await self._update_product_in_db(
                product_id=product_id,
                title=title,
                image_key=new_key,
                content_type=content_type if file_bytes is not None else None,
                file_size=len(file_bytes) if file_bytes is not None else None,
                category_id=category_id,
                remove_category=remove_category,
            )
        except Exception:
            if new_key is not None:
                await self._safe_delete_object(new_key)
            raise

        if new_key is not None and old_key is not None and old_key != new_key:
            await self._safe_delete_object(old_key)

        updated = await self._get_product_model(product_id=product_id)
        return await self._to_payload(updated)

    async def delete_product(self, product_id: UUID4) -> None:
        """Delete a product and its stored image."""
        image_key = await self._delete_product_in_db(product_id=product_id)
        await self._safe_delete_object(image_key)

    @transaction_mode
    async def _insert_product(
        self,
        title: str,
        image_key: str,
        content_type: str,
        file_size: int,
        category_id: UUID4 | None,
    ) -> UUID:
        """Insert a product row and return its ID."""
        return await self.uow.product.add_one_and_get_id(
            title=title,
            image_key=image_key,
            image_content_type=content_type,
            image_size_bytes=file_size,
            category_id=category_id,
        )

    @transaction_mode
    async def _update_product_in_db(
        self,
        product_id: UUID4,
        title: str | None,
        image_key: str | None,
        content_type: str | None,
        file_size: int | None,
        *,
        category_id: UUID4 | None,
        remove_category: bool,
    ) -> str:
        """Apply product changes and return the old image key."""
        product: ProductModel | None = await self.uow.product.get_by_filter_one_or_none(id=product_id)
        self.check_existence(obj=product, details=PRODUCT_NOT_FOUND_MSG)

        old_key = product.image_key

        values: dict = {}
        if title is not None:
            values['title'] = title
        if image_key is not None:
            values.update(
                image_key=image_key,
                image_content_type=content_type,
                image_size_bytes=file_size,
            )
        if remove_category:
            values['category_id'] = None
        elif category_id is not None:
            values['category_id'] = category_id

        await self.uow.product.update_one_by_id(obj_id=product_id, **values)
        return old_key

    @transaction_mode
    async def _delete_product_in_db(self, product_id: UUID4) -> str:
        """Delete a product row and return its image key."""
        product: ProductModel | None = await self.uow.product.get_by_filter_one_or_none(id=product_id)
        self.check_existence(obj=product, details=PRODUCT_NOT_FOUND_MSG)
        await self.uow.product.delete_by_filter(id=product_id)
        return product.image_key

    @transaction_mode
    async def _check_category_exists(self, category_id: UUID4) -> str:
        """Ensure the category exists."""
        category: CategoryModel | None = await self.uow.category.get_by_filter_one_or_none(id=category_id)
        self.check_existence(obj=category, details=CATEGORY_NOT_FOUND_MSG)
        return category.name

    @transaction_mode
    async def get_product_by_id(self, product_id: UUID4) -> ProductPayload:
        """Get a product by ID."""
        product: ProductModel | None = await self.uow.product.get_by_filter_one_or_none(id=product_id)
        self.check_existence(obj=product, details=PRODUCT_NOT_FOUND_MSG)
        return await self._to_payload(product)

    @transaction_mode
    async def get_products_by_filters(self, filters: 'ProductFilters') -> tuple[list[ProductPayload], PageMeta]:
        """Get products matching the filters along with page metadata."""
        category_id: UUID | None = None
        if filters.category:
            category = await self.uow.category.get_by_filter_one_or_none(slug=filters.category)
            if category is None:
                try:
                    category = await self.uow.category.get_by_filter_one_or_none(id=UUID4(filters.category))
                except ValueError:
                    category = None
            self.check_existence(obj=category, details=CATEGORY_NOT_FOUND_MSG)
            category_id = category.id

        products, total = await self.uow.product.get_products_by_filters(filters, category_id=category_id)
        payloads = [await self._to_payload(product) for product in products]
        meta = PageMeta(page=filters.page, per_page=filters.per_page, total=total)
        return payloads, meta

    async def get_product_image(self, product_id: UUID4) -> tuple[bytes, str]:
        """Load the product image bytes and content type."""
        product = await self._get_product_model(product_id=product_id)
        data = await self.storage.get(key=product.image_key)
        return data, product.image_content_type or 'application/octet-stream'

    @transaction_mode
    async def _get_product_model(self, product_id: UUID4) -> ProductModel:
        """Load a product model or raise a not-found error."""
        product: ProductModel | None = await self.uow.product.get_by_filter_one_or_none(id=product_id)
        self.check_existence(obj=product, details=PRODUCT_NOT_FOUND_MSG)
        return product

    async def _to_payload(self, product: ProductModel) -> ProductPayload:
        """Convert a product model to an API payload with an image URL."""
        data: ProductDB = product.to_schema()
        image_url = await self._build_image_url(data)
        return data.to_payload(image_url=image_url)

    async def _build_image_url(self, product: ProductDB) -> str:
        """Build the image URL according to the configured mode."""
        if settings.IMAGE_URL_MODE == 'proxy':
            return f'{settings.PUBLIC_BASE_URL.rstrip("/")}/api/v1/product/{product.id}/image/'
        return await self.storage.presign_url(key=product.image_key, expires_sec=settings.IMAGE_URL_TTL_SEC)

    async def _safe_delete_object(self, key: str) -> None:
        """Delete a storage object, logging any failure."""
        try:
            await self.storage.delete(key=key)
        except Exception as exc:
            logger.error(f'Failed to delete object {key!r} from storage: {exc}')

    @staticmethod
    def _validate_image(file_bytes: bytes, content_type: str | None) -> None:
        """Validate the image type and size."""
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            msg = f'Unsupported image type: {content_type!r}. Allowed: {sorted(settings.ALLOWED_IMAGE_TYPES)}'
            raise HTTPException(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=msg)
        if len(file_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
            msg = f'Image is too large: {len(file_bytes)} bytes (max {settings.MAX_IMAGE_SIZE_BYTES})'
            raise HTTPException(status_code=HTTP_413_CONTENT_TOO_LARGE, detail=msg)
        if not file_bytes:
            msg = 'Image file is empty'
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=msg)

    @staticmethod
    def _build_image_key(content_type: str) -> str:
        """Build a unique storage key for an image."""
        ext = IMAGE_EXT_BY_CONTENT_TYPE.get(content_type, 'bin')
        return f'products/{uuid4()}.{ext}'
