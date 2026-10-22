from datetime import datetime

from pydantic import UUID4, BaseModel, Field


class CategoryDB(BaseModel):
    id: UUID4
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    def to_payload(self) -> 'CategoryPayload':
        return CategoryPayload(id=self.id, name=self.name, slug=self.slug)


class CategoryPayload(BaseModel):
    id: UUID4
    name: str
    slug: str


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=100)


class CreateCategoryResponse(BaseModel):
    payload: CategoryPayload


class CategoryResponse(BaseModel):
    payload: CategoryPayload


class CategoriesListResponse(BaseModel):
    payload: list[CategoryPayload]
