"""build plans: snapshot, nodes, materials, jobs, containers (M6)

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The plan of record: a resolved chain snapshotted at export.
    op.create_table(
        "build_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_type_id", sa.BigInteger(), nullable=False),
        sa.Column("target_name", sa.String(length=200), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("corporation_id", sa.BigInteger(), nullable=True),
        sa.Column("participants_json", sa.Text(), nullable=False),
        sa.Column("include_personal_stock", sa.Boolean(), nullable=False),
        sa.Column("facilities_json", sa.Text(), nullable=False),
        sa.Column("me_override", sa.Integer(), nullable=True),
        sa.Column("te_override", sa.Integer(), nullable=True),
        sa.Column("source_query", sa.Text(), nullable=False),
        sa.Column("copy_seconds_per_run", sa.Integer(), nullable=True),
        sa.Column("copy_total_seconds", sa.Integer(), nullable=True),
        sa.Column("copy_facility_json", sa.Text(), nullable=True),
        sa.Column("cycles_json", sa.Text(), nullable=False),
        sa.Column(
            "superseded_by_plan_id",
            sa.Integer(),
            sa.ForeignKey("build_plans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("refreshed_at", sa.DateTime(), nullable=True),
        sa.Column("refresh_error", sa.Text(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("abandoned_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    # The buildable nodes: (plan, phase, type) is the resolver's node
    # unit; measured facts are columns, display blobs are JSON, and the
    # materialized progress columns are written only by the refresh
    # tick.
    op.create_table(
        "build_plan_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("build_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("group_name", sa.String(length=200), nullable=True),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("runs", sa.Integer(), nullable=False),
        sa.Column("jobs", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("blueprint_type_id", sa.BigInteger(), nullable=False),
        sa.Column("blueprint_name", sa.String(length=200), nullable=True),
        sa.Column("products_per_run", sa.Integer(), nullable=False),
        sa.Column("max_production_limit", sa.Integer(), nullable=True),
        sa.Column("is_target", sa.Boolean(), nullable=False),
        sa.Column("me", sa.Integer(), nullable=False),
        sa.Column("te", sa.Integer(), nullable=False),
        sa.Column("has_original", sa.Boolean(), nullable=False),
        sa.Column("bpc_pool_runs", sa.Integer(), nullable=True),
        sa.Column("blueprint_owner_name", sa.String(length=200), nullable=True),
        sa.Column("blueprint_location_name", sa.String(length=200), nullable=True),
        sa.Column("job_seconds", sa.Integer(), nullable=False),
        sa.Column("total_seconds", sa.Integer(), nullable=False),
        sa.Column("install_json", sa.Text(), nullable=False),
        sa.Column("holds_gate", sa.Boolean(), nullable=False),
        sa.Column("skills_json", sa.Text(), nullable=False),
        sa.Column("materials_json", sa.Text(), nullable=False),
        sa.Column("sourcing", sa.String(length=8), nullable=False),
        sa.Column("available_qty", sa.Integer(), nullable=False),
        sa.Column("delivered_qty", sa.Integer(), nullable=False),
        sa.Column("running_qty", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("state_reason", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "plan_id", "phase", "type_id", name="uq_plan_node_phase_type"
        ),
    )
    op.create_index(
        "ix_build_plan_nodes_plan_phase", "build_plan_nodes", ["plan_id", "phase"]
    )
    # The acquisition table: raw terminators plus purchase lines.
    op.create_table(
        "build_plan_materials",
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("build_plans.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("type_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category_name", sa.String(length=200), nullable=True),
        sa.Column("group_name", sa.String(length=200), nullable=True),
        sa.Column("is_purchase_line", sa.Boolean(), nullable=False),
        sa.Column("required_qty", sa.Integer(), nullable=False),
        sa.Column("acquire_via", sa.String(length=64), nullable=True),
        sa.Column("available_qty", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    # Job correlations: one claim per job, globally.
    op.create_table(
        "build_plan_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("build_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "node_id",
            sa.Integer(),
            sa.ForeignKey("build_plan_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_type", sa.String(length=16), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "owner_type", "owner_id", "job_id", name="uq_plan_job_claim"
        ),
    )
    # Station-container scoping (the PR #52 join).
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
    # Custom item names (container labels) from the assets/names pass.
    op.create_table(
        "asset_names",
        sa.Column("owner_type", sa.String(length=16), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), primary_key=True),
        sa.Column("item_id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    # Character loyalty balances (the LP acquisition node's currency).
    op.create_table(
        "character_loyalty",
        sa.Column("character_id", sa.BigInteger(), primary_key=True),
        sa.Column("corporation_id", sa.BigInteger(), primary_key=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # Children before parents.
    op.drop_table("character_loyalty")
    op.drop_table("asset_names")
    op.drop_table("build_plan_containers")
    op.drop_table("build_plan_jobs")
    op.drop_table("build_plan_materials")
    op.drop_index("ix_build_plan_nodes_plan_phase", table_name="build_plan_nodes")
    op.drop_table("build_plan_nodes")
    op.drop_table("build_plans")
