from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import BaseModel
from src.schemas.category import CategoryDB
from src.utils.custom_types import created_at, updated_at, uuid_pk


class CategoryModel(BaseModel):

    __tablename__ = 'category'

    id: Mapped[uuid_pk]
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    def to_schema(self) -> CategoryDB:
        return CategoryDB(**self.__dict__)
