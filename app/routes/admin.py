"""Admin section: SDE data status and controls, Observability.

The SDE mirror is administrator-controlled: a background loop checks the
published dump MD5 at most once per configured interval and
drop-and-reimports on change — but only once an initial import exists
and while imports are not paused (see app/sde.py). This page is the
control surface: the initial Import now, the interval-bypassing Check
now, pause/resume of the automation, and a stop for a running
import. Single-user app today: the session gate is the only access
control (local accounts are a TODO platform item).

Admin > Observability (M15) is the central view of the one stored
telemetry dataset: every sync kind's latest run — public, character,
and corporation families, with status, duration, and staleness — plus
per-group ESI rate-limit headroom. Specific pages show page-filtered
subsets of the same dataset (the markets sync panel when it lands); the
checks are never duplicated. Grown in place from the framework slice's
sync-status page, so the route path stays /admin/sync.
"""

import asyncio
import json
from datetime import timedelta

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from markupsafe import Markup
from sqlalchemy import func, select

from ..charts import SERIES_HUES, chart_data, line_chart, sparkline
from ..db import sqlite_stats, utc_now
from ..deps import DbDep, is_authenticated
from ..esi.assets import (
    KIND_CHAR_ASSETS,
    KIND_CHAR_BLUEPRINTS,
    KIND_CHAR_JOBS,
    KIND_CHAR_LOYALTY,
    KIND_CHAR_SKILLS,
    KIND_CORP_ASSETS,
    KIND_CORP_BLUEPRINTS,
    KIND_CORP_JOBS,
    OWNER_CHARACTER,
    OWNER_CORPORATION,
)
from ..esi.telemetry import (
    ERROR_LIMIT_BUDGET,
    error_limit_history,
    error_limit_pct_used,
    latest_error_limit,
    latest_sync_runs,
    rate_group_headroom,
    rate_group_history,
    sync_duration_history,
)
from ..esi.world import (
    KIND_COST_INDICES,
    KIND_MARKET_PRICES,
    PUBLIC_OWNER_ID,
    PUBLIC_OWNER_TYPE,
    public_sync_rows,
    world_sync_tick,
)
from ..models import Character, CostIndex, MarketPrice
from ..sde import (
    check_and_import,
    ensure_sde_meta,
    import_exists,
    import_in_progress,
    is_paused,
    request_cancel,
    resolve_db_path,
    sde_info,
    set_paused,
)
from ..templates import templates

router = APIRouter()


def _db_path(request: Request):
    return resolve_db_path(request.app.state.settings.database_url)


def _spawn(request: Request, force: bool) -> None:
    """Run the check/import in a worker thread (a changed release means a
    multi-minute download); the task reference keeps it alive."""
    settings = request.app.state.settings
    db_path = _db_path(request)

    async def run() -> None:
        await asyncio.to_thread(
            check_and_import,
            db_path,
            dump_url=settings.sde_dump_url,
            user_agent=settings.esi_user_agent,
            force=force,
        )

    request.app.state.sde_check_task = asyncio.create_task(run())


@router.get("/admin/sde")
async def admin_sde_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    db_path = _db_path(request)
    # Normalizes a pre-check-era sde_meta so the fields read cleanly.
    if db_path.exists():
        ensure_sde_meta(db_path)
    meta, counts = sde_info(db_path)
    return templates.TemplateResponse(
        request,
        "admin_sde.html",
        {
            "authenticated": True,
            "active": "admin-sde",
            "meta": meta,
            "counts": counts,
            "in_progress": import_in_progress(),
            "has_import": import_exists(db_path),
            "paused": is_paused(db_path),
            "check_interval_hours": request.app.state.settings.sde_check_interval_hours,
        },
    )


@router.post("/admin/sde/check")
async def admin_sde_check(request: Request):
    """Check now: same engine as the background loop, bypassing only the
    interval gate (the MD5 comparison still applies — an unchanged
    release reports up-to-date, it does not re-import)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    _spawn(request, force=False)
    return RedirectResponse("/admin/sde", status_code=303)


@router.post("/admin/sde/import")
async def admin_sde_import(request: Request):
    """Import now: a full download and re-import regardless of the stored
    MD5 — the administrator's trigger for the initial import on a fresh
    deployment, or a manual refresh."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    if import_in_progress():
        return RedirectResponse("/admin/sde", status_code=303)
    _spawn(request, force=True)
    return RedirectResponse("/admin/sde", status_code=303)


@router.post("/admin/sde/pause")
async def admin_sde_pause(request: Request):
    """Toggle the pause on automatic imports (manual buttons still
    work)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    db_path = _db_path(request)
    set_paused(db_path, not is_paused(db_path))
    return RedirectResponse("/admin/sde", status_code=303)


@router.post("/admin/sde/stop")
async def admin_sde_stop(request: Request):
    """Stop the running check/import at the next boundary (checked
    between download chunks — lands within seconds)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    request_cancel()
    return RedirectResponse("/admin/sde", status_code=303)


# Public world-state syncs: family display metadata for the status page.
_SYNC_FAMILIES = {
    KIND_COST_INDICES: {
        "label": "Cost indices",
        "source": "/industry/systems/ · every system × activity",
    },
    KIND_MARKET_PRICES: {
        "label": "Market prices",
        "source": "/markets/prices/ · global adjusted/average per type",
    },
}

# Character and corporation kinds (the sync_runs dataset's other
# sections): label + source for the per-owner rows.
_KIND_META = {
    KIND_CHAR_ASSETS: ("Assets", "/characters/{id}/assets/"),
    KIND_CHAR_BLUEPRINTS: ("Blueprints", "/characters/{id}/blueprints/"),
    KIND_CHAR_SKILLS: ("Skills", "/characters/{id}/skills/"),
    KIND_CHAR_LOYALTY: ("Loyalty", "/characters/{id}/loyalty/points/"),
    KIND_CHAR_JOBS: ("Jobs", "/characters/{id}/industry/jobs/"),
    KIND_CORP_ASSETS: ("Assets", "/corporations/{id}/assets/"),
    KIND_CORP_BLUEPRINTS: ("Blueprints", "/corporations/{id}/blueprints/"),
    KIND_CORP_JOBS: ("Jobs", "/corporations/{id}/industry/jobs/"),
}

# Stored statuses → display chip (class, label). Storage stays verbatim
# (public kinds say "ok", character/corp kinds "synced"); only the chip
# normalizes.
_STATUS_CHIP = {
    "ok": ("ok", "ok"),
    "synced": ("ok", "ok"),
    "error": ("failed", "error"),
    "reauth": ("failed", "reauth"),
    "no-scope": ("warn", "no-scope"),
    "no-roles": ("warn", "no-roles"),
    "never": ("warn", "never"),
}

# Meter thresholds (the markets mockup's headroom-gate classes).
_METER_WARN_PCT = 60
_METER_LOW_PCT = 85

_FRESH_STATUSES = ("ok", "synced")

# Worst-status-first for an owner panel's summary chip (an owner is as
# bad as its worst kind; unknown statuses rank with the gates).
_STATUS_SEVERITY = {"error": 0, "reauth": 1, "no-roles": 2, "no-scope": 3, "ok": 4}


def _meter_class(pct: float | None) -> str:
    if pct is None:
        return ""
    if pct >= _METER_LOW_PCT:
        return "low"
    if pct >= _METER_WARN_PCT:
        return "warn"
    return ""


def _chip(status: str) -> tuple[str, str]:
    return _STATUS_CHIP.get(status, ("warn", status))


def _window_label(window) -> str | None:
    if window is None:
        return None
    minutes = int(window.total_seconds() // 60)
    return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h"


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "—"
    if value < 1024 * 1024:
        return f"{value / 1024:.0f} KB"
    if value < 1024 * 1024 * 1024:
        return f"{value / 1024 / 1024:.1f} MB"
    return f"{value / 1024 / 1024 / 1024:.2f} GB"


@router.get("/admin/sync")
async def admin_sync_page(request: Request, db: DbDep):
    """Observability: every sync kind's latest run (status, duration,
    staleness) across the public, character, and corporation sections,
    plus per-group ESI rate-limit headroom and the legacy error-limit
    budget. DB-pure like every render."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    settings = request.app.state.settings
    world_fresh_after = timedelta(minutes=2 * settings.world_sync_interval_minutes)
    assets_fresh_after = timedelta(minutes=2 * settings.assets_sync_interval_minutes)
    now = utc_now()

    runs = await latest_sync_runs(db)
    run_by_key = {(run.kind, run.owner_type, run.owner_id): run for run in runs}

    # Public families: last outcome + live row counts (pre-slice rows
    # fall back to their data_syncs timestamp).
    rows = await public_sync_rows(db)
    by_kind = {row.kind: row for row in rows}
    families = []
    for kind, meta in _SYNC_FAMILIES.items():
        sync = by_kind.get(kind)
        run = run_by_key.get((kind, PUBLIC_OWNER_TYPE, PUBLIC_OWNER_ID))
        if kind == KIND_COST_INDICES:
            count = (
                await db.execute(select(func.count()).select_from(CostIndex))
            ).scalar_one()
        else:
            count = (
                await db.execute(select(func.count()).select_from(MarketPrice))
            ).scalar_one()
        status = sync.status if sync else "never"
        last_attempt = (run.started_at if run else None) or (
            sync.synced_at if sync else None
        )
        families.append(
            {
                "kind": kind,
                "label": meta["label"],
                "source": meta["source"],
                "status": status,
                "chip": _chip(status),
                "detail": sync.detail if sync else None,
                "count": count,
                "duration_ms": run.duration_ms if run else None,
                "last_attempt": last_attempt,
                "fresh": (
                    status in _FRESH_STATUSES
                    and last_attempt is not None
                    and last_attempt >= now - world_fresh_after
                ),
            }
        )

    # Character and corporation kinds: per-owner rows from the one
    # dataset, joined to character names for the labels.
    names = {
        character.character_id: character.name
        for character in (
            await db.execute(select(Character).order_by(Character.name))
        )
        .scalars()
        .all()
    }

    def _owner_row(run):
        status = run.status
        if run.owner_type == OWNER_CHARACTER:
            owner = names.get(run.owner_id, f"character {run.owner_id}")
        else:
            owner = f"corporation {run.owner_id}"
        label, source = _KIND_META.get(run.kind, (run.kind, ""))
        return {
            "kind": run.kind,
            "label": label,
            "source": source,
            "owner": owner,
            "status": status,
            "chip": _chip(status),
            "detail": run.detail,
            "duration_ms": run.duration_ms,
            "last_attempt": run.started_at,
            "fresh": (
                status in _FRESH_STATUSES
                and run.started_at >= now - assets_fresh_after
            ),
        }

    def _owner_groups(owner_type: str) -> list[dict]:
        """One expanding panel per owner (the roster's corp-row
        presentation): the summary carries the aggregate — kind count,
        worst-status chip, latest attempt — and the panel holds the
        per-kind rows."""
        by_owner: dict[int, list] = {}
        for run in runs:
            if run.owner_type == owner_type:
                by_owner.setdefault(run.owner_id, []).append(run)
        groups = []
        for owner_id, owner_runs in by_owner.items():
            rows = [
                _owner_row(run)
                for run in sorted(owner_runs, key=lambda run: run.kind)
            ]
            worst = min(
                rows, key=lambda row: _STATUS_SEVERITY.get(row["status"], 2)
            )
            groups.append(
                {
                    "owner": rows[0]["owner"],
                    "owner_ref": f"{owner_type}-{owner_id}",
                    "count": len(rows),
                    "chip": worst["chip"],
                    "last_attempt": max(row["last_attempt"] for row in rows),
                    "rows": rows,
                }
            )
        return groups

    character_groups = _owner_groups(OWNER_CHARACTER)
    corp_groups = _owner_groups(OWNER_CORPORATION)

    # Rate-limit headroom: the server's Remaining against the parsed max
    # (the gate number), plus the app's own trailing-window sum as a
    # cross-check. The legacy error budget gets the same meter treatment
    # (its remainder is the budget the universe-resolution 403/404s burn).
    # Each meter cell carries a sparkline of its budget over time (the
    # retained observation history — the trend beside the position).
    group_history = await rate_group_history(db)
    headroom = []
    for group in await rate_group_headroom(db):
        headroom.append(
            {
                "group": group.group,
                "limit_raw": group.limit_raw,
                "max_tokens": group.max_tokens,
                "remaining": group.remaining,
                "pct_used": group.pct_used,
                "window_label": _window_label(group.window),
                "window_used": group.window_used,
                "meter_class": _meter_class(group.pct_used),
                "observed_at": group.observed_at,
                "spark": Markup(
                    sparkline(group_history.get(group.group, []), unit="%")
                ),
            }
        )
    error_limit = await latest_error_limit(db)
    error_limit_pct = error_limit_pct_used(error_limit)
    error_spark = Markup(sparkline(await error_limit_history(db), unit="%"))

    # Sync durations over time (the public families): one line per kind,
    # hues assigned in the fixed family order (color follows the entity),
    # with a JSON twin feeding the crosshair tooltip and a table-view
    # twin for the values.
    public_kinds = list(_SYNC_FAMILIES)
    durations = await sync_duration_history(
        db, owner_type=PUBLIC_OWNER_TYPE, kinds=public_kinds
    )
    duration_series = [
        {
            "name": _SYNC_FAMILIES[kind]["label"],
            "hue": SERIES_HUES[slot],
            "points": durations[kind],
        }
        for slot, kind in enumerate(public_kinds)
        if durations.get(kind)
    ]
    duration_chart = Markup(
        line_chart(duration_series, y_unit=" s", value_format="{:.2f}")
    )
    duration_chart_json = json.dumps(
        chart_data(duration_series, y_unit=" s", value_format="{:.2f}")
    )
    duration_rows = sorted(
        (
            {"label": _SYNC_FAMILIES[kind]["label"], "at": at, "seconds": secs}
            for kind, points in durations.items()
            for at, secs in points
        ),
        key=lambda row: row["at"],
        reverse=True,
    )[:24]

    # SQLite health: storage usage and row counts, read at render time.
    stats = await sqlite_stats(db, settings.database_url)
    database = {
        "storage": _format_bytes(stats["file_bytes"]),
        "used": _format_bytes(stats["used_bytes"]),
        "reclaimable": _format_bytes(stats["free_bytes"]),
        "wal": _format_bytes(stats["wal_bytes"]),
        "journal_mode": stats["journal_mode"],
        "total_rows": stats["total_rows"],
        "tables": stats["tables"],
    }

    return templates.TemplateResponse(
        request,
        "admin_observability.html",
        {
            "authenticated": True,
            "active": "admin-observability",
            "families": families,
            "character_groups": character_groups,
            "corp_groups": corp_groups,
            "headroom": headroom,
            "error_limit": error_limit,
            "error_limit_pct": error_limit_pct,
            "error_limit_budget": ERROR_LIMIT_BUDGET,
            "error_meter_class": _meter_class(error_limit_pct),
            "error_spark": error_spark,
            "duration_chart": duration_chart,
            "duration_chart_json": duration_chart_json,
            "duration_series": duration_series,
            "duration_rows": duration_rows,
            "database": database,
            "interval_minutes": settings.world_sync_interval_minutes,
            "assets_interval_minutes": settings.assets_sync_interval_minutes,
        },
    )


@router.post("/admin/sync/run")
async def admin_sync_run(request: Request):
    """Sync now: one public-sync pass in the background (both families,
    same engine as the loop — ETags make an early revalidation cheap)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    app = request.app

    async def run() -> None:
        await world_sync_tick(
            app.state.session_factory, app.state.http, app.state.settings
        )

    app.state.world_sync_task = asyncio.create_task(run())
    return RedirectResponse("/admin/sync", status_code=303)
