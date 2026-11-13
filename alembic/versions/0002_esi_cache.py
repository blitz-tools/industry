"""esi_cache table for ETag-cached ESI responses

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "esi_cache",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("params_json", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("etag", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_modified", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_esi_cache_character_id", "esi_cache", ["character_id"])


def downgrade() -> None:
    op.drop_index("ix_esi_cache_character_id", table_name="esi_cache")
    op.drop_table("esi_cache")
