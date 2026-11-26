"""Page routes: index, dashboard overview, character roster."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import utc_now
from ..deps import DbDep, EsiDep, is_authenticated, make_esi_client
from ..esi.client import ESIClient, ESIError, ReauthorizationRequired
from ..esi.universe import corporation_name
from ..models import Character
from ..plans import roster_eligibility
from ..templates import portrait_url, templates

router = APIRouter()

# Roman numerals for skill levels (EVE training caps at V).
_SKILL_LEVELS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}

# Scopes behind the roster's live metadata. Endpoints are only called when
# the stored grant covers them: a scopeless call is a guaranteed 403, and
# 403s burn ESI's error-limit budget (same rule as the asset sync).
LOCATION_SCOPE = "esi-location.read_location.v1"
SKILLQUEUE_SCOPE = "esi-skills.read_skillqueue.v1"


def _has_scope(character: Character, scope: str) -> bool:
    return scope in character.scopes.split()


def _parse_esi_date(value: str | None) -> datetime | None:
    """ISO-8601 (ESI sends UTC with a Z suffix) to naive UTC, or None."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


async def _load_characters(db: AsyncSession) -> list[Character]:
    return (await db.execute(select(Character).order_by(Character.name))).scalars().all()


@router.get("/")
async def index(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "index.html", {"authenticated": False})


@dataclass
class CardIssue:
    """One message in a roster card's notification box. `detail` joins the
    box's hover tooltip; severity picks the message's color class."""

    message: str
    detail: str | None = None
    severity: str = "info"  # "info" | "error"


@dataclass
class CharacterCard:
    """View-model for one character tile on the roster page."""

    character: Character
    portrait: str
    wallet: float | None
    needs_reauth: bool
    corporation_name: str | None
    alliance_name: str | None  # None: no alliance, or unresolved
    location_name: str | None  # current system; None without the scope
    training: str | None  # skill in progress, or None
    # The assignment-eligibility view (M6): {holds, total, plans} for
    # characters pinned into at least one active plan — plans carries
    # {id, name, target_type_id} per plan for the participation block;
    # with active plans elsewhere, None reads "not in an active plan's
    # pool", and with no active plans at all the active_plans flag
    # carries the "no active plans" line.
    plan_view: dict | None
    active_plans: bool
    # Notification-box messages; non-empty also tints the card background.
    issues: list[CardIssue] = field(default_factory=list)

    @property
    def issue_tooltip(self) -> str | None:
        """Combined hover text for the notification box."""
        details = [issue.detail for issue in self.issues if issue.detail]
        return "\n".join(details) or None


async def _corporation_name(
    esi: ESIClient, db, corporation_id: int | None
) -> str | None:
    return await corporation_name(db, esi, corporation_id)


async def _alliance_name(esi: ESIClient, alliance_id: int | None) -> str | None:
    if not alliance_id:
        return None
    try:
        return (await esi.get_public(f"/alliances/{alliance_id}/")).get("name")
    except ESIError:
        return None


async def _location_name(esi: ESIClient, character: Character) -> str | None:
    """Current system name. Needs the location scope; characters authorized
    before that scope was registered degrade to None rather than failing."""
    try:
        body = await esi.get(character, "/characters/{character_id}/location/")
        system_id = body.get("solar_system_id")
        if not system_id:
            return None
        return (await esi.get_public(f"/universe/systems/{system_id}/")).get("name")
    except (ReauthorizationRequired, ESIError):
        return None


async def _training_summary(esi: ESIClient, character: Character) -> str | None:
    """The skill in progress (name + target level), "Paused" when the queue
    holds skills but none are training (an Omega-lapsed character's queue:
    entries with no finish date), or None when unknown or empty. Needs the
    skill-queue scope; same degradation as the location."""
    try:
        queue = await esi.get(character, "/characters/{character_id}/skillqueue/")
    except (ReauthorizationRequired, ESIError):
        return None
    entry = _current_queue_entry(queue)
    if entry is None:
        return "Paused" if queue else None
    level = _SKILL_LEVELS.get(entry.get("finished_level"))
    try:
        name = (await esi.get_public(f"/universe/types/{entry['skill_id']}/")).get(
            "name"
        )
    except (ESIError, KeyError):
        return None
    return f"{name} {level}" if level else name


def _current_queue_entry(queue: list[dict]) -> dict | None:
    """First entry whose finish date is still ahead: the skill in progress,
    or the next one up when the queue is paused. ESI's field is finish_date
    (not finished_date, unlike finished_level)."""
    now = utc_now()
    for entry in sorted(queue, key=lambda e: e.get("queue_position", 0)):
        finished = _parse_esi_date(entry.get("finish_date"))
        if finished is not None and finished > now:
            return entry
    return None


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
async def characters_page(request: Request, db: DbDep):
    """Character roster: grid of cards with wallet and character metadata.

    Cards resolve in parallel, each with its own DB session + ESI client —
    a single AsyncSession cannot be shared across concurrent tasks. The
    plan-eligibility line is DB-pure, so it reads the route's own session
    before the cards fan out."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)

    characters = await _load_characters(db)
    eligibility = await roster_eligibility(
        db, [character.character_id for character in characters]
    )
    cards = [
        card
        for card in await asyncio.gather(
            *(
                _build_card(
                    request,
                    character.character_id,
                    eligibility.get(character.character_id)
                    if eligibility is not None
                    else None,
                    eligibility is not None,
                )
                for character in characters
            )
        )
        if card is not None
    ]

    return templates.TemplateResponse(
        request,
        "characters.html",
        {"authenticated": True, "active": "characters", "cards": cards},
    )


async def _build_card(
    request: Request,
    character_id: int,
    plan_view: dict | None,
    active_plans: bool,
) -> CharacterCard | None:
    """Fetch one character's roster metadata with a private session. None
    means the character was forgotten mid-render — its card is skipped.
    `plan_view` and `active_plans` ride along from the route's DB-pure
    read (the private session is for ESI-backed metadata, not plan
    queries)."""
    async with request.app.state.session_factory() as session:
        character = await session.get(Character, character_id)
        if character is None:
            return None
        esi = make_esi_client(request, session)
        card = CharacterCard(
            character=character,
            portrait=portrait_url(character.character_id, 256),
            wallet=None,
            needs_reauth=False,
            corporation_name=None,
            alliance_name=None,
            location_name=None,
            training=None,
            plan_view=plan_view,
            active_plans=active_plans,
        )
        try:
            card.wallet = await esi.get_wallet_balance(character)
        except (ReauthorizationRequired, ESIError):
            card.needs_reauth = True
        # Corporation and alliance are public data: they resolve even when
        # the character needs re-authorization.
        try:
            info = await esi.get_public(f"/characters/{character.character_id}/")
        except ESIError:
            info = None
        if info:
            corporation_id = info.get("corporation_id")
            if corporation_id and corporation_id != character.corporation_id:
                # Persist membership (assets-page grouping reads it without
                # touching ESI).
                character.corporation_id = corporation_id
                await session.commit()
            card.corporation_name = await _corporation_name(esi, session, corporation_id)
            card.alliance_name = await _alliance_name(esi, info.get("alliance_id"))
        if not card.needs_reauth:
            if _has_scope(character, LOCATION_SCOPE):
                card.location_name = await _location_name(esi, character)
            if _has_scope(character, SKILLQUEUE_SCOPE):
                card.training = await _training_summary(esi, character)
        # Notification box: anything wrong with this character's grant.
        if card.needs_reauth:
            card.issues.append(CardIssue("Needs re-authorization", severity="error"))
        # Scopes the app now requests that this grant predates.
        missing = sorted(
            set(request.app.state.settings.esi_scopes) - set(character.scopes.split())
        )
        if missing:
            card.issues.append(
                CardIssue(
                    f"Scopes out of sync ({len(missing)}) — Re-Auth to update",
                    detail="Missing: " + ", ".join(missing),
                )
            )
        return card


@router.post("/characters/{character_id}/main")
async def set_main(character_id: int, request: Request, db: DbDep):
    """Mark one character as the main; any previous main is demoted.
    Single-user app: exactly one main defines which corporation the
    Corporation section targets."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)

    character = await db.get(Character, character_id)
    if character is not None:
        await db.execute(
            update(Character).where(Character.is_main).values(is_main=False)
        )
        character.is_main = True
        await db.commit()
    # Set-main lives on the roster; stay there.
    return RedirectResponse("/characters", status_code=303)
