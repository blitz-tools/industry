"""public world-state syncs: cost indices + market prices (M15 slice, M4)

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ESI /industry/systems/ — one row per system × activity string
    # (the activity enum is ESI's own, stored verbatim).
    op.create_table(
        "cost_indices",
        sa.Column("system_id", sa.BigInteger(), primary_key=True),
        sa.Column("activity", sa.String(length=32), primary_key=True),
        sa.Column("cost_index", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    # ESI /markets/prices/ — either price can be absent per type.
    op.create_table(
        "market_prices",
        sa.Column("type_id", sa.BigInteger(), primary_key=True),
        sa.Column("adjusted_price", sa.Float(), nullable=True),
        sa.Column("average_price", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("market_prices")
    op.drop_table("cost_indices")
