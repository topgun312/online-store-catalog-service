from fastapi import APIRouter, Depends
from pydantic import UUID4
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from src.api.v1.services.category import CategoryService
from src.schemas.category import (
    CategoriesListResponse,
    CategoryPayload,
    CategoryResponse,
    CreateCategoryRequest,
    CreateCategoryResponse,
)

router = APIRouter(prefix='/category')


@router.post(
    path='/',
    status_code=HTTP_201_CREATED,
)
async def create_category(
    category: CreateCategoryRequest,
    service: CategoryService = Depends(),
) -> CreateCategoryResponse:
    """Create a new category."""
    created: CategoryPayload = await service.create_category(category)
    return CreateCategoryResponse(payload=created)


@router.get(
    path='/',
    status_code=HTTP_200_OK,
)
async def get_categories(
    service: CategoryService = Depends(),
) -> CategoriesListResponse:
    """Get all categories ordered by name."""
    categories = await service.get_categories()
    return CategoriesListResponse(payload=categories)


@router.get(
    path='/{category_id}',
    status_code=HTTP_200_OK,
)
async def get_category(
    category_id: UUID4,
    service: CategoryService = Depends(),
) -> CategoryResponse:
    """Get a category by ID."""
    category: CategoryPayload = await service.get_category_by_id(category_id)
    return CategoryResponse(payload=category)
