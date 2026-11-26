"""observability telemetry: rate-limit observations + sync run history (M15)

The telemetry-first slice of M15's completion plan: per-response ESI
rate-control headers mirrored verbatim (both header families, either can
be absent per response), and one append-only run history every sync kind
— public, character, corporation — writes status/duration into (the one
stored dataset the Admin > Observability page and page-filtered subset
views read). data_syncs/asset_syncs keep their last-outcome upsert
roles; these tables are the durable records.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-25

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # One row per ESI response carrying any rate-control header. The
    # limit column is ESI's compound "max/window" string ("150/15m"),
    # stored exactly as sent — parsing is the query layer's job.
    op.create_table(
        "rate_limit_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        # X-Ratelimit-Group verbatim; null when only the legacy
        # error-limit family was present.
        sa.Column("group", sa.String(length=64), nullable=True),
        sa.Column("rate_limit", sa.String(length=32), nullable=True),
        # X-Ratelimit-Remaining: tokens left in this bucket's window.
        sa.Column("rate_remaining", sa.Integer(), nullable=True),
        # X-Ratelimit-Used: tokens consumed by THIS single request —
        # per-request cost, not cumulative window usage.
        sa.Column("rate_used", sa.Integer(), nullable=True),
        # Legacy family: Remain is the global error budget, Reset is
        # seconds-to-roll.
        sa.Column("error_limit_remain", sa.Integer(), nullable=True),
        sa.Column("error_limit_reset", sa.Float(), nullable=True),
        # Client-side correlation: the route and owner (0 = public).
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_rlo_group_observed", "rate_limit_observations", ["group", "observed_at"]
    )
    op.create_index("ix_rlo_observed", "rate_limit_observations", ["observed_at"])
    # One row per sync attempt per kind per owner — append-only history
    # (data_syncs stays the last-outcome upsert).
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("owner_type", sa.String(length=16), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        # Verbatim per writer: ok | error | reauth | no-scope | no-roles
        # — display normalizes, storage never rewrites.
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("item_count", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        # Run start; finish derives (started_at + duration_ms).
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_sync_runs_kind_owner",
        "sync_runs",
        ["kind", "owner_type", "owner_id", "started_at"],
    )
    op.create_index("ix_sync_runs_started", "sync_runs", ["started_at"])


def downgrade() -> None:
    # Indexes before tables, sync_runs before rate_limit_observations
    # (reverse creation order; no cross-table keys exist).
    op.drop_index("ix_sync_runs_started", table_name="sync_runs")
    op.drop_index("ix_sync_runs_kind_owner", table_name="sync_runs")
    op.drop_table("sync_runs")
    op.drop_index("ix_rlo_observed", table_name="rate_limit_observations")
    op.drop_index("ix_rlo_group_observed", table_name="rate_limit_observations")
    op.drop_table("rate_limit_observations")
