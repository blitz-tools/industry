"""Character and corporation data sync: assets, blueprints, skills, and
industry jobs, pulled from ESI into owner-keyed tables with the universe
IDs each snapshot references resolved alongside.

Page fetches go through the ETag cache (a fresh-window pass makes zero
HTTP calls; an expired one revalidates with cheap 304s). The snapshot
replace (delete + insert) is deliberately the LAST write for an owner:
ETagCache.store() commits the shared session mid-fetch, so a failure
before the replace leaves the previous snapshot intact.

Owner-agnostic by design: rows carry owner_type/owner_id. The corporation
sync targets the main character's corporation — their tokens stand in
for the corp, so the Director/CEO role gate runs before anything touches
a corp endpoint (a call we know will 403 burns ESI's error-limit budget).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..db import utc_now
from ..models import (
    Asset,
    AssetSync,
    Blueprint,
    Character,
    CharacterLoyalty,
    DataSync,
    IndustryJob,
    Skill,
    UniverseType,
)
from .client import ESIClient, ESIError, ReauthorizationRequired
from .roles import check_corp_access
from .telemetry import elapsed_ms, monotonic_start, record_sync_run
from .universe import UniverseResolver, corporation_name

logger = logging.getLogger(__name__)

ASSETS_SCOPE = "esi-assets.read_assets.v1"
CORP_ASSETS_SCOPE = "esi-assets.read_corporation_assets.v1"
CORP_BLUEPRINTS_SCOPE = "esi-corporations.read_blueprints.v1"
CORP_JOBS_SCOPE = "esi-industry.read_corporation_jobs.v1"
CHAR_BLUEPRINTS_SCOPE = "esi-characters.read_blueprints.v1"
SKILLS_SCOPE = "esi-skills.read_skills.v1"
CHAR_JOBS_SCOPE = "esi-industry.read_character_jobs.v1"
LOYALTY_SCOPE = "esi-characters.read_loyalty.v1"

# data_syncs kinds for the data this module syncs.
KIND_CORP_BLUEPRINTS = "corp-blueprints"
KIND_CORP_JOBS = "corp-jobs"
KIND_CHAR_BLUEPRINTS = "char-blueprints"
KIND_CHAR_SKILLS = "char-skills"
KIND_CHAR_JOBS = "char-jobs"
KIND_CHAR_LOYALTY = "char-loyalty"
# The asset kinds record into asset_syncs (owner-keyed, no kind column),
# so these exist only for the sync_runs history — the one dataset every
# kind joins (M15's observability slice).
KIND_CHAR_ASSETS = "char-assets"
KIND_CORP_ASSETS = "corp-assets"

# ESI's marker item for a rented office (corporation assets only): each
# office shows up as a type-27 "Office" row (flag "OfficeFolder" for
# structure offices, "Office" for NPC stations) whose parent group holds
# the office's hangar divisions. The marker itself is bookkeeping, not
# inventory — corporation views exclude it from tables and counts. The
# parent container id is reported with location_type "item" but is worth
# resolving as a structure: characters with docking access there get a
# real name and system for it.
OFFICE_TYPE_ID = 27
OFFICE_FLAGS = ("Office", "OfficeFolder")

# Serializes sync passes (manual button vs background tick). Single-process,
# like the per-character refresh locks in client.py.
_sync_lock = asyncio.Lock()

# Containers can nest (ship in a hangar, crate in a ship); cap the walk.
MAX_CHAIN_DEPTH = 10

OWNER_CHARACTER = "character"
OWNER_CORPORATION = "corporation"


@dataclass
class SyncOutcome:
    owner_id: int
    name: str
    status: str  # "synced" | "reauth" | "no-scope" | "no-roles" | "error"
    item_count: int = 0
    detail: str | None = None


def has_assets_scope(character: Character) -> bool:
    return ASSETS_SCOPE in character.scopes.split()


def has_corp_assets_scope(character: Character) -> bool:
    return CORP_ASSETS_SCOPE in character.scopes.split()


async def sync_all_characters(
    db: AsyncSession,
    esi: ESIClient,
    characters: Sequence[Character],
    *,
    resolver: UniverseResolver,
) -> list[SyncOutcome]:
    """Sync every character's data kinds; one failure never aborts the
    rest."""
    async with _sync_lock:
        return [
            outcome
            for character in characters
            for outcome in await _sync_one_character(db, esi, resolver, character)
        ]


async def _sync_one_character(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> list[SyncOutcome]:
    """Sync one character's kinds: assets (with universe resolution),
    blueprints, skills, and industry jobs, each with its own scope gate
    and outcome. A dead refresh token short-circuits the remaining kinds —
    they would all fail the same way, and each failure re-attempts the
    refresh."""
    first = await _sync_character_assets(db, esi, resolver, character)
    outcomes = [first]
    dead_token = first.status == "reauth"
    for kind, fetch in (
        (KIND_CHAR_BLUEPRINTS, _sync_character_blueprints),
        (KIND_CHAR_SKILLS, _sync_character_skills),
        (KIND_CHAR_LOYALTY, _sync_character_loyalty),
        (KIND_CHAR_JOBS, _sync_character_jobs),
    ):
        if dead_token:
            # Near-zero duration is honest: the kind was skipped, not run.
            await _record_data_sync(
                db,
                kind,
                OWNER_CHARACTER,
                character.character_id,
                "reauth",
                duration_ms=elapsed_ms(monotonic_start()),
            )
            outcomes.append(
                SyncOutcome(character.character_id, character.name, "reauth")
            )
            continue
        outcome = await fetch(db, esi, resolver, character)
        outcomes.append(outcome)
        dead_token = outcome.status == "reauth"
    return outcomes


async def _sync_character_assets(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> SyncOutcome:
    # Calling the endpoint without the scope is a guaranteed 403, and 403s
    # burn ESI's error-limit budget.
    if not has_assets_scope(character):
        await _record_sync(
            db,
            OWNER_CHARACTER,
            character.character_id,
            "no-scope",
            f"Grant lacks {ASSETS_SCOPE}",
            kind=KIND_CHAR_ASSETS,
            duration_ms=elapsed_ms(monotonic_start()),
        )
        return SyncOutcome(character.character_id, character.name, "no-scope")

    start = monotonic_start()
    try:
        rows = await esi.get_paginated(character, "/characters/{character_id}/assets/")
    except ReauthorizationRequired:
        await _record_sync(
            db,
            OWNER_CHARACTER,
            character.character_id,
            "reauth",
            kind=KIND_CHAR_ASSETS,
            duration_ms=elapsed_ms(start),
        )
        return SyncOutcome(character.character_id, character.name, "reauth")
    except ESIError as exc:
        await _record_sync(
            db,
            OWNER_CHARACTER,
            character.character_id,
            "error",
            str(exc),
            kind=KIND_CHAR_ASSETS,
            duration_ms=elapsed_ms(start),
        )
        return SyncOutcome(
            character.character_id, character.name, "error", detail=str(exc)
        )

    assets = _build_assets(OWNER_CHARACTER, character.character_id, rows)
    # Snapshot replace: strictly after all page fetches (see module docstring).
    await db.execute(
        delete(Asset).where(
            Asset.owner_type == OWNER_CHARACTER, Asset.owner_id == character.character_id
        )
    )
    if assets:
        await db.execute(insert(Asset), assets)
    await _record_sync(
        db,
        OWNER_CHARACTER,
        character.character_id,
        "ok",
        kind=KIND_CHAR_ASSETS,
        duration_ms=elapsed_ms(start),
        item_count=len(rows),
    )

    # Universe resolution is best-effort and outside the snapshot write:
    # a failing name lookup must not lose a good snapshot.
    await _resolve_universe(db, esi, resolver, character, rows, assets)

    return SyncOutcome(
        character.character_id, character.name, "synced", item_count=len(rows)
    )


async def _sync_data_kind(
    db: AsyncSession,
    *,
    kind: str,
    holder: Character,
    owner_type: str,
    owner_id: int,
    owner_name: str,
    scope: str,
    replace: Callable[[], Awaitable[int]],
) -> SyncOutcome:
    """The scaffolding every data-kind sync shares: scope gate (a scopeless
    call is a guaranteed 403 and burns ESI's error-limit budget), outcome
    recording, and the SyncOutcome. `holder` is the character whose grant
    is checked — the synced character, or the main standing in for the
    corporation. `replace` performs the page fetches and the snapshot
    replace and returns the item count; keeping the replace inside it
    preserves the module's ordering rule (the snapshot replace is the
    fetch's last write, so a failure leaves the previous snapshot)."""
    if scope not in holder.scopes.split():
        detail = f"Grant lacks {scope}"
        await _record_data_sync(
            db,
            kind,
            owner_type,
            owner_id,
            "no-scope",
            detail,
            duration_ms=elapsed_ms(monotonic_start()),
        )
        return SyncOutcome(owner_id, owner_name, "no-scope", detail=detail)
    start = monotonic_start()
    try:
        item_count = await replace()
    except ReauthorizationRequired:
        await _record_data_sync(
            db, kind, owner_type, owner_id, "reauth", duration_ms=elapsed_ms(start)
        )
        return SyncOutcome(owner_id, owner_name, "reauth")
    except ESIError as exc:
        await _record_data_sync(
            db,
            kind,
            owner_type,
            owner_id,
            "error",
            str(exc),
            duration_ms=elapsed_ms(start),
        )
        return SyncOutcome(owner_id, owner_name, "error", detail=str(exc))
    await _record_data_sync(
        db,
        kind,
        owner_type,
        owner_id,
        "ok",
        duration_ms=elapsed_ms(start),
        item_count=item_count,
    )
    return SyncOutcome(owner_id, owner_name, "synced", item_count=item_count)


def _blueprint_values(
    owner_type: str, owner_id: int, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """ESI blueprint rows to owner-keyed table values (character and
    corporation endpoints share the shape)."""
    return [
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "item_id": row["item_id"],
            "type_id": row["type_id"],
            "location_id": row["location_id"],
            "location_flag": row.get("location_flag", ""),
            "quantity": row.get("quantity", 1),
            "runs": row.get("runs"),
            "material_efficiency": row.get("material_efficiency", 0),
            "time_efficiency": row.get("time_efficiency", 0),
        }
        for row in rows
    ]


def _job_values(
    owner_type: str, owner_id: int, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """ESI industry-job rows to owner-keyed table values (character and
    corporation endpoints share the shape)."""
    return [
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "job_id": row["job_id"],
            "installer_id": row.get("installer_id", 0),
            "activity_id": row.get("activity_id", 0),
            "blueprint_type_id": row.get("blueprint_type_id", 0),
            "runs": row.get("runs", 0),
            "successful_runs": row.get("successful_runs"),
            "status": row.get("status", ""),
            "start_date": _parse_esi_datetime(row.get("start_date")),
            "end_date": _parse_esi_datetime(row.get("end_date")),
            "completed_date": _parse_esi_datetime(row.get("completed_date")),
            "station_id": row.get("station_id"),
        }
        for row in rows
    ]


async def _resolve_blueprint_locations(
    db: AsyncSession,
    resolver: UniverseResolver,
    *,
    owner_type: str,
    owner_id: int,
    rows: list[dict[str, Any]],
) -> None:
    """Name blueprint locations the owner's asset snapshot can't hop:
    location ids that are not snapshot items resolve on their own (station
    or structure — see UniverseResolver.resolve_location_ids). Hop-able
    ids (containers, offices) keep naming through their parent at render
    time, so this never parks a placeholder over a name the hop would
    find. Best-effort like all universe resolution; the resolver never
    raises."""
    if not rows:
        return
    location_ids = {row["location_id"] for row in rows}
    hopable = set(
        (
            await db.execute(
                select(Asset.item_id).where(
                    Asset.owner_type == owner_type,
                    Asset.owner_id == owner_id,
                    Asset.item_id.in_(location_ids),
                )
            )
        ).scalars()
    )
    unresolvable = location_ids - hopable
    if not unresolvable:
        return
    all_characters = (
        (await db.execute(select(Character).order_by(Character.name))).scalars().all()
    )
    await resolver.resolve_location_ids(unresolvable, characters=all_characters)


async def _sync_character_blueprints(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> SyncOutcome:
    """Character blueprint snapshot, same shape as the corporation kind."""
    fetched: list[dict[str, Any]] = []

    async def replace() -> int:
        rows = await esi.get_paginated(
            character, "/characters/{character_id}/blueprints/"
        )
        fetched.extend(rows)
        values = _blueprint_values(OWNER_CHARACTER, character.character_id, rows)
        await db.execute(
            delete(Blueprint).where(
                Blueprint.owner_type == OWNER_CHARACTER,
                Blueprint.owner_id == character.character_id,
            )
        )
        if values:
            await db.execute(insert(Blueprint), values)
        return len(rows)

    outcome = await _sync_data_kind(
        db,
        kind=KIND_CHAR_BLUEPRINTS,
        holder=character,
        owner_type=OWNER_CHARACTER,
        owner_id=character.character_id,
        owner_name=character.name,
        scope=CHAR_BLUEPRINTS_SCOPE,
        replace=replace,
    )
    if outcome.status == "synced":
        # Blueprint type names for the page, best-effort and outside the
        # outcome (a failing name lookup must not lose a good snapshot;
        # the resolver never raises).
        await resolver.ensure_types({row["type_id"] for row in fetched})
        # And the locations the owner's snapshot can't hop (structures
        # named directly — see _resolve_blueprint_locations).
        await _resolve_blueprint_locations(
            db,
            resolver,
            owner_type=OWNER_CHARACTER,
            owner_id=character.character_id,
            rows=fetched,
        )
    return outcome


async def _sync_character_skills(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> SyncOutcome:
    """Character skills snapshot: the whole sheet in one response (not
    paginated)."""
    sheet: list[dict[str, Any]] = []

    async def replace() -> int:
        body = await esi.get(character, "/characters/{character_id}/skills/")
        sheet.extend(body.get("skills", []) if isinstance(body, dict) else [])
        values = [
            {
                "owner_type": OWNER_CHARACTER,
                "owner_id": character.character_id,
                "skill_id": skill["skill_id"],
                "trained_skill_level": skill.get("trained_skill_level", 0),
                "active_skill_level": skill.get("active_skill_level", 0),
                "skillpoints_in_skill": skill.get("skillpoints_in_skill", 0),
            }
            for skill in sheet
        ]
        await db.execute(
            delete(Skill).where(
                Skill.owner_type == OWNER_CHARACTER,
                Skill.owner_id == character.character_id,
            )
        )
        if values:
            await db.execute(insert(Skill), values)
        return len(sheet)

    outcome = await _sync_data_kind(
        db,
        kind=KIND_CHAR_SKILLS,
        holder=character,
        owner_type=OWNER_CHARACTER,
        owner_id=character.character_id,
        owner_name=character.name,
        scope=SKILLS_SCOPE,
        replace=replace,
    )
    if outcome.status == "synced":
        # Skill names for the page, best-effort (see blueprints above).
        await resolver.ensure_types({skill["skill_id"] for skill in sheet})
    return outcome


async def _sync_character_loyalty(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> SyncOutcome:
    """Character loyalty-point balances: one row per corporation the
    character holds points with (not paginated), replaced wholesale.
    M6's LP acquisition node reads these — the offer variants stay a
    curated pin until M15 syncs the lpstore dataset."""
    balances: list[dict[str, Any]] = []

    async def replace() -> int:
        # The loyalty route is /loyalty/points/ — the bare /loyalty/
        # path 404s (the live failure this fixed, 2026-11-25; the
        # tests had mocked the wrong route faithfully).
        rows = await esi.get(
            character, "/characters/{character_id}/loyalty/points/"
        )
        balances.extend(rows if isinstance(rows, list) else [])
        values = [
            {
                "character_id": character.character_id,
                "corporation_id": row["corporation_id"],
                "points": row.get("points", 0),
            }
            for row in balances
        ]
        await db.execute(
            delete(CharacterLoyalty).where(
                CharacterLoyalty.character_id == character.character_id
            )
        )
        if values:
            await db.execute(insert(CharacterLoyalty), values)
        return len(balances)

    outcome = await _sync_data_kind(
        db,
        kind=KIND_CHAR_LOYALTY,
        holder=character,
        owner_type=OWNER_CHARACTER,
        owner_id=character.character_id,
        owner_name=character.name,
        scope=LOYALTY_SCOPE,
        replace=replace,
    )
    if outcome.status == "synced":
        # Corporation names for the LP ledger, best-effort (see skills
        # above) — renders stay pure universe_corporations joins.
        for row in balances:
            await corporation_name(db, esi, row["corporation_id"])
    return outcome


async def _sync_character_jobs(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    character: Character,
) -> SyncOutcome:
    """Character industry job snapshot, completed jobs included — the
    planner correlates history, not just live slots (same view as the
    corporation kind)."""

    async def replace() -> int:
        rows = await esi.get_paginated(
            character,
            "/characters/{character_id}/industry/jobs/",
            params={"include_completed": "true"},
        )
        values = _job_values(OWNER_CHARACTER, character.character_id, rows)
        await db.execute(
            delete(IndustryJob).where(
                IndustryJob.owner_type == OWNER_CHARACTER,
                IndustryJob.owner_id == character.character_id,
            )
        )
        if values:
            await db.execute(insert(IndustryJob), values)
        return len(rows)

    return await _sync_data_kind(
        db,
        kind=KIND_CHAR_JOBS,
        holder=character,
        owner_type=OWNER_CHARACTER,
        owner_id=character.character_id,
        owner_name=character.name,
        scope=CHAR_JOBS_SCOPE,
        replace=replace,
    )


def _build_assets(
    owner_type: str, owner_id: int, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
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
                "owner_type": owner_type,
                "owner_id": owner_id,
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
    item_ids = {row["item_id"] for row in rows}
    # Top-level locations: rows that sit directly in one (containers point
    # at their parent, so every parent is covered).
    wanted = {
        (row["location_id"], row["location_type"])
        for row in rows
        if row["location_type"] != "item"
    }
    # Dangling item locations: ESI reports some structure-hangar contents
    # (and personal items in corporation offices) against ids that are
    # never asset rows in the owner's snapshot — no hop exists. They
    # resolve like any untyped location id (stations/structures answer,
    # docking access permitting; an id that resolves nowhere parks as
    # restricted instead of burning the error budget every pass).
    dangling = {
        row["location_id"]
        for row in rows
        if row["location_type"] == "item" and row["location_id"] not in item_ids
    }
    # Office contents (and the marker) hang off container ids reported as
    # "item" that are really the office's structure — resolving them names
    # the office panels and places them in their system (needs a character
    # with the structures scope and docking access; otherwise parks).
    wanted |= {
        (row["parent_location_id"], "structure")
        for row in assets
        if row["owner_type"] == OWNER_CORPORATION
        and row["location_flag"] in OFFICE_FLAGS
    }
    if not type_ids and not wanted and not dangling:
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
    # Dangling ids classify and resolve like any untyped location id
    # (see resolve_location_ids) — this is what names structure-hangar
    # contents on the assets AND blueprints pages.
    if dangling:
        infos.update(
            await resolver.resolve_location_ids(
                dangling, characters=all_characters
            )
        )
    system_ids = {info.system_id for info in infos.values() if info.system_id}
    await resolver.ensure_systems(system_ids)


async def _record_sync(
    db: AsyncSession,
    owner_type: str,
    owner_id: int,
    status: str,
    detail: str | None = None,
    *,
    kind: str,
    duration_ms: int | None = None,
    item_count: int = 0,
) -> None:
    """Upsert the owner's asset_syncs row (the assets page's read) and
    append the run to the sync_runs history with its kind (M15's one
    dataset — the asset kinds join the data kinds there)."""
    sync = await db.get(AssetSync, (owner_type, owner_id))
    if sync is None:
        sync = AssetSync(owner_type=owner_type, owner_id=owner_id)
        db.add(sync)
    sync.status = status
    sync.detail = detail
    sync.synced_at = utc_now()
    await db.commit()
    await record_sync_run(
        db,
        kind=kind,
        owner_type=owner_type,
        owner_id=owner_id,
        status=status,
        duration_ms=duration_ms,
        item_count=item_count,
        detail=detail,
    )


async def sync_corporation(
    db: AsyncSession,
    esi: ESIClient,
    *,
    resolver: UniverseResolver,
) -> list[SyncOutcome] | None:
    """Sync the main character's corporation data: assets, blueprints,
    and industry jobs. None when no main is selected (nothing to target).
    The role gate runs once; each kind records its own outcome, so a
    missing kind-specific scope fails only that kind."""
    async with _sync_lock:
        return await _sync_corporation_locked(db, esi, resolver)


async def _sync_corporation_locked(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
) -> list[SyncOutcome] | None:
    main = (
        await db.execute(select(Character).where(Character.is_main))
    ).scalar_one_or_none()
    if main is None:
        return None

    corp_id = main.corporation_id
    if corp_id is None:
        # Roster renders and the corp overview persist membership; resolve
        # here too so the background tick converges without a page visit.
        try:
            corp_id = (
                await esi.get_public(f"/characters/{main.character_id}/")
            ).get("corporation_id")
        except ESIError:
            corp_id = None
        if corp_id is None:
            return None  # nothing to key a sync row against; retry next pass
        main.corporation_id = corp_id
        await db.commit()
    label = f"corporation {corp_id}"

    # Role gate first: the main's tokens stand in for the corporation.
    gate_start = monotonic_start()
    access = await check_corp_access(esi, main)
    if access.status != "ok":
        if access.status == "insufficient":
            status, detail = "no-roles", "Main holds no Director/CEO role"
        else:
            status, detail = access.status, f"Role gate: {access.status}"
        duration_ms = elapsed_ms(gate_start)
        await _record_sync(
            db,
            OWNER_CORPORATION,
            corp_id,
            status,
            detail,
            kind=KIND_CORP_ASSETS,
            duration_ms=duration_ms,
        )
        await _record_data_sync(
            db,
            KIND_CORP_BLUEPRINTS,
            OWNER_CORPORATION,
            corp_id,
            status,
            detail,
            duration_ms=duration_ms,
        )
        await _record_data_sync(
            db,
            KIND_CORP_JOBS,
            OWNER_CORPORATION,
            corp_id,
            status,
            detail,
            duration_ms=duration_ms,
        )
        return [SyncOutcome(corp_id, label, status, detail=detail)]

    return [
        await _sync_corp_assets(db, esi, resolver, main, corp_id, label),
        await _sync_corp_blueprints(db, esi, resolver, main, corp_id, label),
        await _sync_corp_jobs(db, esi, main, corp_id, label),
    ]


async def _sync_corp_assets(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    main: Character,
    corp_id: int,
    label: str,
) -> SyncOutcome:
    """Corporation asset snapshot (role gate already passed)."""
    if not has_corp_assets_scope(main):
        detail = f"Main grant lacks {CORP_ASSETS_SCOPE}"
        await _record_sync(
            db,
            OWNER_CORPORATION,
            corp_id,
            "no-scope",
            detail,
            kind=KIND_CORP_ASSETS,
            duration_ms=elapsed_ms(monotonic_start()),
        )
        return SyncOutcome(corp_id, label, "no-scope", detail=detail)

    start = monotonic_start()
    try:
        rows = await esi.get_paginated(main, f"/corporations/{corp_id}/assets/")
    except ReauthorizationRequired:
        await _record_sync(
            db,
            OWNER_CORPORATION,
            corp_id,
            "reauth",
            kind=KIND_CORP_ASSETS,
            duration_ms=elapsed_ms(start),
        )
        return SyncOutcome(corp_id, label, "reauth")
    except ESIError as exc:
        await _record_sync(
            db,
            OWNER_CORPORATION,
            corp_id,
            "error",
            str(exc),
            kind=KIND_CORP_ASSETS,
            duration_ms=elapsed_ms(start),
        )
        return SyncOutcome(corp_id, label, "error", detail=str(exc))

    assets = _build_assets(OWNER_CORPORATION, corp_id, rows)
    # Snapshot replace: strictly after all page fetches (see module docstring).
    await db.execute(
        delete(Asset).where(
            Asset.owner_type == OWNER_CORPORATION, Asset.owner_id == corp_id
        )
    )
    if assets:
        await db.execute(insert(Asset), assets)
    await _record_sync(
        db,
        OWNER_CORPORATION,
        corp_id,
        "ok",
        kind=KIND_CORP_ASSETS,
        duration_ms=elapsed_ms(start),
        item_count=len(rows),
    )

    # Universe resolution is best-effort and outside the snapshot write.
    await _resolve_universe(db, esi, resolver, main, rows, assets)

    return SyncOutcome(corp_id, label, "synced", item_count=len(rows))


async def _sync_corp_blueprints(
    db: AsyncSession,
    esi: ESIClient,
    resolver: UniverseResolver,
    main: Character,
    corp_id: int,
    label: str,
) -> SyncOutcome:
    """Corporation blueprint snapshot (role gate already passed)."""
    fetched: list[dict[str, Any]] = []

    async def replace() -> int:
        rows = await esi.get_paginated(main, f"/corporations/{corp_id}/blueprints/")
        fetched.extend(rows)
        values = _blueprint_values(OWNER_CORPORATION, corp_id, rows)
        await db.execute(
            delete(Blueprint).where(
                Blueprint.owner_type == OWNER_CORPORATION,
                Blueprint.owner_id == corp_id,
            )
        )
        if values:
            await db.execute(insert(Blueprint), values)
        return len(rows)

    outcome = await _sync_data_kind(
        db,
        kind=KIND_CORP_BLUEPRINTS,
        holder=main,
        owner_type=OWNER_CORPORATION,
        owner_id=corp_id,
        owner_name=label,
        scope=CORP_BLUEPRINTS_SCOPE,
        replace=replace,
    )
    if outcome.status == "synced":
        # Locations the corp snapshot can't hop, same as the character
        # kind (see _resolve_blueprint_locations).
        await _resolve_blueprint_locations(
            db,
            resolver,
            owner_type=OWNER_CORPORATION,
            owner_id=corp_id,
            rows=fetched,
        )
    return outcome


async def _sync_corp_jobs(
    db: AsyncSession,
    esi: ESIClient,
    main: Character,
    corp_id: int,
    label: str,
) -> SyncOutcome:
    """Corporation industry job snapshot, completed jobs included — the
    planner will correlate history, not just live slots (role gate
    already passed)."""

    async def replace() -> int:
        rows = await esi.get_paginated(
            main,
            f"/corporations/{corp_id}/industry/jobs/",
            params={"include_completed": "true"},
        )
        values = _job_values(OWNER_CORPORATION, corp_id, rows)
        await db.execute(
            delete(IndustryJob).where(
                IndustryJob.owner_type == OWNER_CORPORATION,
                IndustryJob.owner_id == corp_id,
            )
        )
        if values:
            await db.execute(insert(IndustryJob), values)
        return len(rows)

    return await _sync_data_kind(
        db,
        kind=KIND_CORP_JOBS,
        holder=main,
        owner_type=OWNER_CORPORATION,
        owner_id=corp_id,
        owner_name=label,
        scope=CORP_JOBS_SCOPE,
        replace=replace,
    )


def _parse_esi_datetime(value: str | None):
    """ISO-8601 (ESI sends UTC with a Z suffix) to naive UTC, or None."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


async def _record_data_sync(
    db: AsyncSession,
    kind: str,
    owner_type: str,
    owner_id: int,
    status: str,
    detail: str | None = None,
    *,
    duration_ms: int | None = None,
    item_count: int | None = None,
) -> None:
    sync = await db.get(DataSync, (kind, owner_type, owner_id))
    if sync is None:
        sync = DataSync(kind=kind, owner_type=owner_type, owner_id=owner_id)
        db.add(sync)
    sync.status = status
    sync.detail = detail
    sync.synced_at = utc_now()
    await db.commit()
    await record_sync_run(
        db,
        kind=kind,
        owner_type=owner_type,
        owner_id=owner_id,
        status=status,
        duration_ms=duration_ms,
        item_count=item_count,
        detail=detail,
    )


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
            # The corporation sync shares the resolver and the tick's
            # never-raise contract; the gate inside records failures.
            corp_outcomes = await sync_corporation(db, esi, resolver=resolver)
            if corp_outcomes is not None:
                outcomes.extend(corp_outcomes)
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
