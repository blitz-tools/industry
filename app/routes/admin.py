"""Admin section: SDE data status and controls, public-sync status.

The SDE mirror is administrator-controlled: a background loop checks the
published dump MD5 at most once per configured interval and
drop-and-reimports on change — but only once an initial import exists
and while imports are not paused (see app/sde.py). This page is the
control surface: the initial Import now, the interval-bypassing Check
now, pause/resume of the automation, and a stop for a running
import. Single-user app today: the session gate is the only access
control (local accounts are a TODO platform item).

The public world-state syncs (cost indices, market prices — M15's
framework slice) get their status surface here: one row per family with
its last outcome and row counts, plus a Sync now. This is deliberately
the seed of M15's Admin > Observability page; the heavier families join
the same view when they land.
"""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from ..deps import DbDep, is_authenticated
from ..esi.world import (
    KIND_COST_INDICES,
    KIND_MARKET_PRICES,
    public_sync_rows,
    world_sync_tick,
)
from ..models import CostIndex, MarketPrice
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


@router.get("/admin/sync")
async def admin_sync_page(request: Request, db: DbDep):
    """Public-sync status: one row per family with its last outcome and
    current row counts, plus a Sync now. DB-pure like every render."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    rows = await public_sync_rows(db)
    by_kind = {row.kind: row for row in rows}
    families = []
    for kind, meta in _SYNC_FAMILIES.items():
        sync = by_kind.get(kind)
        if kind == KIND_COST_INDICES:
            count = (
                await db.execute(select(func.count()).select_from(CostIndex))
            ).scalar_one()
        else:
            count = (
                await db.execute(select(func.count()).select_from(MarketPrice))
            ).scalar_one()
        families.append(
            {
                "kind": kind,
                "label": meta["label"],
                "source": meta["source"],
                "status": sync.status if sync else "never",
                "detail": sync.detail if sync else None,
                "synced_at": sync.synced_at if sync else None,
                "count": count,
            }
        )
    return templates.TemplateResponse(
        request,
        "admin_sync.html",
        {
            "authenticated": True,
            "active": "admin-sync",
            "families": families,
            "interval_minutes": request.app.state.settings.world_sync_interval_minutes,
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
