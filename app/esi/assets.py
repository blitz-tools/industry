"""Character asset sync: pull every page of ESI's assets endpoint into the
assets table, resolve the universe IDs the snapshot references, and record
a per-owner outcome.

Page fetches go through the ETag cache (a fresh-window pass makes zero
HTTP calls; an expired one revalidates with cheap 304s). The snapshot
replace (delete + insert) is deliberately the LAST write for an owner:
ETagCache.store() commits the shared session mid-fetch, so a failure
before the replace leaves the previous snapshot intact.

Owner-agnostic by design: rows carry owner_type/owner_id so corporation
assets can reuse this module unchanged.
"""

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..db import utc_now
from ..models import Asset, AssetSync, Character, UniverseType
from .client import ESIClient, ESIError, ReauthorizationRequired
from .universe import UniverseResolver

logger = logging.getLogger(__name__)

ASSETS_SCOPE = "esi-assets.read_assets.v1"

# Serializes sync passes (manual button vs background tick). Single-process,
# like the per-character refresh locks in client.py.
_sync_lock = asyncio.Lock()

# Containers can nest (ship in a hangar, crate in a ship); cap the walk.
MAX_CHAIN_DEPTH = 10

OWNER_CHARACTER = "character"


@dataclass
class SyncOutcome:
    owner_id: int
    name: str
    status: str  # "synced" | "reauth" | "no-scope" | "error"
    item_count: int = 0
    detail: str | None = None


def has_assets_scope(character: Character) -> bool:
    return ASSETS_SCOPE in character.scopes.split()


async def sync_all_characters(
    db: AsyncSession,
    esi: ESIClient,
    characters: Sequence[Character],
    *,
    resolver: UniverseResolver,
) -> list[SyncOutcome]:
    """Sync every character; one failure never aborts the rest."""
    async with _sync_lock:
        return [
            await _sync_one_character(db, esi, resolver, character)
            for character in characters
        ]


async def _sync_one_character(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> SyncOutcome:
    # Calling the endpoint without the scope is a guaranteed 403, and 403s
    # burn ESI's error-limit budget.
    if not has_assets_scope(character):
        await _record_sync(db, character.character_id, "no-scope")
        return SyncOutcome(character.character_id, character.name, "no-scope")

    try:
        rows = await esi.get_paginated(character, "/characters/{character_id}/assets/")
    except ReauthorizationRequired:
        await _record_sync(db, character.character_id, "reauth")
        return SyncOutcome(character.character_id, character.name, "reauth")
    except ESIError as exc:
        await _record_sync(db, character.character_id, "error", str(exc))
        return SyncOutcome(
            character.character_id, character.name, "error", detail=str(exc)
        )

    assets = _build_assets(character.character_id, rows)
    # Snapshot replace: strictly after all page fetches (see module docstring).
    await db.execute(
        delete(Asset).where(
            Asset.owner_type == OWNER_CHARACTER, Asset.owner_id == character.character_id
        )
    )
    if assets:
        await db.execute(insert(Asset), assets)
    await _record_sync(db, character.character_id, "ok", item_count=len(rows))

    # Universe resolution is best-effort and outside the snapshot write:
    # a failing name lookup must not lose a good snapshot.
    await _resolve_universe(db, esi, resolver, character, rows, assets)

    return SyncOutcome(
        character.character_id, character.name, "synced", item_count=len(rows)
    )


def _build_assets(character_id: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe by item_id (page boundaries can shift mid-sync) and resolve
    each row's top-level location (container chains collapse to their
    station/structure/system parent)."""
    by_item = {row["item_id"]: row for row in rows}
    locations = {
        item_id: (row["location_id"], row["location_type"])
        for item_id, row in by_item.items()
    }
    assets = []
    for item_id, row in by_item.items():
        assets.append(
            {
                "owner_type": OWNER_CHARACTER,
                "owner_id": character_id,
                "item_id": item_id,
                "type_id": row["type_id"],
                "quantity": row["quantity"],
                "location_id": row["location_id"],
                "location_flag": row.get("location_flag", ""),
                "location_type": row["location_type"],
                "parent_location_id": _parent_location_id(row, locations),
                "is_blueprint_copy": row.get("is_blueprint_copy", False),
                "is_singleton": row.get("is_singleton", False),
            }
        )
    return assets


def _parent_location_id(
    item: dict[str, Any], locations: dict[int, tuple[int, str]]
) -> int:
    """Walk item → container → … until a station/structure/system. ESI
    reports contents of ships/containers against the container's item_id;
    the denormalized parent keeps grouping and pagination indexed."""
    location_id = item["location_id"]
    location_type = item["location_type"]
    seen: set[int] = set()
    depth = 0
    while (
        location_type == "item"
        and depth < MAX_CHAIN_DEPTH
        and location_id not in seen
    ):
        seen.add(location_id)
        parent = locations.get(location_id)
        if parent is None:
            break  # container not in the snapshot; keep the raw location
        location_id, location_type = parent
        depth += 1
    return location_id


async def _resolve_universe(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
    rows: list[dict[str, Any]],
    assets: list[dict[str, Any]],
) -> None:
    """Resolve types and locations referenced by the fresh snapshot. The
    resolver never raises; failures degrade names to placeholders that the
    next sync pass retries."""
    type_ids = {row["type_id"] for row in rows}
    # Top-level locations: rows that sit directly in one (containers point
    # at their parent, so every parent is covered).
    wanted = {
        (row["location_id"], row["location_type"])
        for row in rows
        if row["location_type"] != "item"
    }
    if not type_ids and not wanted:
        return
    all_characters = (
        (await db.execute(select(Character).order_by(Character.name))).scalars().all()
    )
    await resolver.ensure_types(type_ids)
    # Groups/categories power the asset type filter. Collected from the
    # stored types (including previously-synced ones), so a filter shipped
    # after types were already resolved backfills on the next sync pass.
    if type_ids:
        group_ids = {
            group_id
            for group_id in (
                await db.execute(
                    select(UniverseType.group_id).where(
                        UniverseType.type_id.in_(type_ids)
                    )
                )
            ).scalars()
            if group_id is not None
        }
        await resolver.ensure_groups(group_ids)
    infos = await resolver.resolve_locations(wanted, characters=all_characters)
    system_ids = {info.system_id for info in infos.values() if info.system_id}
    await resolver.ensure_systems(system_ids)


async def _record_sync(
    db: AsyncSession,
    owner_id: int,
    status: str,
    detail: str | None = None,
    *,
    item_count: int = 0,
) -> None:
    sync = await db.get(AssetSync, (OWNER_CHARACTER, owner_id))
    if sync is None:
        sync = AssetSync(owner_type=OWNER_CHARACTER, owner_id=owner_id)
        db.add(sync)
    sync.status = status
    sync.detail = detail
    sync.synced_at = utc_now()
    await db.commit()


async def sync_tick(
    session_factory: async_sessionmaker[AsyncSession],
    http: Any,
    settings: Settings,
) -> None:
    """One background sync pass with its own session. Never raises: the
    loop must survive ESI outages."""
    try:
        async with session_factory() as db:
            characters = (
                (await db.execute(select(Character).order_by(Character.name)))
                .scalars()
                .all()
            )
            if not characters:
                return
            esi = ESIClient(http, settings, db)
            resolver = UniverseResolver(db, esi, settings=settings)
            outcomes = await sync_all_characters(db, esi, characters, resolver=resolver)
            for outcome in outcomes:
                if outcome.status == "error":
                    logger.warning(
                        "asset sync failed for %s: %s", outcome.name, outcome.detail
                    )
    except Exception:
        logger.exception("asset sync tick failed")


async def asset_sync_loop(
    session_factory: async_sessionmaker[AsyncSession],
    http: Any,
    settings: Settings,
) -> None:
    """Tick once shortly after startup (a restarted server converges
    without waiting out the interval), then every interval."""
    interval = settings.assets_sync_interval_minutes * 60
    while True:
        await sync_tick(session_factory, http, settings)
        await asyncio.sleep(interval)
