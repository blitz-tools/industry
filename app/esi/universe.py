"""Owner-agnostic universe ID resolution: types, stations, structures,
systems, and regions, cached in DB tables and fetched through the ESI
client's ETag cache.

Everything here is best-effort: a failing call degrades a name to a
placeholder ("Unknown type #123") rather than raising, so universe
resolution can never fail an asset sync or a page render. Structures
ESI refuses (403 without docking access) are parked as restricted rows
for `structure_retry_days` — every 403 burns ESI's error-limit budget,
so they must not be retried on every pass.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..db import utc_now
from ..models import (
    Character,
    UniverseCategory,
    UniverseGroup,
    UniverseLocation,
    UniverseRegion,
    UniverseType,
)
from .client import ESIClient, ESIError, ESIStatusError

LOCATION_STATION = "station"
LOCATION_STRUCTURE = "structure"
LOCATION_SYSTEM = "solar_system"


@dataclass
class LocationInfo:
    location_id: int
    kind: str  # "station" | "structure" | "solar_system"
    name: str | None  # None when unresolved; "Structure #<id>" when restricted
    system_id: int | None
    restricted: bool


@dataclass
class SystemInfo:
    system_id: int
    name: str | None
    region_id: int | None
    region_name: str | None


class UniverseResolver:
    """Resolves and caches universe entities. Owner-agnostic by design:
    nothing here knows whether the referencing assets belong to characters
    or corporations."""

    def __init__(
        self,
        db: AsyncSession,
        esi: ESIClient,
        *,
        settings: Settings,
    ):
        self._db = db
        self._esi = esi
        self._settings = settings

    async def ensure_types(self, type_ids: Iterable[int]) -> None:
        """Fetch /universe/types/ data for ids not yet stored."""
        wanted = set(type_ids)
        if not wanted:
            return
        existing = set(
            (
                await self._db.execute(
                    select(UniverseType.type_id).where(UniverseType.type_id.in_(wanted))
                )
            ).scalars()
        )
        for type_id in sorted(wanted - existing):
            try:
                body = await self._esi.get_public(f"/universe/types/{type_id}/")
            except ESIError:
                continue  # deleted/unreachable; renders as "Unknown type #id"
            self._db.add(
                UniverseType(
                    type_id=type_id,
                    name=body["name"],
                    volume=body.get("volume"),
                    packaged_volume=body.get("packaged_volume"),
                    group_id=body.get("group_id"),
                )
            )
        await self._db.commit()

    async def get_type(self, type_id: int) -> UniverseType | None:
        return await self._db.get(UniverseType, type_id)

    async def ensure_groups(self, group_ids: Iterable[int | None]) -> None:
        """Fetch /universe/groups/ data (and each group's category) for ids
        not yet stored; category names drive the assets page type filter. A
        group whose category fails to resolve is not stored, so the next
        sync pass retries it."""
        wanted = {group_id for group_id in group_ids if group_id is not None}
        if not wanted:
            return
        existing = set(
            (
                await self._db.execute(
                    select(UniverseGroup.group_id).where(
                        UniverseGroup.group_id.in_(wanted)
                    )
                )
            ).scalars()
        )
        for group_id in sorted(wanted - existing):
            try:
                body = await self._esi.get_public(f"/universe/groups/{group_id}/")
            except ESIError:
                continue  # deleted/unreachable; assets land in "Other"
            category_id = body.get("category_id")
            if category_id is None or await self._ensure_category(category_id):
                self._db.add(
                    UniverseGroup(
                        group_id=group_id,
                        name=body["name"],
                        category_id=category_id,
                    )
                )
        await self._db.commit()

    async def _ensure_category(self, category_id: int) -> UniverseCategory | None:
        category = await self._db.get(UniverseCategory, category_id)
        if category is not None:
            return category
        try:
            body = await self._esi.get_public(f"/universe/categories/{category_id}/")
        except ESIError:
            return None
        category = UniverseCategory(category_id=category_id, name=body["name"])
        self._db.add(category)
        return category

    async def resolve_locations(
        self,
        wanted: Iterable[tuple[int, str]],
        *,
        characters: Sequence[Character] = (),
    ) -> dict[int, LocationInfo]:
        """Resolve (location_id, kind) pairs to LocationInfo, fetching and
        persisting anything missing. `characters` are tried in name order
        for structures, which require a token with docking access."""
        infos: dict[int, LocationInfo] = {}
        pending: list[tuple[int, str]] = []
        ids = [location_id for location_id, _ in wanted]
        if ids:
            rows = (
                (
                    await self._db.execute(
                        select(UniverseLocation).where(
                            UniverseLocation.location_id.in_(ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            by_id = {row.location_id: row for row in rows}
        else:
            by_id = {}

        retry_cutoff = utc_now() - timedelta(days=self._settings.structure_retry_days)
        for location_id, kind in wanted:
            row = by_id.get(location_id)
            if row is None:
                pending.append((location_id, kind))
                continue
            if row.restricted and row.updated_at > retry_cutoff:
                # Recently refused: do not burn error-limit on a retry.
                infos[location_id] = self._info_from_row(row)
            elif row.restricted:
                pending.append((location_id, kind))
            else:
                infos[location_id] = self._info_from_row(row)

        for location_id, kind in pending:
            info = await self._fetch_location(location_id, kind, characters)
            infos[location_id] = info

        await self._db.commit()
        return infos

    async def ensure_systems(self, system_ids: Iterable[int]) -> dict[int, SystemInfo]:
        """Resolve system names and their region (via the constellation
        hop) for the given system ids; returns SystemInfo per system."""
        result: dict[int, SystemInfo] = {}
        for system_id in sorted(set(system_ids)):
            row = await self._db.get(UniverseLocation, system_id)
            if row is None:
                row = UniverseLocation(
                    location_id=system_id, kind=LOCATION_SYSTEM, system_id=system_id
                )
                self._db.add(row)
            if row.name is None or row.constellation_id is None:
                try:
                    body = await self._esi.get_public(f"/universe/systems/{system_id}/")
                    row.name = body.get("name")
                    row.constellation_id = body.get("constellation_id")
                except ESIError:
                    pass
            if row.region_id is None and row.constellation_id is not None:
                try:
                    body = await self._esi.get_public(
                        f"/universe/constellations/{row.constellation_id}/"
                    )
                    row.region_id = body.get("region_id")
                except ESIError:
                    pass
            region_name = None
            if row.region_id is not None:
                region = await self._ensure_region(row.region_id)
                region_name = region.name if region is not None else None
            result[system_id] = SystemInfo(
                system_id=system_id,
                name=row.name,
                region_id=row.region_id,
                region_name=region_name,
            )
        await self._db.commit()
        return result

    async def _ensure_region(self, region_id: int) -> UniverseRegion | None:
        region = await self._db.get(UniverseRegion, region_id)
        if region is not None:
            return region
        try:
            body = await self._esi.get_public(f"/universe/regions/{region_id}/")
        except ESIError:
            return None
        region = UniverseRegion(region_id=region_id, name=body["name"])
        self._db.add(region)
        return region

    async def _fetch_location(
        self,
        location_id: int,
        kind: str,
        characters: Sequence[Character],
    ) -> LocationInfo:
        """Fetch one unknown location; persist what was learned. Reuses an
        existing row (restricted-structure retries) instead of reinserting."""
        row = await self._db.get(UniverseLocation, location_id)

        def _row() -> UniverseLocation:
            if row is None:
                new = UniverseLocation(location_id=location_id, kind=kind)
                self._db.add(new)
                return new
            return row

        if kind == LOCATION_STATION:
            try:
                body = await self._esi.get_public(f"/universe/stations/{location_id}/")
            except ESIError:
                return LocationInfo(location_id, kind, None, None, False)
            target = _row()
            target.kind = kind
            target.name = body["name"]
            target.system_id = body.get("system_id")
            target.restricted = False
            return self._info_from_row(target)

        if kind == LOCATION_STRUCTURE:
            # Structures need a character token with docking access; try
            # each character in turn. All-refused parks the structure.
            for character in sorted(characters, key=lambda c: c.name):
                try:
                    body = await self._esi.get(
                        character, f"/universe/structures/{location_id}/"
                    )
                except ESIStatusError as exc:
                    if exc.status_code == 403:
                        continue
                    return LocationInfo(location_id, kind, None, None, False)
                except ESIError:
                    return LocationInfo(location_id, kind, None, None, False)
                target = _row()
                target.kind = kind
                target.name = body["name"]
                target.system_id = body.get("solar_system_id")
                target.restricted = False
                return self._info_from_row(target)
            target = _row()
            target.kind = kind
            target.name = f"Structure #{location_id}"
            target.system_id = None
            target.restricted = True
            return self._info_from_row(target)

        if kind == LOCATION_SYSTEM:
            try:
                body = await self._esi.get_public(f"/universe/systems/{location_id}/")
            except ESIError:
                return LocationInfo(location_id, kind, None, location_id, False)
            target = _row()
            target.kind = kind
            target.name = body.get("name")
            target.system_id = location_id
            target.constellation_id = body.get("constellation_id")
            target.restricted = False
            return self._info_from_row(target)

        return LocationInfo(location_id, kind, None, None, False)

    @staticmethod
    def _info_from_row(row: UniverseLocation) -> LocationInfo:
        return LocationInfo(
            location_id=row.location_id,
            kind=row.kind,
            name=row.name,
            system_id=row.system_id if row.kind != LOCATION_SYSTEM else row.location_id,
            restricted=row.restricted,
        )
