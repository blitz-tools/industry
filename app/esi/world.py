"""Public world-state syncs (the M15 framework slice): endpoints with no
character scopes and no role gates — the sync category's definition.

This module carries the band's first two families, the light public
snapshots M4's install-cost math consumes:

- cost indices: /industry/systems/ → cost_indices, one row per system ×
  activity. The activity strings are ESI's own enum ("manufacturing",
  "reaction", …), stored verbatim per the mirror philosophy — mapping to
  the registry's activity keys is a query-layer concern
  (app.industry.cost_index). Pinned from a live response 2026-11-23:
  copying, invention, manufacturing, reaction,
  researching_material_efficiency, researching_time_efficiency; 5,485
  systems; not paginated.
- market prices: /markets/prices/ → market_prices. Either price can be
  absent per type (live 2026-11-23: adjusted present on all 16,234 rows,
  average missing on ~2,000) — consumers degrade, never crash. Not
  paginated.

The heavier families (public contracts, regional orders/history, LP
store offers, player-structure markets) land with M15 proper; they bring
pruning semantics these full-snapshot families don't need.

Both fetches go through the ETag-cached public client, and the snapshot
replace (delete + insert) is deliberately the LAST write —
ETagCache.store() commits the shared session mid-fetch, so a failure
before the replace leaves the previous snapshot intact (the ordering
rule from esi/assets.py). data_syncs rows key on the "public" owner
(0): status is only ok/error, because no scope or role gate exists to
fail any other way.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..db import utc_now
from ..models import CostIndex, DataSync, MarketPrice
from .assets import SyncOutcome
from .client import ESIClient, ESIError

logger = logging.getLogger(__name__)

# data_syncs kinds for the public families (owner_type "public", owner 0).
KIND_COST_INDICES = "cost-indices"
KIND_MARKET_PRICES = "market-prices"

PUBLIC_OWNER_TYPE = "public"
PUBLIC_OWNER_ID = 0

# Serializes sync passes against the background tick (single-process,
# like esi/assets.py's lock; no manual button exists yet — M15's sync
# panel may add one).
_sync_lock = asyncio.Lock()


async def _record_data_sync(
    db: AsyncSession,
    kind: str,
    status: str,
    detail: str | None = None,
) -> None:
    """Upsert the kind's public data_syncs row (the assets-module
    pattern, keyed on the constant public owner). Row counts are not
    recorded — the status view reads them live from the tables."""
    sync = await db.get(DataSync, (kind, PUBLIC_OWNER_TYPE, PUBLIC_OWNER_ID))
    if sync is None:
        sync = DataSync(
            kind=kind, owner_type=PUBLIC_OWNER_TYPE, owner_id=PUBLIC_OWNER_ID
        )
        db.add(sync)
    sync.status = status
    sync.detail = detail
    sync.synced_at = utc_now()
    await db.commit()


async def _sync_public_kind(
    db: AsyncSession,
    *,
    kind: str,
    fetch: Callable[[], Awaitable[int]],
) -> SyncOutcome:
    """The scaffolding a public family shares: fetch + snapshot replace
    (inside `fetch`, so the replace stays the fetch's last write), the
    data_syncs record, and the outcome. No scope gate exists to check —
    a public endpoint either answers or errors."""
    label = "public"
    try:
        item_count = await fetch()
    except ESIError as exc:
        detail = str(exc)
        await _record_data_sync(db, kind, "error", detail)
        return SyncOutcome(PUBLIC_OWNER_ID, label, "error", detail=detail)
    await _record_data_sync(db, kind, "ok")
    return SyncOutcome(PUBLIC_OWNER_ID, label, "synced", item_count=item_count)


async def sync_cost_indices(db: AsyncSession, esi: ESIClient) -> SyncOutcome:
    """Snapshot /industry/systems/ into cost_indices: every system ×
    activity row, ESI's activity strings verbatim."""

    def rows_from(systems: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "system_id": system["solar_system_id"],
                "activity": entry["activity"],
                "cost_index": float(entry["cost_index"]),
            }
            for system in systems
            for entry in system.get("cost_indices", [])
        ]

    async def fetch() -> int:
        systems = await esi.get_public("/industry/systems/")
        values = rows_from(systems)
        # Snapshot replace: strictly after the fetch (module docstring).
        await db.execute(delete(CostIndex))
        if values:
            await db.execute(insert(CostIndex), values)
        return len(values)

    return await _sync_public_kind(db, kind=KIND_COST_INDICES, fetch=fetch)


async def sync_market_prices(db: AsyncSession, esi: ESIClient) -> SyncOutcome:
    """Snapshot /markets/prices/ into market_prices: every type's global
    adjusted/average price, either column allowed absent."""

    async def fetch() -> int:
        prices = await esi.get_public("/markets/prices/")
        values = [
            {
                "type_id": row["type_id"],
                "adjusted_price": row.get("adjusted_price"),
                "average_price": row.get("average_price"),
            }
            for row in prices
        ]
        await db.execute(delete(MarketPrice))
        if values:
            await db.execute(insert(MarketPrice), values)
        return len(values)

    return await _sync_public_kind(db, kind=KIND_MARKET_PRICES, fetch=fetch)


async def world_sync_tick(
    session_factory: async_sessionmaker[AsyncSession],
    http: Any,
    settings: Settings,
) -> None:
    """One public-sync pass with its own session. Never raises: the loop
    must survive ESI outages. Deliberately NOT part of sync_tick (the
    character-sync pass) — that tick early-returns on an empty roster,
    and public data must sync regardless."""
    try:
        async with session_factory() as db:
            esi = ESIClient(http, settings, db)
            async with _sync_lock:
                outcomes = [
                    await sync_cost_indices(db, esi),
                    await sync_market_prices(db, esi),
                ]
            for outcome in outcomes:
                if outcome.status == "error":
                    logger.warning(
                        "public sync failed (%s): %s",
                        outcome.name,
                        outcome.detail,
                    )
    except Exception:
        logger.exception("world sync tick failed")


async def world_sync_loop(
    session_factory: async_sessionmaker[AsyncSession],
    http: Any,
    settings: Settings,
) -> None:
    """Tick once shortly after startup (a restarted server converges
    without waiting out the interval), then every interval."""
    interval = settings.world_sync_interval_minutes * 60
    while True:
        await world_sync_tick(session_factory, http, settings)
        await asyncio.sleep(interval)


async def public_sync_rows(db: AsyncSession) -> list[DataSync]:
    """The public families' data_syncs rows for the admin status view
    (M15's Observability page grows from this)."""
    return list(
        (
            await db.execute(
                select(DataSync)
                .where(DataSync.owner_type == PUBLIC_OWNER_TYPE)
                .order_by(DataSync.kind)
            )
        )
        .scalars()
        .all()
    )
