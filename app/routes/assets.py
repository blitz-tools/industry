"""Asset page routes: the structure browser, per-structure fragments, and
the manual sync trigger.

The page and fragment handlers are pure DB reads — all ESI traffic belongs
to the background sync (see app/esi/assets.py). Only POST /assets/sync
touches ESI, and it does so through the same sync entry point.
"""

from datetime import timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from ..assets import (
    apply_region_filter,
    carry_query,
    character_filter_groups,
    character_sync_status,
    humanize_sync_age,
    keep_selected_category,
    parse_category,
    parse_chars,
    parse_direction,
    parse_region,
    parse_sort,
    sort_headers,
    structure_page,
    system_groups,
)
from ..deps import DbDep, EsiDep, is_authenticated
from ..esi.assets import sync_all_characters
from ..esi.universe import UniverseResolver
from ..models import Character
from ..templates import templates

router = APIRouter()


async def _load_characters(db) -> list[Character]:
    return (
        (await db.execute(select(Character).order_by(Character.name))).scalars().all()
    )


@router.get("/assets")
async def assets_page(request: Request, db: DbDep):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    # The character selection lives in the URL when present, and is
    # remembered in the session otherwise — leaving and returning to the
    # page keeps the chosen characters. "All" is stored as its sentinel so
    # it survives too.
    raw_chars = request.query_params.getlist("chars")
    if not raw_chars:
        stored = request.session.get("assets_chars")
        if stored is not None:
            raw_chars = [stored]
    selected = parse_chars(raw_chars, characters)
    if raw_chars:
        request.session["assets_chars"] = (
            "all" if selected is None else ",".join(str(c) for c in selected)
        )
    selected_category = parse_category(request.query_params.get("category"))
    view = await system_groups(db, owner_ids=selected, category=selected_category)

    # Region filter: validated against known regions, then applied to the
    # resolved system list (a structure's region is fixed, so fragments
    # never need to re-check it).
    selected_region = await apply_region_filter(
        db, view, parse_region(request.query_params.get("region"))
    )
    # Category options are dynamic (buckets with assets under the owner
    # filter); a selected-but-empty bucket stays visible.
    keep_selected_category(view, selected_category)

    sync_statuses, last_sync = await character_sync_status(db, characters)
    # "Fresh" means synced within two sync intervals; older reads as stale.
    fresh_after = timedelta(
        minutes=2 * request.app.state.settings.assets_sync_interval_minutes
    )
    return templates.TemplateResponse(
        request,
        "assets.html",
        {
            "authenticated": True,
            "active": "assets",
            "selected": selected,
            "view": view,
            "selected_region": selected_region,
            "selected_category": selected_category,
            "character_groups": await character_filter_groups(
                db,
                characters,
                sync_statuses,
                selected=selected,
                fresh_after=fresh_after,
            ),
            "last_sync_text": humanize_sync_age(last_sync),
            "page_size": request.app.state.settings.assets_page_size,
        },
    )


@router.get("/assets/structure/{location_id}")
async def structure_fragment(
    request: Request, db: DbDep, location_id: int, page: int = 1
):
    """Per-structure panel contents, fetched on expand. Auth failures
    return 401 HTML rather than a redirect — this is a fetch target."""
    if not is_authenticated(request):
        return HTMLResponse(
            "<p class='warn'>Not authorized — reload the page to sign in.</p>",
            status_code=401,
        )

    characters = await _load_characters(db)
    selected = parse_chars(request.query_params.getlist("chars"), characters)
    category = parse_category(request.query_params.get("category"))
    sort = parse_sort(request.query_params.get("sort"))
    direction = parse_direction(request.query_params.get("dir"))
    page_size = request.app.state.settings.assets_page_size
    rows, total, used_page = await structure_page(
        db,
        location_id,
        page=page,
        page_size=page_size,
        owner_ids=selected,
        category=category,
        sort=sort,
        direction=direction,
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
            "selected": selected,
            "selected_category": category,
            "sort": sort,
            "direction": direction,
            "sort_headers": sort_headers(
                location_id,
                current_sort=sort,
                current_dir=direction,
                chars=selected,
                category=category,
            ),
            "carry_qs": carry_query(
                chars=selected,
                category=category,
                sort=sort,
                direction=direction,
            ),
            "fragment_base": "/assets/structure",
            "show_owner": True,
            "is_office": False,
        },
    )


@router.post("/assets/sync")
async def sync_assets(request: Request, db: DbDep, esi: EsiDep):
    """Force a full sync now (awaits the background pass if one is
    mid-flight), then back to /assets preserving the active filters."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)

    characters = await _load_characters(db)
    settings = request.app.state.settings
    resolver = UniverseResolver(db, esi, settings=settings)
    await sync_all_characters(db, esi, characters, resolver=resolver)

    form = await request.form()
    params = [
        (name, value)
        for name, value in (
            ("chars", form.get("chars")),
            ("region", form.get("region")),
            ("category", form.get("category")),
        )
        if value
    ]
    target = "/assets"
    if params:
        target += "?" + urlencode(params)
    return RedirectResponse(target, status_code=303)
