from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import BaseModel
from src.models.category import CategoryModel
from src.schemas.product import ProductDB
from src.utils.custom_types import created_at, updated_at, uuid_pk


class ProductModel(BaseModel):

    __tablename__ = 'product'

    id: Mapped[uuid_pk]
    title: Mapped[str] = mapped_column(String(255))
    image_key: Mapped[str] = mapped_column(String(512))
    image_content_type: Mapped[str | None] = mapped_column(String(100), default=None)
    image_size_bytes: Mapped[int | None] = mapped_column(Integer, default=None)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('category.id', ondelete='SET NULL'),
        default=None,
        nullable=True,
    )
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    category: Mapped[CategoryModel | None] = relationship('CategoryModel', lazy='selectin')

    def to_schema(self) -> ProductDB:
        return ProductDB(
            id=self.id,
            title=self.title,
            image_key=self.image_key,
            image_content_type=self.image_content_type,
            image_size_bytes=self.image_size_bytes,
            category_id=self.category_id,
            category_name=self.category.name if self.category else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
