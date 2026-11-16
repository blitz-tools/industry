"""character skills snapshot (per-character, owner-keyed)

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("skill_id", sa.BigInteger(), primary_key=True),
        # Trained level is what the character has actually trained;
        # active level includes implants/boosters and is what gameplay
        # math sees today.
        sa.Column("trained_skill_level", sa.Integer(), nullable=False),
        sa.Column("active_skill_level", sa.Integer(), nullable=False),
        sa.Column("skillpoints_in_skill", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("skills")
