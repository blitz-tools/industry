"""EVE SSO auth routes: login, callback, logout, forget."""

import hmac
import secrets
from datetime import timedelta

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import utc_now
from ..deps import DbDep, HttpDep
from ..esi.assets import OWNER_CHARACTER
from ..esi.etag import purge_character
from ..esi.sso import (
    CharacterClaims,
    SSOClient,
    SSOError,
    TokenResponse,
    decode_access_token,
)
from ..models import Asset, AssetSync, Character
from ..templates import templates

router = APIRouter()

STATE_SESSION_KEY = "sso_state"


def sso_from(request: Request, http) -> SSOClient:
    return SSOClient(http, request.app.state.settings)


async def upsert_character(
    db: AsyncSession, claims: CharacterClaims, tokens: TokenResponse
) -> Character:
    """Create or update the character row for these claims.

    A changed owner_hash means the character was transferred between EVE
    accounts; the previous owner's grants are void, so tokens are overwritten
    wholesale either way.
    """
    character = await db.get(Character, claims.character_id)
    if character is None:
        character = Character(character_id=claims.character_id)
        db.add(character)
    elif character.owner_hash != claims.owner_hash:
        # Transfer: the previous owner's cached ESI responses belong to a
        # different grant; drop them so nothing stale is ever served.
        await purge_character(db, claims.character_id)
    character.name = claims.name
    character.owner_hash = claims.owner_hash
    character.scopes = " ".join(claims.scopes)
    character.access_token = tokens.access_token
    character.refresh_token = tokens.refresh_token
    character.access_token_expires_at = utc_now() + timedelta(seconds=tokens.expires_in)
    await db.commit()
    await db.refresh(character)
    return character


@router.get("/auth/eve/login")
async def login(request: Request, http: HttpDep):
    """Start the OAuth flow. Also used as "Add character" — EVE's SSO screen
    lets the user pick a different character (or account) each time."""
    state = secrets.token_urlsafe(24)
    request.session[STATE_SESSION_KEY] = state
    return RedirectResponse(sso_from(request, http).authorize_url(state), status_code=302)


@router.get("/auth/eve/callback")
async def callback(
    request: Request,
    http: HttpDep,
    db: DbDep,
    code: str | None = None,
    state: str | None = None,
):
    expected = request.session.pop(STATE_SESSION_KEY, None)  # one-shot
    if code is None or state is None or expected is None:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "authenticated": False,
                "message": "Missing code or state in the SSO response.",
            },
            status_code=400,
        )
    if not hmac.compare_digest(state, expected):
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "authenticated": False,
                "message": "SSO state mismatch — please try signing in again.",
            },
            status_code=400,
        )

    sso = sso_from(request, http)
    try:
        tokens = await sso.exchange_code(code)
        claims = decode_access_token(tokens.access_token)
    except SSOError as exc:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"authenticated": False, "message": f"EVE SSO error: {exc}"},
            status_code=502,
        )

    await upsert_character(db, claims, tokens)
    request.session["authenticated"] = True
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/auth/logout")
async def logout(request: Request):
    """Clear the browser session only; character rows and their refresh
    tokens survive, so the next login shows every authorized character."""
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@router.post("/characters/{character_id}/forget")
async def forget(character_id: int, request: Request, http: HttpDep, db: DbDep):
    character = await db.get(Character, character_id)
    if character is not None:
        sso = sso_from(request, http)
        try:
            await sso.revoke(character.refresh_token)
        except SSOError:
            pass  # best-effort; drop the row regardless
        await db.delete(character)
        # Their asset snapshot and sync state go with the character.
        await db.execute(
            delete(Asset).where(
                Asset.owner_type == OWNER_CHARACTER, Asset.owner_id == character_id
            )
        )
        await db.execute(
            delete(AssetSync).where(
                AssetSync.owner_type == OWNER_CHARACTER,
                AssetSync.owner_id == character_id,
            )
        )
        await db.commit()
    return RedirectResponse("/dashboard", status_code=303)
