"""ORM models."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, TimestampMixin, utc_now


class Character(Base, TimestampMixin):
    """An authorized EVE character and its current SSO tokens.

    One row per character, across any number of EVE accounts. Refresh-token
    rotation replaces the token set in place, so tokens live inline. A changed
    owner_hash means the character was transferred and old tokens are void.
    """

    __tablename__ = "characters"

    character_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    access_token_expires_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=utc_now
    )
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    # Current corporation (public data, refreshed on roster renders) —
    # lets the assets page group by corporation without touching ESI.
    corporation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # The single main character (single-user app): defines which
    # corporation the Corporation section targets. The main's tokens
    # authorize the corp-scoped ESI calls.
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class EsiCache(Base, TimestampMixin):
    """Cached ESI response body with its ETag, for If-None-Match revalidation.

    Rows are disposable derived data: pruning or dropping the table never
    loses anything the API can't resupply. Keyed by character (authenticated
    routes serve character-specific content at shared URLs), path, and
    canonical params JSON.
    """

    __tablename__ = "esi_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    character_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    # Persisted response headers (JSON, lowercase names) worth surviving
    # a fresh-window hit — e.g. X-Pages for paginated endpoints.
    headers_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class Asset(Base, TimestampMixin):
    """One asset item (or stack) owned by a character or corporation.

    Snapshot data synced from ESI's assets endpoint, replaced wholesale per
    owner on every successful sync. `parent_location_id` is the top-level
    station/structure the item sits in, resolved in memory at sync time —
    ESI reports contents of ships/containers against the container's
    item_id, and the denormalized parent keeps grouping and pagination as
    plain indexed lookups.
    """

    __tablename__ = "assets"
    __table_args__ = (
        Index(
            "ix_assets_owner_parent",
            "owner_type",
            "owner_id",
            "parent_location_id",
        ),
    )

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    location_flag: Mapped[str] = mapped_column(String(64), nullable=False)
    # "station" | "item" | "solar_system" as reported by ESI for location_id.
    location_type: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_blueprint_copy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_singleton: Mapped[bool] = mapped_column(Boolean, nullable=False)


class AssetSync(Base, TimestampMixin):
    """Last asset-sync outcome per owner, read by the assets page."""

    __tablename__ = "asset_syncs"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # "ok" | "reauth" | "no-scope" | "error"; synced_at is the last attempt.
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=utc_now
    )


class Blueprint(Base, TimestampMixin):
    """A blueprint owned by a character or corporation, synced from ESI's
    blueprints endpoints and replaced wholesale per owner. `runs` is -1
    for originals (unlimited); copies carry their remaining runs. ME/TE
    are ESI's integers (10 reads as 10%)."""

    __tablename__ = "blueprints"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    location_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    location_flag: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    runs: Mapped[int | None] = mapped_column(nullable=True)
    material_efficiency: Mapped[int] = mapped_column(nullable=False)
    time_efficiency: Mapped[int] = mapped_column(nullable=False)


class Skill(Base, TimestampMixin):
    """One trained skill for a character, synced from ESI's skills endpoint
    and replaced wholesale per owner. The planner multiplies these against
    blueprint-required skills (M4 time math) and slot-count ceilings (M9);
    `trained_skill_level` is what was actually trained, while
    `active_skill_level` includes implant/booster effects."""

    __tablename__ = "skills"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    skill_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trained_skill_level: Mapped[int] = mapped_column(nullable=False)
    active_skill_level: Mapped[int] = mapped_column(nullable=False)
    skillpoints_in_skill: Mapped[int] = mapped_column(BigInteger, nullable=False)


class IndustryJob(Base, TimestampMixin):
    """An industry job installed by a member of the owning character or
    corporation, synced from ESI's industry jobs endpoints. The activity
    and blueprint ids are what the planner will join against the SDE
    (M2); the statuses come back from ESI's include_completed view."""

    __tablename__ = "industry_jobs"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    installer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    activity_id: Mapped[int] = mapped_column(nullable=False)
    blueprint_type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    runs: Mapped[int] = mapped_column(nullable=False)
    successful_runs: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    station_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class DataSync(Base, TimestampMixin):
    """Last sync outcome per data kind per owner, for kinds beyond assets
    (which have their own asset_syncs table): corporation blueprints and
    jobs, character blueprints, skills, and jobs, and future kinds
    (prices, …)."""

    __tablename__ = "data_syncs"

    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # "ok" | "no-scope" | "no-roles" | "reauth" | "error"
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=utc_now
    )


class RateLimitObservation(Base, TimestampMixin):
    """One ESI response's rate-control headers, verbatim (M15
    observability): the X-Ratelimit floating-window family and the legacy
    error-limit family, either, neither, or both — same tolerance as
    ESILimiter.observe. Append-only: interpretation (headroom, window
    sums) is the query layer's job (app.esi.telemetry), never the
    write's. `rate_limit` is ESI's compound "max/window" string
    ("150/15m"), stored exactly as sent. Buckets are per group + userID
    (app+character, or source IP for public gets), so owner_id — the
    bucket-key half this app can see — makes per-character bucket
    separation queryable."""

    __tablename__ = "rate_limit_observations"
    __table_args__ = (
        Index("ix_rlo_group_observed", "group", "observed_at"),
        Index("ix_rlo_observed", "observed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=utc_now
    )
    status_code: Mapped[int] = mapped_column(nullable=False)
    # X-Ratelimit-Group, the server's own string; null when the response
    # carried only the legacy error-limit family.
    group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # X-Ratelimit-Limit VERBATIM — compound "150/15m", never an integer
    # on the wire; parsed (or degraded) at read time.
    rate_limit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # X-Ratelimit-Remaining: tokens left in this bucket's window.
    rate_remaining: Mapped[int | None] = mapped_column(nullable=True)
    # X-Ratelimit-Used: tokens consumed by THIS single request (2XX=2,
    # 3XX=1, 4XX=5 with 429 exempt, 5XX=0) — per-request cost, NOT
    # cumulative window usage.
    rate_used: Mapped[int | None] = mapped_column(nullable=True)
    # X-Esi-Error-Limit-Remain / -Reset (reset = seconds-to-roll; the
    # legacy budget is global, not per group).
    error_limit_remain: Mapped[int | None] = mapped_column(nullable=True)
    error_limit_reset: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Client-side correlation, not server-said: which route and which
    # owner caused the request (0 = the public owner).
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)


class SyncRun(Base, TimestampMixin):
    """One sync attempt per kind per owner (M15 observability): the
    append-only history every sync kind writes — public, character, and
    corporation alike, the one stored dataset page-filtered views read
    (the subset rule). data_syncs/asset_syncs keep their last-outcome
    upsert roles for the pages that read them today; this table is the
    durable record with durations. Statuses are stored verbatim in the
    data_syncs/asset_syncs vocabulary ("ok" on success — the in-memory
    SyncOutcome's "synced" normalizes at the record boundary); display
    normalizes, storage never rewrites."""

    __tablename__ = "sync_runs"
    __table_args__ = (
        Index("ix_sync_runs_kind_owner", "kind", "owner_type", "owner_id", "started_at"),
        Index("ix_sync_runs_started", "started_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_type: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Verbatim per writer: "ok" | "error" | "reauth" | "no-scope" |
    # "no-roles".
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # Wall-clock duration of the attempt; null only if measurement
    # itself failed (degrades to "—", never loses the row).
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    item_count: Mapped[int | None] = mapped_column(nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Run start; finish derives (started_at + duration_ms).
    started_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, default=utc_now
    )


class UniverseType(Base, TimestampMixin):
    """Resolved /universe/types/{id}/ data; effectively write-once."""

    __tablename__ = "universe_types"

    type_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    packaged_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class UniverseCorporation(Base, TimestampMixin):
    """Resolved /corporations/{id}/ names; refreshed by roster renders so
    ESI-free pages (assets) can label corporation groups."""

    __tablename__ = "universe_corporations"

    corporation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class UniverseGroup(Base, TimestampMixin):
    """Resolved /universe/groups/{id}/ data: the group's name and the
    category it belongs to. Category names drive the asset type filter."""

    __tablename__ = "universe_groups"

    group_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class UniverseCategory(Base, TimestampMixin):
    """Resolved /universe/categories/{id}/ data; effectively write-once."""

    __tablename__ = "universe_categories"

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class UniverseLocation(Base, TimestampMixin):
    """Resolved stations, structures, and solar systems.

    Structures ESI refuses (403 without docking access) are kept as
    `restricted` rows named "Structure #<id>" and not retried for
    `structure_retry_days` — 403s burn ESI's error-limit budget.
    """

    __tablename__ = "universe_locations"

    location_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # "station" | "structure" | "solar_system"
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    system_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    constellation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    region_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    restricted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class UniverseRegion(Base, TimestampMixin):
    """Resolved region names; shared by many systems."""

    __tablename__ = "universe_regions"

    region_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Structure(Base, TimestampMixin):
    """One physical facility in the M3 registry (user state). Split from
    its registrations so structure-level facts — name, type, system,
    the supercapital capability — never duplicate across a
    multi-registration structure's rows. Security derives from the
    system (ESI security_status, classified at save time) and is stored
    denormalized so planner queries stay join-free; hand-set only when
    no system is chosen. `location_id` ties an imported row back to the
    asset-sync sighting (partial-unique: one registry row per physical
    structure)."""

    __tablename__ = "structures"
    __table_args__ = (
        Index(
            "uq_structures_location",
            "location_id",
            unique=True,
            sqlite_where=text("location_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Key into app.facilities.STRUCTURE_TYPES.
    structure_type: Mapped[str] = mapped_column(String(16), nullable=False)
    system_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Denormalized display copy (ESI names systems at save time).
    system_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # "high" | "low" | "null" — derived from the system, hand-set only
    # without one; None = unknown.
    security_class: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # Capability flag, structure-level (the Hel/Ragnarok pin): gates the
    # final hull job only. Validated on save — nullsec systems only.
    supercapital_assembly: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # The asset-sync sighting this row imported from, when it did.
    location_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class StructureRegistration(Base, TimestampMixin):
    """One structure × activity registration (M3): the rigs, tax, and
    default flag are per-activity dials, so they live here rather than
    on the structure. Exactly one default per activity is enforced by a
    partial unique index; setting a new default demotes the previous
    one in the save path (app/routes/structures.py)."""

    __tablename__ = "structure_registrations"
    __table_args__ = (
        UniqueConstraint("structure_id", "activity", name="uq_structure_activity"),
        Index(
            "uq_registration_default",
            "activity",
            unique=True,
            sqlite_where=text("is_default = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    structure_id: Mapped[int] = mapped_column(
        ForeignKey("structures.id", ondelete="CASCADE"), nullable=False
    )
    # Key into app.facilities.ACTIVITIES.
    activity: Mapped[str] = mapped_column(String(16), nullable=False)
    # Rig tiers: "none" | "t1" | "t2" (keys into facilities.RIG_TIERS).
    me_rig: Mapped[str] = mapped_column(String(4), nullable=False, default="none")
    te_rig: Mapped[str] = mapped_column(String(4), nullable=False, default="none")
    # Industry tax as a fraction (0.005 = 0.5%); None = NPC-set.
    tax_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CostIndex(Base, TimestampMixin):
    """One system's industry cost index for one activity, verbatim from
    ESI's /industry/systems/ payload (M15's public sync band; M4's
    install-cost input). The activity string is ESI's own enum
    ("manufacturing", "reaction", …), stored verbatim — mapping to the
    registry's activity keys is a query-layer concern. Replaced wholesale
    on every sync."""

    __tablename__ = "cost_indices"

    system_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    activity: Mapped[str] = mapped_column(String(32), primary_key=True)
    cost_index: Mapped[float] = mapped_column(Float, nullable=False)


class MarketPrice(Base, TimestampMixin):
    """One type's global adjusted/average price, verbatim from ESI's
    /markets/prices/ payload (M15's public sync band). Either price can
    be absent — ESI omits average_price on ~2k types — so consumers
    (M4's install-cost base value) degrade rather than crash. Replaced
    wholesale on every sync."""

    __tablename__ = "market_prices"

    type_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    adjusted_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_price: Mapped[float | None] = mapped_column(Float, nullable=True)


class BuildPlan(Base, TimestampMixin):
    """One exported build plan (M6): a resolved chain snapshotted as the
    plan of record. Re-running the planner makes a NEW plan — snapshot
    columns are never mutated after export; only status, timestamps, and
    the materialized node columns move. Participant ids and facility
    facts are pinned at export (roster/registry changes never move an
    active plan); `source_query` is the planner URL the plan came from,
    the Re-run button's target. Progress refreshes are recorded on the
    row itself (refreshed_at/refresh_error) rather than in data_syncs —
    that table is for ESI syncs."""

    __tablename__ = "build_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Denormalized so the plans list renders without SDE joins.
    target_name: Mapped[str] = mapped_column(String(200), nullable=False)
    units: Mapped[int] = mapped_column(nullable=False)
    # "draft" | "active" | "complete" | "abandoned"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    # The main's corporation at export — the office-pool key.
    corporation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Resolved participants at export (JSON rows: ids plus the time
    # readouts the draft detail renders) — roster changes never move a
    # plan.
    participants_json: Mapped[str] = mapped_column(Text, nullable=False)
    # The Material sources selection at export: null = the corp-side
    # default (every office hangar and container — personal hangars
    # out); a JSON list = the explicit source refs, the present-even-
    # empty sentinel included. Subsumes the old build_plan_containers
    # table: a container is one source kind among the refs.
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Activity key → pinned registration facts (JSON; null values where
    # no facility is registered for the activity).
    facilities_json: Mapped[str] = mapped_column(Text, nullable=False)
    me_override: Mapped[int | None] = mapped_column(nullable=True)
    te_override: Mapped[int | None] = mapped_column(nullable=True)
    # The /planner/plan query string the plan was exported from.
    source_query: Mapped[str] = mapped_column(Text, nullable=False)
    copy_seconds_per_run: Mapped[int | None] = mapped_column(nullable=True)
    copy_total_seconds: Mapped[int | None] = mapped_column(nullable=True)
    # The pinned copying registration (JSON, one facilities_json entry).
    copy_facility_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ChainResult.cycles rendered shape (JSON; display-only).
    cycles_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Set on the plan a Re-run fork replaced (the only auto-abandon
    # path; fresh exports never touch sibling plans).
    superseded_by_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("build_plans.id", ondelete="SET NULL"), nullable=True
    )
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    refresh_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    abandoned_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)


class BuildPlanNode(Base, TimestampMixin):
    """One buildable node of an exported plan (M6) — the chain resolver's
    (type, phase) unit. Everything the detail page renders is snapshotted
    here (columns for measured facts, JSON for display blobs) so pages
    stay DB-pure; the materialized columns (available/delivered/running/
    state) are written only by the refresh tick, never recomputed on
    render. `sourcing` is the one mutable snapshot column — the
    Purchase⇄Build marking amends it in place."""

    __tablename__ = "build_plan_nodes"
    __table_args__ = (
        UniqueConstraint("plan_id", "phase", "type_id", name="uq_plan_node_phase_type"),
        Index("ix_build_plan_nodes_plan_phase", "plan_id", "phase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("build_plans.id", ondelete="CASCADE"), nullable=False
    )
    phase: Mapped[int] = mapped_column(nullable=False)
    type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # invGroups name — the phase display-name material.
    group_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    qty: Mapped[int] = mapped_column(nullable=False)
    runs: Mapped[int] = mapped_column(nullable=False)
    jobs: Mapped[int] = mapped_column(nullable=False)
    activity_id: Mapped[int] = mapped_column(nullable=False)
    blueprint_type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    blueprint_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    products_per_run: Mapped[int] = mapped_column(nullable=False)
    max_production_limit: Mapped[int | None] = mapped_column(nullable=True)
    is_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Calc snapshot (export-time blueprint selection and facility math).
    me: Mapped[int] = mapped_column(nullable=False)
    te: Mapped[int] = mapped_column(nullable=False)
    has_original: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bpc_pool_runs: Mapped[int | None] = mapped_column(nullable=True)
    blueprint_owner_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    blueprint_location_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    job_seconds: Mapped[int] = mapped_column(nullable=False)
    total_seconds: Mapped[int] = mapped_column(nullable=False)
    install_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Export-time skill-gate fact (the plan is a pinned document — a
    # later-trained skill doesn't clear it until Re-run).
    holds_gate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # [{skill_id, name, level}] — feeds the roster eligibility flag, M9.
    skills_json: Mapped[str] = mapped_column(Text, nullable=False)
    # The PlanMaterial list — purchase-marking's raw-math input and the
    # multibuy source.
    materials_json: Mapped[str] = mapped_column(Text, nullable=False)
    # "build" | "purchase" — the marking, amended in place.
    sourcing: Mapped[str] = mapped_column(String(8), nullable=False, default="build")
    # Materialized by the refresh tick (never on render).
    available_qty: Mapped[int] = mapped_column(nullable=False, default=0)
    delivered_qty: Mapped[int] = mapped_column(nullable=False, default=0)
    running_qty: Mapped[int] = mapped_column(nullable=False, default=0)
    # "missing" | "ready" | "running" | "deliver" | "complete"
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="missing")
    state_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)


class BuildPlanMaterial(Base, TimestampMixin):
    """One acquisition line of an exported plan (M6): a raw terminator of
    the chain, or a purchase line added for a node marked Purchase.
    `required_qty` is amended in place by marking — recomputed from the
    nodes' materials_json (snapshot total minus purchase-marked demands),
    so the amend is lossless and un-marking is symmetric."""

    __tablename__ = "build_plan_materials"

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("build_plans.id", ondelete="CASCADE"), primary_key=True
    )
    type_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # True on rows added for purchase-marked nodes (the commodity being
    # bought, not built).
    is_purchase_line: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    required_qty: Mapped[int] = mapped_column(nullable=False)
    # The curated acquire-via label, snapshotted at export.
    acquire_via: Mapped[str | None] = mapped_column(String(64), nullable=True)
    available_qty: Mapped[int] = mapped_column(nullable=False, default=0)


class BuildPlanJob(Base, TimestampMixin):
    """One industry-job-to-plan-node correlation (M6), written by the
    refresh tick from the heuristic matcher (blueprint + activity +
    location; the endpoint carries no plan reference). Rewritten
    wholesale per tick. The unique constraint on the industry_jobs key
    is global — one job claims into at most one plan across all plans
    (the concurrent-plan false-positive guard)."""

    __tablename__ = "build_plan_jobs"
    __table_args__ = (
        UniqueConstraint("owner_type", "owner_id", "job_id", name="uq_plan_job_claim"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("build_plans.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("build_plan_nodes.id", ondelete="CASCADE"), nullable=False
    )
    owner_type: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    job_id: Mapped[int] = mapped_column(BigInteger, nullable=False)


class AssetName(Base, TimestampMixin):
    """A custom item name from ESI's assets/names endpoint (M6's
    container bucketing): the in-game label on a station container or
    other renamed item. Written by a best-effort pass after the asset
    snapshot replace and persisted independently of the wholesale-
    replaced assets, so a failed name fetch keeps the previous names
    (a batch containing any never-named id fails wholesale with 404 —
    the sync falls back to per-item requests)."""

    __tablename__ = "asset_names"

    owner_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class CharacterLoyalty(Base, TimestampMixin):
    """One character's loyalty-point balance with one corporation,
    synced from ESI's loyalty endpoint and replaced wholesale per
    character (M6's LP acquisition node — currency balances; the offer
    variants are a curated pin until M15 syncs the lpstore dataset)."""

    __tablename__ = "character_loyalty"

    character_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    corporation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    points: Mapped[int] = mapped_column(nullable=False)

