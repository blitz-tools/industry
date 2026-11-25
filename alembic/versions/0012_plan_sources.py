"""build plans: the sources snapshot (M6 export PR)

Replaces 0011's include_personal_stock bool — superseded the same round
by the Material sources selector (PR #93): the coverage pool is an
explicit source set, not a personal-stock toggle. sources_json holds the
selection (null = the corp-side default; a JSON list = the explicit
source refs). build_plan_containers folds into it: a container is one
source kind among the refs, so the table's join is the read's, not the
schema's.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("build_plans", sa.Column("sources_json", sa.Text(), nullable=True))
    # The bool was never written (PR #92's ps param was superseded before
    # the export shipped), so nothing is lost in the drop.
    with op.batch_alter_table("build_plans") as batch:
        batch.drop_column("include_personal_stock")
    op.drop_table("build_plan_containers")


def downgrade() -> None:
    # Children before parents; the bool returns with a server default so
    # the NOT NULL holds on the (empty-of-meaning) existing rows.
    op.create_table(
        "build_plan_containers",
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("build_plans.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("item_id", sa.BigInteger(), primary_key=True),
        sa.Column("owner_type", sa.String(length=16), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    with op.batch_alter_table("build_plans") as batch:
        batch.add_column(
            sa.Column(
                "include_personal_stock",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
    op.drop_column("build_plans", "sources_json")
