"""character corporation membership and corporation name cache

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("corporation_id", sa.BigInteger(), nullable=True),
    )
    op.create_table(
        "universe_corporations",
        sa.Column("corporation_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("universe_corporations")
    op.drop_column("characters", "corporation_id")
