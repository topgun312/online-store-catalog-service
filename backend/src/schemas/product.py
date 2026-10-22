from datetime import datetime

from pydantic import UUID4, BaseModel


class ProductDB(BaseModel):
    id: UUID4
    title: str
    image_key: str
    image_content_type: str | None = None
    image_size_bytes: int | None = None
    category_id: UUID4 | None = None
    category_name: str | None = None
    created_at: datetime
    updated_at: datetime

    def to_payload(self, image_url: str) -> 'ProductPayload':
        return ProductPayload(
            id=self.id,
            title=self.title,
            image_url=image_url,
            category_id=self.category_id,
            category_name=self.category_name,
            created_at=self.created_at,
        )


class ProductPayload(BaseModel):
    id: UUID4
    title: str
    image_url: str
    category_id: UUID4 | None = None
    category_name: str | None = None
    created_at: datetime


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int


class CreateProductResponse(BaseModel):
    payload: ProductPayload


class ProductResponse(BaseModel):
    payload: ProductPayload


class ProductsListResponse(BaseModel):
    payload: list[ProductPayload]
    meta: PageMeta
