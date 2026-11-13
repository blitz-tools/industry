"""assets, asset_syncs, and universe resolution tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("item_id", sa.BigInteger(), primary_key=True),
        sa.Column("type_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("location_flag", sa.String(length=64), nullable=False),
        sa.Column("location_type", sa.String(length=16), nullable=False),
        sa.Column("parent_location_id", sa.BigInteger(), nullable=False),
        sa.Column("is_blueprint_copy", sa.Boolean(), nullable=False),
        sa.Column("is_singleton", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_assets_owner_parent",
        "assets",
        ["owner_type", "owner_id", "parent_location_id"],
    )

    op.create_table(
        "asset_syncs",
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "universe_types",
        sa.Column("type_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("packaged_volume", sa.Float(), nullable=True),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "universe_locations",
        sa.Column("location_id", sa.BigInteger(), primary_key=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("system_id", sa.BigInteger(), nullable=True),
        sa.Column("constellation_id", sa.BigInteger(), nullable=True),
        sa.Column("region_id", sa.BigInteger(), nullable=True),
        sa.Column("restricted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "universe_regions",
        sa.Column("region_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.add_column(
        "esi_cache",
        sa.Column("headers_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("esi_cache", "headers_json")
    op.drop_table("universe_regions")
    op.drop_table("universe_locations")
    op.drop_table("universe_types")
    op.drop_table("asset_syncs")
    op.drop_index("ix_assets_owner_parent", table_name="assets")
    op.drop_table("assets")
