"""Asset query/view layer: pure DB reads for the assets page.

Page renders never touch ESI — the background sync owns all fetching, and
this module turns the stored snapshot into the system → structure view
with per-type row aggregation. Everything filters by owner id list so the
character multi-selector (and, later, corporation views) compose freely.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import utc_now
from .esi.assets import OWNER_CHARACTER
from .models import (
    Asset,
    AssetSync,
    Character,
    UniverseCategory,
    UniverseGroup,
    UniverseLocation,
    UniverseRegion,
    UniverseType,
)

UNKNOWN_SYSTEM = "Unknown system"


@dataclass(frozen=True)
class CategoryBucket:
    """One asset type filter option: a friendly label over a set of EVE
    universe category names (as ESI reports them). An empty category set is
    the catch-all bucket matching everything no named bucket claims."""

    key: str  # URL parameter value
    label: str
    categories: tuple[str, ...]


# ESI's name for the blueprint category; blueprint icons need the
# imageserver's dedicated bp/bpc renders (see AssetRow.icon_kind).
BLUEPRINT_CATEGORY = "Blueprint"

# Categories the imageserver has no images for at all (probed 2026-11:
# every type variation 404s). Rows here render a placeholder instead of a
# broken image. Page renders can't probe the imageserver themselves — the
# no-ESI purity rule — so this list is the record of what it serves.
ICONLESS_CATEGORIES = frozenset({"SKINs", "Ancient Relics"})


CATEGORY_BUCKETS: tuple[CategoryBucket, ...] = (
    CategoryBucket(
        "materials",
        "Materials",
        (
            "Material",  # minerals, ice products, moon materials, fuel
            "Asteroid",  # ore
            "Commodity",
            "Planetary Industry",
            "Planetary Resources",
            "Planetary Commodities",
        ),
    ),
    CategoryBucket("reactions", "Reactions", ("Reaction",)),
    CategoryBucket("blueprints", "Blueprints", (BLUEPRINT_CATEGORY,)),
    CategoryBucket("ships", "Ships", ("Ship",)),
    CategoryBucket("modules", "Modules", ("Module", "Charge", "Subsystem")),
    CategoryBucket("drones", "Drones & Fighters", ("Drone", "Fighter")),
    CategoryBucket("skills", "Skills", ("Skill",)),
    CategoryBucket("implants", "Implants", ("Implant",)),
    CategoryBucket(
        "structures",
        "Structures",
        ("Structure", "Structure Module", "Starbase", "Deployable"),
    ),
    CategoryBucket("other", "Other", ()),
)

BUCKETS_BY_KEY = {bucket.key: bucket for bucket in CATEGORY_BUCKETS}
# Category name → the bucket that claims it; unclaimed names (and
# unresolved types) belong to "Other".
BUCKET_BY_CATEGORY = {
    name: bucket.key for bucket in CATEGORY_BUCKETS for name in bucket.categories
}
CLAIMED_CATEGORIES = frozenset(BUCKET_BY_CATEGORY)


@dataclass
class StructurePanel:
    location_id: int
    name: str  # resolved name, "Structure #<id>", or "Location #<id>"
    kind: str
    item_count: int
    restricted: bool


@dataclass
class SystemGroup:
    system_id: int | None  # None → the Unknown-system group, sorted last
    name: str
    region_id: int | None
    region_name: str | None
    structures: list[StructurePanel] = field(default_factory=list)


@dataclass
class RegionOption:
    region_id: int
    name: str


@dataclass
class CategoryOption:
    key: str  # bucket key (URL parameter value)
    label: str


@dataclass
class AssetView:
    groups: list[SystemGroup]
    # Region options from the character-filtered (but region-unfiltered)
    # data, so the dropdown stays stable under its own filter.
    regions: list[RegionOption]
    # Category options from the character-filtered (but category-unfiltered)
    # data — buckets that actually have assets, same stability rule.
    categories: list[CategoryOption]
    total_items: int


@dataclass
class AssetRow:
    owner_id: int
    owner_name: str
    type_id: int
    type_name: str | None
    quantity: int
    volume_total: float | None  # unit volume × summed quantity
    location_flag: str
    is_blueprint_copy: bool
    # Imageserver path segment ("icon", "bp", "bpc"), or None when the
    # type's category has no images at all: blueprints 400 on the plain
    # icon endpoint, and SKINs/Ancient Relics have no variations.
    icon_kind: str | None = "icon"


@dataclass
class CharacterSyncStatus:
    character_id: int
    name: str
    status: str | None  # None = never synced
    detail: str | None


async def character_sync_status(
    db: AsyncSession, characters: Sequence[Character]
) -> tuple[list[CharacterSyncStatus], datetime | None]:
    """Per-character sync outcome plus the global last-attempt time."""
    syncs = {
        row.owner_id: row
        for row in (
            await db.execute(
                select(AssetSync).where(AssetSync.owner_type == OWNER_CHARACTER)
            )
        ).scalars()
    }
    statuses = [
        CharacterSyncStatus(
            character_id=character.character_id,
            name=character.name,
            status=syncs[character.character_id].status
            if character.character_id in syncs
            else None,
            detail=syncs[character.character_id].detail
            if character.character_id in syncs
            else None,
        )
        for character in characters
    ]
    last = max((row.synced_at for row in syncs.values()), default=None)
    return statuses, last


def parse_chars(raw: list[str], valid: Sequence[Character]) -> list[int] | None:
    """Parse ?chars= — accepts comma-joined and repeated-key forms. None
    means "all characters" (absent, empty, or nothing valid)."""
    valid_ids = {character.character_id for character in valid}
    selected: set[int] = set()
    for chunk in raw:
        for token in chunk.split(","):
            token = token.strip()
            if token.lstrip("-").isdigit():
                selected.add(int(token))
    selected &= valid_ids
    return sorted(selected) or None


def parse_region(raw: str | None) -> int | None:
    """Parse ?region= to an int; None for absent or garbage."""
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_category(raw: str | None) -> str | None:
    """Parse ?category= to a bucket key; None for absent or unknown."""
    if raw is None:
        return None
    return raw if raw in BUCKETS_BY_KEY else None


def parse_sort(raw: str | None) -> str | None:
    """Parse ?sort= to a sortable column key; None for absent or unknown."""
    if raw is None:
        return None
    return raw if raw in SORT_KEYS else None


def parse_direction(raw: str | None) -> str | None:
    """Parse ?dir=; only "asc" and "desc" are meaningful."""
    return raw if raw in ("asc", "desc") else None


# Sortable asset-table columns: URL key and header label.
SORTABLE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("type", "Type"),
    ("character", "Character"),
    ("quantity", "Qty"),
    ("volume", "Volume"),
    ("flag", "Flag"),
)
SORT_KEYS = frozenset(key for key, _ in SORTABLE_COLUMNS)


@dataclass(frozen=True)
class SortHeader:
    """One clickable table header: `url` applies this sort (the opposite
    direction when the column is already active)."""

    key: str
    label: str
    url: str
    active: bool
    descending: bool  # current direction, when active


def sort_headers(
    location_id: int,
    *,
    current_sort: str | None,
    current_dir: str | None,
    chars: list[int] | None,
    category: str | None,
) -> list[SortHeader]:
    headers = []
    for key, label in SORTABLE_COLUMNS:
        active = key == current_sort
        # Active columns toggle direction; inactive ones start ascending.
        next_dir = ("desc" if current_dir == "asc" else "asc") if active else "asc"
        params = [("sort", key), ("dir", next_dir)]
        if chars:
            params.append(("chars", ",".join(str(c) for c in chars)))
        if category:
            params.append(("category", category))
        headers.append(
            SortHeader(
                key=key,
                label=label,
                url=f"/assets/structure/{location_id}?{urlencode(params)}",
                active=active,
                descending=current_dir == "desc",
            )
        )
    return headers


def carry_query(
    *,
    chars: list[int] | None,
    category: str | None,
    sort: str | None,
    direction: str | None,
) -> str:
    """Query string of fragment params pagination links re-apply (i.e.
    everything except the page they themselves set)."""
    params = []
    if chars:
        params.append(("chars", ",".join(str(c) for c in chars)))
    if category:
        params.append(("category", category))
    if sort:
        params.append(("sort", sort))
        params.append(("dir", direction or "asc"))
    return urlencode(params)


def _category_filter_joins(query, *, with_type: bool):
    """Outer-join the type → group → category chain category filters walk.
    Cardinality is 1:1 at every hop (PK lookups), so the joins never
    multiply rows; unresolved links read as NULL."""
    if with_type:
        query = query.outerjoin(UniverseType, UniverseType.type_id == Asset.type_id)
    return (
        query.outerjoin(UniverseGroup, UniverseGroup.group_id == UniverseType.group_id)
        .outerjoin(
            UniverseCategory, UniverseCategory.category_id == UniverseGroup.category_id
        )
    )


def category_condition(bucket: CategoryBucket):
    """SQL condition on Asset rows for one bucket."""
    if bucket.categories:
        return UniverseCategory.name.in_(bucket.categories)
    # "Other": anything a named bucket does not claim, or that could not be
    # resolved at all. The explicit NULL checks keep SQL's three-valued
    # logic from silently dropping unresolved rows.
    return or_(
        UniverseType.type_id.is_(None),
        UniverseGroup.group_id.is_(None),
        UniverseGroup.category_id.is_(None),
        UniverseCategory.category_id.is_(None),
        UniverseCategory.name.is_(None),
        ~UniverseCategory.name.in_(CLAIMED_CATEGORIES),
    )


def _icon_kind(category_name: str | None, is_blueprint_copy: bool) -> str | None:
    """Imageserver path segment for a row's type icon, or None when the
    type's category has no images at all (see ICONLESS_CATEGORIES)."""
    if category_name in ICONLESS_CATEGORIES:
        return None
    if is_blueprint_copy:
        return "bpc"
    if category_name == BLUEPRINT_CATEGORY:
        return "bp"
    return "icon"


def _order_keys(sort: str | None, direction: str | None) -> list:
    """ORDER BY keys for structure rows: the requested column (when `sort`
    names one) followed by the default owner-then-type order, so ties and
    unsorted pages paginate deterministically."""
    type_name = func.coalesce(UniverseType.name, "#" + cast(Asset.type_id, String))
    primary = {
        "type": type_name,
        "character": Character.name,
        "quantity": func.sum(Asset.quantity),
        "volume": func.sum(Asset.quantity) * UniverseType.volume,
        "flag": func.max(Asset.location_flag),
    }.get(sort)
    keys = []
    if primary is not None:
        key = primary.desc() if direction == "desc" else primary.asc()
        if sort == "volume":
            key = key.nulls_last()  # unknown volumes sink, either direction
        keys.append(key)
    keys.extend([Character.name, type_name])
    return keys


def humanize_sync_age(synced_at: datetime | None, *, now: datetime | None = None) -> str:
    """Coarse last-sync wording: never minutes — under an hour reads as
    'less than an hour ago', then hours, then days."""
    if synced_at is None:
        return "Data not synced yet"
    age = (now or utc_now()) - synced_at
    if age < timedelta(hours=1):
        return "Data sync'd less than an hour ago"
    hours = age // timedelta(hours=1)
    if hours < 24:
        return f"Data sync'd {hours} hour{'s' if hours != 1 else ''} ago"
    days = age // timedelta(days=1)
    return f"Data sync'd {days} day{'s' if days != 1 else ''} ago"


async def system_groups(
    db: AsyncSession,
    *,
    owner_ids: list[int] | None,
    category: str | None = None,
) -> AssetView:
    """System → structure view of the character asset snapshot, filtered to
    the selected owners (None = all) and category bucket (None = all)."""
    conditions = [Asset.owner_type == OWNER_CHARACTER]
    if owner_ids is not None:
        conditions.append(Asset.owner_id.in_(owner_ids))

    # Category options: asset counts per resolved category name over the
    # owner-filtered (but category-unfiltered) data, so the dropdown only
    # offers buckets that actually have assets and stays stable under its
    # own filter — the same rule as the region options.
    name_expr = func.coalesce(UniverseCategory.name, "")
    rows_by_name = (
        await db.execute(
            _category_filter_joins(
                select(name_expr, func.count()).select_from(Asset),
                with_type=True,
            )
            .where(*conditions)
            .group_by(name_expr)
        )
    ).all()
    present = {BUCKET_BY_CATEGORY.get(name, "other") for name, _ in rows_by_name}
    category_options = [
        CategoryOption(bucket.key, bucket.label)
        for bucket in CATEGORY_BUCKETS
        if bucket.key in present
    ]

    counts_conditions = list(conditions)
    if category is not None:
        counts_conditions.append(category_condition(BUCKETS_BY_KEY[category]))
    counts_query = select(
        Asset.parent_location_id,
        func.count(),
        # Each top-level location has at least one direct
        # (non-container) child row that names its kind.
        func.max(
            case((Asset.location_type != "item", Asset.location_type))
        ),
    ).where(*counts_conditions)
    if category is not None:
        counts_query = _category_filter_joins(counts_query, with_type=True)
    counts = (
        await db.execute(counts_query.group_by(Asset.parent_location_id))
    ).all()

    if not counts:
        return AssetView(
            groups=[], regions=[], categories=category_options, total_items=0
        )

    location_rows = (
        (
            await db.execute(
                select(UniverseLocation).where(
                    UniverseLocation.location_id.in_([c[0] for c in counts])
                )
            )
        )
        .scalars()
        .all()
    )
    locations = {row.location_id: row for row in location_rows}

    # Collect every system referenced, then load their names in one pass.
    system_ids = {
        row.system_id
        for row in locations.values()
        if row.system_id is not None and row.kind != "solar_system"
    }
    system_ids |= {
        parent_id
        for parent_id, _, kind in counts
        if kind == "solar_system"  # assets located directly in a system
    }
    system_rows = (
        (
            await db.execute(
                select(UniverseLocation).where(
                    UniverseLocation.location_id.in_(system_ids)
                )
            )
        )
        .scalars()
        .all()
        if system_ids
        else []
    )
    systems = {row.location_id: row for row in system_rows}
    region_names = {
        row.region_id: row.name
        for row in (
            (
                await db.execute(
                    select(UniverseRegion).where(
                        UniverseRegion.region_id.in_(
                            {
                                row.region_id
                                for row in system_rows
                                if row.region_id is not None
                            }
                        )
                    )
                )
            )
            .scalars()
            .all()
        )
    }

    groups: dict[int | None, SystemGroup] = {}
    for parent_id, item_count, kind in counts:
        row = locations.get(parent_id)
        if row is not None:
            name = row.name or f"Location #{parent_id}"
            restricted = row.restricted
            system_id = row.system_id
            resolved_kind = row.kind
        else:
            name = f"Location #{parent_id}"
            restricted = False
            system_id = None
            resolved_kind = kind or "unknown"
        if resolved_kind == "solar_system":
            system_id = parent_id
        system = systems.get(system_id) if system_id is not None else None
        group = groups.get(system_id)
        if group is None:
            group = groups[system_id] = SystemGroup(
                system_id=system_id,
                name=system.name if system is not None and system.name else (
                    f"System #{system_id}" if system_id is not None else UNKNOWN_SYSTEM
                ),
                region_id=system.region_id if system is not None else None,
                region_name=(
                    region_names.get(system.region_id)
                    if system is not None and system.region_id is not None
                    else None
                ),
            )
        group.structures.append(
            StructurePanel(
                location_id=parent_id,
                name=name,
                kind=resolved_kind,
                item_count=item_count,
                restricted=restricted,
            )
        )

    ordered = sorted(
        groups.values(),
        key=lambda g: (g.system_id is None, g.name.lower()),
    )
    for group in ordered:
        group.structures.sort(key=lambda s: s.name.lower())

    region_options: dict[int, RegionOption] = {}
    for group in ordered:
        if group.region_id is not None:
            region_options.setdefault(
                group.region_id,
                RegionOption(
                    region_id=group.region_id,
                    name=group.region_name or f"Region #{group.region_id}",
                ),
            )
    return AssetView(
        groups=ordered,
        regions=sorted(region_options.values(), key=lambda r: r.name.lower()),
        categories=category_options,
        total_items=sum(len(g.structures) for g in ordered),
    )


async def structure_page(
    db: AsyncSession,
    location_id: int,
    *,
    page: int,
    page_size: int,
    owner_ids: list[int] | None,
    category: str | None = None,
    sort: str | None = None,
    direction: str | None = None,
) -> tuple[list[AssetRow], int, int]:
    """One page of per-type aggregated rows for a structure's panel. The
    same asset type from one owner merges into a single row with summed
    quantity (blueprint originals and copies stay separate rows). Filters
    by owner ids and category bucket (None = all); `sort` names a column
    to order by (None = the default owner-then-type order). Returns
    (rows, total groups, page used) — the page is clamped to range."""
    conditions = [
        Asset.owner_type == OWNER_CHARACTER,
        Asset.parent_location_id == location_id,
    ]
    if owner_ids is not None:
        conditions.append(Asset.owner_id.in_(owner_ids))
    if category is not None:
        conditions.append(category_condition(BUCKETS_BY_KEY[category]))

    group_by = [Asset.owner_id, Asset.type_id, Asset.is_blueprint_copy]
    total_query = select(*group_by).where(*conditions)
    if category is not None:
        total_query = _category_filter_joins(total_query, with_type=True)
    total_groups = (
        await db.execute(
            select(func.count()).select_from(
                total_query.group_by(*group_by).subquery()
            )
        )
    ).scalar_one()

    pages = max(1, -(-total_groups // page_size))
    page = min(max(1, page), pages)

    rows_query = _category_filter_joins(
        select(
            Asset.owner_id,
            Character.name,
            Asset.type_id,
            UniverseType.name,
            UniverseType.volume,
            func.sum(Asset.quantity),
            func.max(
                Asset.location_flag
            ),
            Asset.is_blueprint_copy,
            UniverseCategory.name,
        )
        .join(Character, Character.character_id == Asset.owner_id)
        .outerjoin(UniverseType, UniverseType.type_id == Asset.type_id)
        .where(*conditions),
        with_type=False,
    )
    rows_raw = (
        await db.execute(
            rows_query.group_by(
                Asset.owner_id,
                Asset.type_id,
                Asset.is_blueprint_copy,
                Character.name,
                UniverseType.name,
                UniverseType.volume,
                UniverseCategory.name,
            )
            .order_by(*_order_keys(sort, direction))
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
    ).all()

    asset_rows = [
        AssetRow(
            owner_id=owner_id,
            owner_name=owner_name,
            type_id=type_id,
            type_name=type_name,
            quantity=int(quantity),
            volume_total=volume * quantity if volume is not None else None,
            location_flag=flag or "",
            is_blueprint_copy=is_copy,
            icon_kind=_icon_kind(category_name, is_copy),
        )
        for (
            owner_id,
            owner_name,
            type_id,
            type_name,
            volume,
            quantity,
            flag,
            is_copy,
            category_name,
        ) in rows_raw
    ]
    return asset_rows, total_groups, page
