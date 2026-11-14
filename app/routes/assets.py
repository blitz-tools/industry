"""Asset page routes: the structure browser, per-structure fragments, the
manual sync trigger, and corporation section stubs.

The page and fragment handlers are pure DB reads — all ESI traffic belongs
to the background sync (see app/esi/assets.py). Only POST /assets/sync
touches ESI, and it does so through the same sync entry point.
"""

from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from ..assets import (
    BUCKETS_BY_KEY,
    CategoryOption,
    RegionOption,
    carry_query,
    character_sync_status,
    humanize_sync_age,
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
from ..models import Character, UniverseRegion
from ..templates import templates

router = APIRouter()

CORP_PAGES = {
    "assets": "Assets",
    "jobs": "Jobs",
    "wallets": "Wallets",
    "blueprints": "Blueprints",
}


async def _load_characters(db) -> list[Character]:
    return (
        (await db.execute(select(Character).order_by(Character.name))).scalars().all()
    )


@router.get("/assets")
async def assets_page(request: Request, db: DbDep):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    selected = parse_chars(request.query_params.getlist("chars"), characters)
    selected_category = parse_category(request.query_params.get("category"))
    view = await system_groups(db, owner_ids=selected, category=selected_category)

    # Region filter: validated against known regions, then applied to the
    # resolved system list (a structure's region is fixed, so fragments
    # never need to re-check it).
    selected_region = parse_region(request.query_params.get("region"))
    if selected_region is not None:
        known = {option.region_id for option in view.regions}
        if selected_region not in known:
            row = await db.get(UniverseRegion, selected_region)
            if row is None:
                selected_region = None  # unknown id: treat as All
            else:
                view.regions.append(RegionOption(row.region_id, row.name))
                view.regions.sort(key=lambda option: option.name.lower())
    if selected_region is not None:
        view.groups = [
            group for group in view.groups if group.region_id == selected_region
        ]
        view.total_items = sum(len(group.structures) for group in view.groups)

    # Category options are dynamic (buckets with assets under the owner
    # filter). A selected bucket that matched nothing stays visible in the
    # dropdown, so the URL state keeps a matching control.
    if selected_category is not None and selected_category not in {
        option.key for option in view.categories
    }:
        bucket = BUCKETS_BY_KEY[selected_category]
        view.categories.append(CategoryOption(bucket.key, bucket.label))

    sync_statuses, last_sync = await character_sync_status(db, characters)
    return templates.TemplateResponse(
        request,
        "assets.html",
        {
            "authenticated": True,
            "active": "assets",
            "characters": characters,
            "selected": selected,
            "view": view,
            "selected_region": selected_region,
            "selected_category": selected_category,
            "sync_statuses": sync_statuses,
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


@router.get("/corp/{page}")
async def corp_page(request: Request, page: str):
    """Stub pages for the Corporation section; real implementations land
    with the corporation asset work."""
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
    return templates.TemplateResponse(
        request,
        "corp_stub.html",
        {"authenticated": True, "active": f"corp-{page}", "title": title},
    )
