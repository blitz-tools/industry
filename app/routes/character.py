"""Character data pages: blueprints, skills, and industry jobs — the
character-side mirrors of the Corporation section's data pages.

Pure DB reads like every data page: all ESI traffic belongs to the
background sync or the shared Sync now button (POST /character/sync),
which runs the same per-character pass. A `?char=` filter narrows a page
to one character; absent it, every registered character's rows render
together.
"""

from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..assets import humanize_sync_age
from ..deps import DbDep, EsiDep, is_authenticated
from ..esi.assets import (
    KIND_CHAR_BLUEPRINTS,
    KIND_CHAR_JOBS,
    KIND_CHAR_SKILLS,
    OWNER_CHARACTER,
    sync_all_characters,
)
from ..esi.universe import UniverseResolver
from ..industry import (
    blueprints_page,
    character_skills,
    character_sync_notes,
    jobs_page,
    skill_summaries,
)
from ..models import Character
from ..templates import templates

router = APIRouter()

# Pages the shared sync button may return to.
SYNC_BACK_TARGETS = frozenset({"/blueprints", "/skills", "/jobs"})


async def _load_characters(db) -> list[Character]:
    return (
        (await db.execute(select(Character).order_by(Character.name))).scalars().all()
    )


def _selected_character(
    request: Request, characters: list[Character]
) -> Character | None:
    """The `?char=` filter: the matching tracked character, or None
    (absent, garbage, or an unknown id — all mean "every character")."""
    raw = request.query_params.get("char")
    if raw is None or not raw.strip():
        return None
    try:
        character_id = int(raw)
    except ValueError:
        return None
    return next(
        (
            character
            for character in characters
            if character.character_id == character_id
        ),
        None,
    )


@router.get("/blueprints")
async def character_blueprints_page(request: Request, db: DbDep, page: int = 1):
    """Every registered character's blueprints: type, ME/TE, runs
    (originals vs copies), location — the same shape as the corporation
    page, plus the owning character."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    selected = _selected_character(request, characters)
    owner_ids = [selected.character_id] if selected else None
    rows, total, used_page = await blueprints_page(
        db,
        owner_type=OWNER_CHARACTER,
        owner_ids=owner_ids,
        page=page,
        page_size=request.app.state.settings.assets_page_size,
    )
    notes, last = await character_sync_notes(
        db, KIND_CHAR_BLUEPRINTS, characters, owner_ids
    )
    return templates.TemplateResponse(
        request,
        "character_blueprints.html",
        {
            "authenticated": True,
            "active": "blueprints",
            "characters": characters,
            "selected": selected,
            "rows": rows,
            "total": total,
            "page": used_page,
            "pages": max(1, -(-total // request.app.state.settings.assets_page_size)),
            "sync_notes": notes,
            "last_sync_text": humanize_sync_age(last),
        },
    )


@router.get("/skills")
async def skills_page(request: Request, db: DbDep, page: int = 1):
    """Character skills. Without a `?char=` selection: one summary card
    per character (skill count, total SP, sync state). With one: that
    character's full sheet, name-ordered and paginated."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    selected = _selected_character(request, characters)
    if selected is None:
        summaries = await skill_summaries(db, characters)
        notes, last = await character_sync_notes(
            db, KIND_CHAR_SKILLS, characters, None
        )
        return templates.TemplateResponse(
            request,
            "character_skills.html",
            {
                "authenticated": True,
                "active": "skills",
                "characters": characters,
                "selected": None,
                "summaries": summaries,
                "sync_notes": notes,
                "last_sync_text": humanize_sync_age(last),
            },
        )

    rows, total, used_page = await character_skills(
        db,
        selected.character_id,
        page=page,
        page_size=request.app.state.settings.assets_page_size,
    )
    notes, last = await character_sync_notes(
        db, KIND_CHAR_SKILLS, characters, [selected.character_id]
    )
    return templates.TemplateResponse(
        request,
        "character_skills.html",
        {
            "authenticated": True,
            "active": "skills",
            "characters": characters,
            "selected": selected,
            "rows": rows,
            "total": total,
            "page": used_page,
            "pages": max(1, -(-total // request.app.state.settings.assets_page_size)),
            "sync_notes": notes,
            "last_sync_text": humanize_sync_age(last),
        },
    )


@router.get("/jobs")
async def character_jobs_page(
    request: Request, db: DbDep, page: int = 1, all: bool = False
):
    """Every registered character's industry jobs: active by default, the
    full history behind the toggle — the same shape as the corporation
    page, plus the owning character."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    selected = _selected_character(request, characters)
    owner_ids = [selected.character_id] if selected else None
    rows, total, used_page = await jobs_page(
        db,
        owner_type=OWNER_CHARACTER,
        owner_ids=owner_ids,
        include_completed=all,
        page=page,
        page_size=request.app.state.settings.assets_page_size,
    )
    notes, last = await character_sync_notes(
        db, KIND_CHAR_JOBS, characters, owner_ids
    )
    # The active/history toggle flips `all` and keeps the character filter.
    toggle_params = []
    if not all:
        toggle_params.append(("all", "1"))
    if selected:
        toggle_params.append(("char", str(selected.character_id)))
    toggle_url = "/jobs" + ("?" + urlencode(toggle_params) if toggle_params else "")
    return templates.TemplateResponse(
        request,
        "character_jobs.html",
        {
            "authenticated": True,
            "active": "jobs",
            "characters": characters,
            "selected": selected,
            "rows": rows,
            "total": total,
            "page": used_page,
            "pages": max(1, -(-total // request.app.state.settings.assets_page_size)),
            "show_all": all,
            "toggle_url": toggle_url,
            "sync_notes": notes,
            "last_sync_text": humanize_sync_age(last),
        },
    )


@router.post("/character/sync")
async def sync_character_data(request: Request, db: DbDep, esi: EsiDep):
    """The character data pages' Sync now: same per-character sync pass as
    the background tick, then back to the page that asked (whitelisted),
    keeping its character filter."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)

    characters = await _load_characters(db)
    settings = request.app.state.settings
    resolver = UniverseResolver(db, esi, settings=settings)
    await sync_all_characters(db, esi, characters, resolver=resolver)

    form = await request.form()
    back = form.get("back") or "/blueprints"
    if back not in SYNC_BACK_TARGETS:
        back = "/blueprints"
    # Carry the page's own state back: the character filter and the jobs
    # history toggle (a sync that silently reverts the view reads as data
    # loss).
    params = []
    char = form.get("char")
    if char is not None and char.strip().isdigit():
        params.append(("char", str(int(char))))
    if form.get("all") == "1":
        params.append(("all", "1"))
    target = back + ("?" + urlencode(params) if params else "")
    return RedirectResponse(target, status_code=303)
