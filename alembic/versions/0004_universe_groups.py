"""universe groups and categories for the asset type filter

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "universe_groups",
        sa.Column("group_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "universe_categories",
        sa.Column("category_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("universe_categories")
    op.drop_table("universe_groups")
