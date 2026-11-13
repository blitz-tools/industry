"""Page routes: index, dashboard overview, characters management."""

from dataclasses import dataclass

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import DbDep, EsiDep, is_authenticated
from ..esi.client import ESIError, ReauthorizationRequired
from ..models import Character
from ..templates import portrait_url, templates

router = APIRouter()


async def _load_characters(db: AsyncSession) -> list[Character]:
    return (await db.execute(select(Character).order_by(Character.name))).scalars().all()


@router.get("/")
async def index(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "index.html", {"authenticated": False})


@dataclass
class CharacterCard:
    """View-model for one character tile on the Characters page."""

    character: Character
    portrait: str
    wallet: float | None
    needs_reauth: bool


@router.get("/dashboard")
async def dashboard(request: Request, db: DbDep, esi: EsiDep):
    """Sparse overview: totals across all stored characters."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    total_wallet = 0.0
    unavailable = 0
    for character in characters:
        try:
            # Cheap under the ETag cache's fresh window.
            total_wallet += await esi.get_wallet_balance(character)
        except (ReauthorizationRequired, ESIError):
            unavailable += 1

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "authenticated": True,
            "active": "dashboard",
            "total_wallet": total_wallet,
            "character_count": len(characters),
            "account_count": len({c.owner_hash for c in characters}),
            "unavailable": unavailable,
        },
    )


@router.get("/characters")
async def characters_page(request: Request, db: DbDep, esi: EsiDep):
    """Character management: grid of cards plus the add-character tile."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    cards: list[CharacterCard] = []
    for character in await _load_characters(db):
        card = CharacterCard(
            character=character,
            portrait=portrait_url(character.character_id, 256),
            wallet=None,
            needs_reauth=False,
        )
        try:
            card.wallet = await esi.get_wallet_balance(character)
        except (ReauthorizationRequired, ESIError):
            card.needs_reauth = True
        cards.append(card)

    return templates.TemplateResponse(
        request,
        "characters.html",
        {"authenticated": True, "active": "characters", "cards": cards},
    )
