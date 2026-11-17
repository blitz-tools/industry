"""Corporation section: the overview page, the corporation asset browser,
and the (still stub) sub-pages.

The section targets exactly one corporation — the main character's (see
`Character.is_main`). The overview resolves that corporation and runs the
role gate: the main's tokens stand in for the corp on corp-scoped ESI
calls, which only works while they hold Director or CEO. Sub-pages stay
inaccessible until the gate passes, so users never hit guaranteed-403
syncs; every failure mode gets an explanatory state on the overview
instead (same philosophy as restricted-structure parking).

The corporation assets page reuses the character browser's view layer
(`app/assets.py` is owner-parameterized) and the same background sync
machinery (`app/esi/assets.py`); its renders are pure DB reads like the
character page — only the render-time role gate touches ESI, through the
ETag cache.
"""

from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from ..assets import (
    apply_region_filter,
    carry_query,
    corp_sync_note,
    corporation_offices,
    humanize_sync_age,
    is_office_location,
    keep_selected_category,
    owner_sync_status,
    parse_category,
    parse_direction,
    parse_region,
    parse_sort,
    sort_headers,
    structure_page,
    system_groups,
)
from ..deps import DbDep, EsiDep, is_authenticated
from ..esi.assets import (
    KIND_CORP_BLUEPRINTS,
    KIND_CORP_JOBS,
    OWNER_CORPORATION,
    sync_corporation,
)
from ..esi.client import ESIError
from ..esi.roles import CorpAccess, check_corp_access
from ..esi.universe import UniverseResolver, corporation_name
from ..industry import corporation_blueprints, corporation_jobs
from ..models import Character, DataSync
from ..templates import templates
from . import trusted_target

router = APIRouter()

CORP_PAGES = {
    "wallets": "Wallets",
}

CORP_ASSETS_FRAGMENT_BASE = "/corp/assets/structure"

# Pages the shared sync button may return to.
SYNC_BACK_TARGETS = frozenset({"/corp/assets", "/corp/blueprints", "/corp/jobs"})


async def _load_main(db) -> Character | None:
    return (
        await db.execute(select(Character).where(Character.is_main))
    ).scalar_one_or_none()


async def _resolve_corporation_id(db, esi, main: Character) -> int | None:
    """The main's corporation id: public data, persisted on first resolve
    so later renders (and the sync) stay ESI-free for the id."""
    if main.corporation_id is not None:
        return main.corporation_id
    try:
        info = await esi.get_public(f"/characters/{main.character_id}/")
        corporation_id = info.get("corporation_id")
    except ESIError:
        corporation_id = None
    if corporation_id is not None:
        main.corporation_id = corporation_id
        await db.commit()
    return corporation_id


async def _resolve_corporation(db, esi, main: Character) -> tuple[int | None, str | None]:
    """The corporation id plus its live name (overview only — data pages
    need just the id and stay DB-pure)."""
    corporation_id = await _resolve_corporation_id(db, esi, main)
    return corporation_id, await corporation_name(db, esi, corporation_id)


@router.get("/corp")
async def corp_overview(request: Request, db: DbDep, esi: EsiDep):
    """Corporation landing page: the main character, their corporation,
    and the role-gate status that unlocks the sub-pages."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    main = await _load_main(db)
    access = CorpAccess("no-main")
    corporation_id = None
    corporation_name_text = None
    if main is not None:
        corporation_id, corporation_name_text = await _resolve_corporation(db, esi, main)
        access = await check_corp_access(esi, main)

    return templates.TemplateResponse(
        request,
        "corp_overview.html",
        {
            "authenticated": True,
            "active": "corp",
            "main": main,
            "corporation_id": corporation_id,
            "corporation_name": corporation_name_text,
            "access": access,
        },
    )


@router.get("/corp/assets")
async def corp_assets_page(request: Request, db: DbDep, esi: EsiDep):
    """The corporation asset browser: the main's corporation snapshot in
    the same system → structure shape as the character page, plus the
    office summary (the shared inventory pool). Pure DB reads apart from
    the render-time role gate."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    main = await _load_main(db)
    if main is None or (await check_corp_access(esi, main)).status != "ok":
        return RedirectResponse("/corp", status_code=302)
    corporation_id = await _resolve_corporation_id(db, esi, main)

    selected_category = parse_category(request.query_params.get("category"))
    view = await system_groups(
        db,
        owner_ids=[corporation_id] if corporation_id else [],
        category=selected_category,
        owner_type=OWNER_CORPORATION,
    )
    selected_region = await apply_region_filter(
        db, view, parse_region(request.query_params.get("region"))
    )
    keep_selected_category(view, selected_category)

    sync = (
        await owner_sync_status(db, OWNER_CORPORATION, corporation_id)
        if corporation_id
        else None
    )
    return templates.TemplateResponse(
        request,
        "corp_assets.html",
        {
            "authenticated": True,
            "active": "corp-assets",
            "corporation_id": corporation_id,
            "view": view,
            "selected_region": selected_region,
            "selected_category": selected_category,
            "offices": (
                await corporation_offices(db, corporation_id)
                if corporation_id
                else []
            ),
            "sync_note": corp_sync_note(sync),
            "last_sync_text": humanize_sync_age(sync.synced_at if sync else None),
            "page_size": request.app.state.settings.assets_page_size,
        },
    )


@router.get("/corp/assets/structure/{location_id}")
async def corp_structure_fragment(
    request: Request, db: DbDep, location_id: int, page: int = 1
):
    """Per-structure panel contents for the corporation browser. Same
    fetch-target contract as the character fragment (401 HTML on auth
    failure); no owner column — the page names the single owner."""
    if not is_authenticated(request):
        return HTMLResponse(
            "<p class='warn'>Not authorized — reload the page to sign in.</p>",
            status_code=401,
        )

    main = await _load_main(db)
    corporation_id = main.corporation_id if main is not None else None
    if corporation_id is None:
        return HTMLResponse(
            "<p class='warn'>No corporation targeted — set a main character.</p>",
            status_code=409,
        )

    category = parse_category(request.query_params.get("category"))
    sort = parse_sort(request.query_params.get("sort"))
    direction = parse_direction(request.query_params.get("dir"))
    page_size = request.app.state.settings.assets_page_size
    rows, total, used_page = await structure_page(
        db,
        location_id,
        page=page,
        page_size=page_size,
        owner_ids=[corporation_id],
        category=category,
        sort=sort,
        direction=direction,
        owner_type=OWNER_CORPORATION,
    )
    pages = max(1, -(-total // page_size))
    return templates.TemplateResponse(
        request,
        "assets_structure.html",
        {
            "location_id": location_id,
            "rows": rows,
            "page": used_page,
            "pages": pages,
            "total": total,
            "selected_category": category,
            "sort": sort,
            "direction": direction,
            "sort_headers": sort_headers(
                location_id,
                current_sort=sort,
                current_dir=direction,
                chars=None,
                category=category,
                base=CORP_ASSETS_FRAGMENT_BASE,
                include_owner=False,
            ),
            "carry_qs": carry_query(
                chars=None,
                category=category,
                sort=sort,
                direction=direction,
            ),
            "fragment_base": CORP_ASSETS_FRAGMENT_BASE,
            "show_owner": False,
            "is_office": await is_office_location(
                db, OWNER_CORPORATION, corporation_id, location_id
            ),
        },
    )


@router.post("/corp/assets/sync")
async def sync_corp_assets(request: Request, db: DbDep, esi: EsiDep):
    """Force a corporation sync now (awaits a mid-flight pass), then back
    to /corp/assets preserving the active filters."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)

    settings = request.app.state.settings
    resolver = UniverseResolver(db, esi, settings=settings)
    await sync_corporation(db, esi, resolver=resolver)

    form = await request.form()
    params = [
        (name, value)
        for name, value in (
            ("region", form.get("region")),
            ("category", form.get("category")),
        )
        if value
    ]
    target = "/corp/assets"
    if params:
        target += "?" + urlencode(params)
    return RedirectResponse(target, status_code=303)


@router.post("/corp/sync")
async def sync_corp_data(request: Request, db: DbDep, esi: EsiDep):
    """The blueprints/jobs pages' Sync now: same corporation sync, back to
    the page that asked (whitelisted)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)

    settings = request.app.state.settings
    resolver = UniverseResolver(db, esi, settings=settings)
    await sync_corporation(db, esi, resolver=resolver)

    form = await request.form()
    back = trusted_target(form.get("back"), SYNC_BACK_TARGETS, "/corp/assets")
    return RedirectResponse(back, status_code=303)


async def _data_sync(db, kind: str, corporation_id: int | None):
    if corporation_id is None:
        return None
    return await db.get(DataSync, (kind, OWNER_CORPORATION, corporation_id))


@router.get("/corp/blueprints")
async def corp_blueprints_page(request: Request, db: DbDep, esi: EsiDep, page: int = 1):
    """The corporation's blueprints: type, ME/TE, runs (originals vs
    copies), location. Pure DB reads apart from the render-time role
    gate; locations label from the universe cache the asset syncs fill."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    main = await _load_main(db)
    if main is None or (await check_corp_access(esi, main)).status != "ok":
        return RedirectResponse("/corp", status_code=302)
    corporation_id = await _resolve_corporation_id(db, esi, main)

    rows, total, used_page = await corporation_blueprints(
        db,
        corporation_id or 0,
        page=page,
        page_size=request.app.state.settings.assets_page_size,
    )
    sync = await _data_sync(db, KIND_CORP_BLUEPRINTS, corporation_id)
    return templates.TemplateResponse(
        request,
        "corp_blueprints.html",
        {
            "authenticated": True,
            "active": "corp-blueprints",
            "rows": rows,
            "total": total,
            "page": used_page,
            "pages": max(1, -(-total // request.app.state.settings.assets_page_size)),
            "sync_note": corp_sync_note(sync),
            "last_sync_text": humanize_sync_age(sync.synced_at if sync else None),
        },
    )


@router.get("/corp/jobs")
async def corp_jobs_page(
    request: Request, db: DbDep, esi: EsiDep, page: int = 1, all: bool = False
):
    """The corporation's industry jobs: active ones by default, the full
    history (delivered/cancelled/reverted) behind the toggle. Installer
    names resolve through the tracked characters."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    main = await _load_main(db)
    if main is None or (await check_corp_access(esi, main)).status != "ok":
        return RedirectResponse("/corp", status_code=302)
    corporation_id = await _resolve_corporation_id(db, esi, main)

    rows, total, used_page = await corporation_jobs(
        db,
        corporation_id or 0,
        include_completed=all,
        page=page,
        page_size=request.app.state.settings.assets_page_size,
    )
    sync = await _data_sync(db, KIND_CORP_JOBS, corporation_id)
    return templates.TemplateResponse(
        request,
        "corp_jobs.html",
        {
            "authenticated": True,
            "active": "corp-jobs",
            "rows": rows,
            "total": total,
            "page": used_page,
            "pages": max(1, -(-total // request.app.state.settings.assets_page_size)),
            "show_all": all,
            "sync_note": corp_sync_note(sync),
            "last_sync_text": humanize_sync_age(sync.synced_at if sync else None),
        },
    )


@router.get("/corp/{page}")
async def corp_page(request: Request, page: str, db: DbDep, esi: EsiDep):
    """Stub pages for the Corporation section, gated on the main's role
    check. Real implementations land with the corporation data work."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    title = CORP_PAGES.get(page)
    if title is None:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"authenticated": True, "message": f"No such page: /corp/{page}"},
            status_code=404,
        )

    main = await _load_main(db)
    # Gate: without a passing role check the sub-pages stay closed — the
    # overview explains why (and what to do about it).
    if main is None or (await check_corp_access(esi, main)).status != "ok":
        return RedirectResponse("/corp", status_code=302)
    return templates.TemplateResponse(
        request,
        "corp_stub.html",
        {"authenticated": True, "active": f"corp-{page}", "title": title},
    )
