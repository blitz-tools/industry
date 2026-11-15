"""Corporation section: the overview page and the (still stub) sub-pages.

The section targets exactly one corporation — the main character's (see
`Character.is_main`). The overview resolves that corporation and runs the
role gate: the main's tokens stand in for the corp on corp-scoped ESI
calls, which only works while they hold Director or CEO. Sub-pages stay
inaccessible until the gate passes, so users never hit guaranteed-403
syncs; every failure mode gets an explanatory state on the overview
instead (same philosophy as restricted-structure parking).

The overview's live lookups (public character/corporation data, the
roles call) go through the ETag cache, so repeat renders are cheap.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..deps import DbDep, EsiDep, is_authenticated
from ..esi.client import ESIError
from ..esi.roles import CorpAccess, check_corp_access
from ..esi.universe import corporation_name
from ..models import Character
from ..templates import templates

router = APIRouter()

CORP_PAGES = {
    "assets": "Assets",
    "jobs": "Jobs",
    "wallets": "Wallets",
    "blueprints": "Blueprints",
}


async def _load_main(db) -> Character | None:
    return (
        await db.execute(select(Character).where(Character.is_main))
    ).scalar_one_or_none()


async def _resolve_corporation(db, esi, main: Character) -> tuple[int | None, str | None]:
    """The main's corporation id (public data, persisted for ESI-free
    pages) and its live name."""
    corporation_id = main.corporation_id
    if corporation_id is None:
        try:
            info = await esi.get_public(f"/characters/{main.character_id}/")
            corporation_id = info.get("corporation_id")
        except ESIError:
            corporation_id = None
        if corporation_id is not None:
            main.corporation_id = corporation_id
            await db.commit()
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
