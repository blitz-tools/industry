"""structure registry: structures + per-activity registrations (M3)

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "structures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("structure_type", sa.String(length=16), nullable=False),
        sa.Column("system_id", sa.BigInteger(), nullable=True),
        sa.Column("system_name", sa.String(length=200), nullable=True),
        # high | low | null; derived from the system, hand-set without one.
        sa.Column("security_class", sa.String(length=8), nullable=True),
        sa.Column("supercapital_assembly", sa.Boolean(), nullable=False),
        # The asset-sync sighting an imported row came from.
        sa.Column("location_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    # One registry row per physical structure.
    op.create_index(
        "uq_structures_location",
        "structures",
        ["location_id"],
        unique=True,
        sqlite_where=sa.text("location_id IS NOT NULL"),
    )
    op.create_table(
        "structure_registrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "structure_id",
            sa.Integer(),
            sa.ForeignKey("structures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("activity", sa.String(length=16), nullable=False),
        sa.Column("me_rig", sa.String(length=4), nullable=False),
        sa.Column("te_rig", sa.String(length=4), nullable=False),
        # Industry tax as a fraction (0.005 = 0.5%); null = NPC-set.
        sa.Column("tax_rate", sa.Float(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("structure_id", "activity", name="uq_structure_activity"),
    )
    # Exactly one default per activity.
    op.create_index(
        "uq_registration_default",
        "structure_registrations",
        ["activity"],
        unique=True,
        sqlite_where=sa.text("is_default = 1"),
    )


def downgrade() -> None:
    op.drop_index("uq_registration_default", table_name="structure_registrations")
    op.drop_table("structure_registrations")
    op.drop_index("uq_structures_location", table_name="structures")
    op.drop_table("structures")
