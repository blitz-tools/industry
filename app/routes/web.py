"""Page routes: index and dashboard."""

from dataclasses import dataclass

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..deps import DbDep, EsiDep, is_authenticated
from ..esi.client import ESIError, ReauthorizationRequired
from ..models import Character
from ..templates import portrait_url, templates

router = APIRouter()


@router.get("/")
async def index(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "index.html", {})


@dataclass
class CharacterCard:
    """View-model for one dashboard card."""

    character: Character
    portrait: str
    wallet: float | None
    needs_reauth: bool


@router.get("/dashboard")
async def dashboard(request: Request, db: DbDep, esi: EsiDep):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = (
        (await db.execute(select(Character).order_by(Character.name))).scalars().all()
    )
    cards: list[CharacterCard] = []
    for character in characters:
        card = CharacterCard(
            character=character,
            portrait=portrait_url(character.character_id),
            wallet=None,
            needs_reauth=False,
        )
        try:
            # Demo call proving the full token chain works; a failing
            # character must not break the rest of the page.
            card.wallet = await esi.get_wallet_balance(character)
        except (ReauthorizationRequired, ESIError):
            card.needs_reauth = True
        cards.append(card)

    return templates.TemplateResponse(request, "dashboard.html", {"cards": cards})
