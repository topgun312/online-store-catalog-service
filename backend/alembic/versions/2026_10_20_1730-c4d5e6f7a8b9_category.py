"""category + product.category_id

Revision ID: c4d5e6f7a8b9
Revises: 7f3c9a2b1e84
Create Date: 2026-10-20 17:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "7f3c9a2b1e84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# seed categories (fixed ids so that integrations can reference them)
SEED_CATEGORIES = [
    {"id": "0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e", "name": "Электроника", "slug": "electronics"},
    {"id": "1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f", "name": "Одежда", "slug": "clothing"},
    {"id": "2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a", "name": "Другое", "slug": "other"},
]


def upgrade() -> None:
    op.create_table(
        "category",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.add_column("product", sa.Column("category_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_product_category_id",
        "product",
        "category",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    category_table = sa.table(
        "category",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
    )
    op.bulk_insert(category_table, SEED_CATEGORIES)


def downgrade() -> None:
    op.drop_constraint("fk_product_category_id", "product", type_="foreignkey")
    op.drop_column("product", "category_id")
    op.drop_table("category")
