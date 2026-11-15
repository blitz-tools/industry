"""ORM models."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Index,
    String,
    Text,
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
    (which have their own asset_syncs table): corporation blueprints,
    industry jobs, and future kinds (skills, prices, …)."""

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
