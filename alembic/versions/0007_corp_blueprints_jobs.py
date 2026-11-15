"""corporation blueprints, industry jobs, and per-kind sync status

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blueprints",
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("item_id", sa.BigInteger(), primary_key=True),
        sa.Column("type_id", sa.BigInteger(), nullable=False),
        sa.Column("location_id", sa.BigInteger(), nullable=False),
        sa.Column("location_flag", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        # -1 marks an original (unlimited runs); copies carry their runs.
        sa.Column("runs", sa.Integer(), nullable=True),
        sa.Column("material_efficiency", sa.Integer(), nullable=False),
        sa.Column("time_efficiency", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "industry_jobs",
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("job_id", sa.BigInteger(), primary_key=True),
        sa.Column("installer_id", sa.BigInteger(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("blueprint_type_id", sa.BigInteger(), nullable=False),
        sa.Column("runs", sa.Integer(), nullable=False),
        sa.Column("successful_runs", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("completed_date", sa.DateTime(), nullable=True),
        sa.Column("station_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "data_syncs",
        sa.Column("kind", sa.String(length=32), primary_key=True),
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("data_syncs")
    op.drop_table("industry_jobs")
    op.drop_table("blueprints")
