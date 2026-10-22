from typing import TYPE_CHECKING

from fastapi import HTTPException
from pydantic import UUID4
from starlette.status import HTTP_409_CONFLICT

from src.schemas.category import CategoryPayload, CreateCategoryRequest
from src.utils.constans import CATEGORY_ALREADY_EXISTS_MSG, CATEGORY_NOT_FOUND_MSG
from src.utils.service import BaseService, transaction_mode

if TYPE_CHECKING:
    from src.models import CategoryModel


def build_slug(name: str) -> str:
    """Build a URL-friendly slug from a name."""
    return name.strip().lower().replace(' ', '-')


class CategoryService(BaseService):
    """Business logic for catalog categories."""

    _repo: str = 'category'

    @transaction_mode
    async def create_category(self, category: CreateCategoryRequest) -> CategoryPayload:
        """Create a category, rejecting duplicates by name or slug."""
        slug = build_slug(category.slug or category.name)
        existing: CategoryModel | None = await self.uow.category.get_by_filter_one_or_none(slug=slug)
        if existing is None:
            existing = await self.uow.category.get_by_filter_one_or_none(name=category.name)
        if existing is not None:
            raise HTTPException(status_code=HTTP_409_CONFLICT, detail=CATEGORY_ALREADY_EXISTS_MSG)

        created: CategoryModel = await self.uow.category.add_one_and_get_obj(name=category.name, slug=slug)
        return created.to_schema().to_payload()

    @transaction_mode
    async def get_category_by_id(self, category_id: UUID4) -> CategoryPayload:
        """Get a category by ID."""
        category: CategoryModel | None = await self.uow.category.get_by_filter_one_or_none(id=category_id)
        self.check_existence(obj=category, details=CATEGORY_NOT_FOUND_MSG)
        return category.to_schema().to_payload()

    @transaction_mode
    async def get_categories(self) -> list[CategoryPayload]:
        """Get all categories ordered by name."""
        categories: list[CategoryModel] = await self.uow.category.get_categories_ordered()
        return [category.to_schema().to_payload() for category in categories]
