"""Asset query/view layer: pure DB reads for the assets page.

Page renders never touch ESI — the background sync owns all fetching, and
this module turns the stored snapshot into the system → structure view
with per-type row aggregation. Everything filters by owner id list so the
character multi-selector (and, later, corporation views) compose freely.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import String, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import utc_now
from .esi.assets import OWNER_CHARACTER
from .models import (
    Asset,
    AssetSync,
    Character,
    UniverseLocation,
    UniverseRegion,
    UniverseType,
)

UNKNOWN_SYSTEM = "Unknown system"


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
class AssetView:
    groups: list[SystemGroup]
    # Region options from the character-filtered (but region-unfiltered)
    # data, so the dropdown stays stable under its own filter.
    regions: list[RegionOption]
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


async def system_groups(db: AsyncSession, *, owner_ids: list[int] | None) -> AssetView:
    """System → structure view of the character asset snapshot, filtered to
    the selected owners (None = all)."""
    conditions = [Asset.owner_type == OWNER_CHARACTER]
    if owner_ids is not None:
        conditions.append(Asset.owner_id.in_(owner_ids))
    counts = (
        await db.execute(
            select(
                Asset.parent_location_id,
                func.count(),
                # Each top-level location has at least one direct
                # (non-container) child row that names its kind.
                func.max(
                    case((Asset.location_type != "item", Asset.location_type))
                ),
            )
            .where(*conditions)
            .group_by(Asset.parent_location_id)
        )
    ).all()

    if not counts:
        return AssetView(groups=[], regions=[], total_items=0)

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
        total_items=sum(len(g.structures) for g in ordered),
    )


async def structure_page(
    db: AsyncSession,
    location_id: int,
    *,
    page: int,
    page_size: int,
    owner_ids: list[int] | None,
) -> tuple[list[AssetRow], int, int]:
    """One page of per-type aggregated rows for a structure's panel. The
    same asset type from one owner merges into a single row with summed
    quantity (blueprint originals and copies stay separate rows). Returns
    (rows, total groups, page used) — the page is clamped to range."""
    conditions = [
        Asset.owner_type == OWNER_CHARACTER,
        Asset.parent_location_id == location_id,
    ]
    if owner_ids is not None:
        conditions.append(Asset.owner_id.in_(owner_ids))

    group_by = [Asset.owner_id, Asset.type_id, Asset.is_blueprint_copy]
    total_groups = (
        await db.execute(
            select(func.count()).select_from(
                select(*group_by)
                .where(*conditions)
                .group_by(*group_by)
                .subquery()
            )
        )
    ).scalar_one()

    pages = max(1, -(-total_groups // page_size))
    page = min(max(1, page), pages)

    rows_raw = (
        await db.execute(
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
            )
            .join(Character, Character.character_id == Asset.owner_id)
            .outerjoin(UniverseType, UniverseType.type_id == Asset.type_id)
            .where(*conditions)
            .group_by(
                Asset.owner_id,
                Asset.type_id,
                Asset.is_blueprint_copy,
                Character.name,
                UniverseType.name,
                UniverseType.volume,
            )
            .order_by(
                Character.name,
                func.coalesce(
                    UniverseType.name, "#" + cast(Asset.type_id, String)
                ),
            )
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
        ) in rows_raw
    ]
    return asset_rows, total_groups, page
