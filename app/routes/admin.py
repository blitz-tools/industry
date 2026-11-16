"""Admin section: SDE data status and controls.

The SDE mirror updates itself: a background loop checks the published
dump MD5 at most once per configured interval and drop-and-reimports on
change (see app/sde.py). This page is the status surface — last check,
last import, outcome — plus a manual Check now that bypasses the
interval gate. Single-user app today: the session gate is the only
access control (local accounts are a TODO platform item).
"""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..deps import is_authenticated
from ..sde import (
    check_and_import,
    ensure_sde_meta,
    import_in_progress,
    resolve_db_path,
    sde_info,
)
from ..templates import templates

router = APIRouter()


@router.get("/admin/sde")
async def admin_sde_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    settings = request.app.state.settings
    db_path = resolve_db_path(settings.database_url)
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
            "check_interval_hours": settings.sde_check_interval_hours,
        },
    )


@router.post("/admin/sde/check")
async def admin_sde_check(request: Request):
    """Check now: same engine as the background loop, bypassing only the
    interval gate (the MD5 comparison still applies — an unchanged
    release reports up-to-date, it does not re-import). Runs in a worker
    thread (a changed release means a multi-minute download) — the
    response returns immediately and the status lands on the page as it
    completes."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)

    settings = request.app.state.settings
    db_path = resolve_db_path(settings.database_url)

    async def run() -> None:
        await asyncio.to_thread(
            check_and_import,
            db_path,
            dump_url=settings.sde_dump_url,
            user_agent=settings.esi_user_agent,
        )

    # Keep a reference so the task is never garbage-collected mid-run.
    request.app.state.sde_check_task = asyncio.create_task(run())
    return RedirectResponse("/admin/sde", status_code=303)
