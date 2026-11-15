"""Main character tests: the is_main flag and its roster action, and the
Corporation overview's role gating (no-main / no-scope / insufficient /
ok) plus the gated sub-pages.

Corp-overview states that need no ESI are asserted ESI-free (respx
raises on unmatched calls); the roles endpoint must never be called
without the scope — that's the error-budget rule the gate exists for.
"""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import respx
from sqlalchemy import select

from app.db import utc_now
from app.models import Character
from tests.conftest import make_access_token, mock_roster_metadata, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
WALLET_URL = "https://esi.test/latest/characters/1234/wallet/"
ROLES_URL = "https://esi.test/latest/characters/1234/roles/"

ALPHA = 1234  # created via the SSO login flow
BRAVO = 5678

CORP_ID = 98000001
CORP_URL = f"https://esi.test/latest/corporations/{CORP_ID}/"
PUBLIC_CHAR_URL = "https://esi.test/latest/characters/1234/"

# A grant that covers the roles scope (the default test set predates it).
ROLES_GRANT = ["publicData", "esi-characters.read_corporation_roles.v1"]


async def _login(client, scopes=None):
    """Create character ALPHA through the real SSO flow; `scopes` overrides
    the grant's scope set (the roles scope predates the default set)."""
    access_token = make_access_token(scopes=scopes) if scopes is not None else None
    respx.post(SSO_TOKEN_URL).respond(
        json=token_response(access_token=access_token)
    )
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _seed_bravo(db_session, *, is_main=False) -> Character:
    bravo = Character(
        character_id=BRAVO,
        name="Bravo Pilot",
        owner_hash="owner-bravo",
        scopes="publicData esi-assets.read_assets.v1",
        access_token="tok-bravo",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R-bravo",
        is_main=is_main,
    )
    db_session.add(bravo)
    await db_session.commit()
    return bravo


async def _set_main(client, character_id: int):
    return await client.post(
        f"/characters/{character_id}/main", follow_redirects=False
    )


@respx.mock
async def test_set_main_and_switch(client, db_session):
    await _login(client)
    await _seed_bravo(db_session)

    response = await _set_main(client, BRAVO)
    assert response.status_code == 303
    assert response.headers["location"] == "/characters"
    # Column tuples, not ORM objects: bravo lives in this session's
    # identity map from seeding, and the app's session changed the flag.
    flags = dict(
        (
            await db_session.execute(
                select(Character.character_id, Character.is_main)
            )
        ).all()
    )
    assert flags == {ALPHA: False, BRAVO: True}

    # Switching mains demotes the previous one — exactly one main.
    await _set_main(client, ALPHA)
    flags = dict(
        (
            await db_session.execute(
                select(Character.character_id, Character.is_main)
            )
        ).all()
    )
    assert flags == {ALPHA: True, BRAVO: False}


@respx.mock
async def test_set_main_requires_auth(client, db_session):
    await _seed_bravo(db_session)

    response = await client.post("/characters/5678/main", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    bravo = await db_session.get(Character, BRAVO)
    assert bravo.is_main is False


@respx.mock
async def test_set_main_unknown_character(client):
    await _login(client)
    response = await _set_main(client, 999999)
    assert response.status_code == 303
    assert response.headers["location"] == "/characters"


@respx.mock
async def test_roster_shows_main_badge(client):
    await _login(client)
    await _set_main(client, ALPHA)
    respx.get(WALLET_URL).respond(json=4321.5)
    mock_roster_metadata()

    response = await client.get("/characters")
    assert response.status_code == 200
    assert "main-badge" in response.text
    assert 'aria-label="Set as main"' not in response.text


@respx.mock
async def test_roster_shows_set_as_main_button(client):
    await _login(client)
    respx.get(WALLET_URL).respond(json=4321.5)
    mock_roster_metadata()

    response = await client.get("/characters")
    assert response.status_code == 200
    assert 'aria-label="Set as main"' in response.text
    assert "main-badge" not in response.text


@respx.mock
async def test_corp_overview_no_main(client):
    await _login(client)

    response = await client.get("/corp")
    assert response.status_code == 200
    assert "No main character selected" in response.text


@respx.mock
async def test_corp_overview_no_scope(client, db_session):
    """A main whose grant predates the roles scope gets an explanatory
    state — and the roles endpoint is never called."""
    await _login(client)
    await _set_main(client, ALPHA)
    respx.get(PUBLIC_CHAR_URL).respond(json={"corporation_id": CORP_ID})
    respx.get(CORP_URL).respond(json={"name": "Blitz Holdings"})
    roles_route = respx.get(ROLES_URL).respond(json={"roles": ["Director"]})

    response = await client.get("/corp")
    assert response.status_code == 200
    assert "missing the roles scope" in response.text
    assert "Re-Auth" in response.text
    assert roles_route.call_count == 0
    # The corporation resolved and persisted for ESI-free renders.
    alpha = await db_session.get(Character, ALPHA)
    assert alpha.corporation_id == CORP_ID


@respx.mock
async def test_corp_overview_director_ok(client, db_session):
    await _login(client, scopes=ROLES_GRANT)
    await _set_main(client, ALPHA)
    # Stored corporation membership skips the public character lookup.
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()
    respx.get(CORP_URL).respond(json={"name": "Blitz Holdings"})
    respx.get(ROLES_URL).respond(json={"roles": ["Director", "Personnel_Manager"]})

    response = await client.get("/corp")
    assert response.status_code == 200
    assert "Blitz Holdings" in response.text
    assert "Director" in response.text
    assert "role confirmed" in response.text


@respx.mock
async def test_corp_overview_ceo_ok(client, db_session):
    await _login(client, scopes=ROLES_GRANT)
    await _set_main(client, ALPHA)
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()
    respx.get(CORP_URL).respond(json={"name": "Blitz Holdings"})
    respx.get(ROLES_URL).respond(json={"roles": ["CEO"]})

    response = await client.get("/corp")
    assert response.status_code == 200
    assert "role confirmed" in response.text


@respx.mock
async def test_corp_overview_insufficient_roles(client, db_session):
    await _login(client, scopes=ROLES_GRANT)
    await _set_main(client, ALPHA)
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()
    respx.get(CORP_URL).respond(json={"name": "Blitz Holdings"})
    respx.get(ROLES_URL).respond(json={"roles": ["Personnel_Manager"]})

    response = await client.get("/corp")
    assert response.status_code == 200
    assert "no Director or CEO role" in response.text


@respx.mock
async def test_corp_subpages_gated(client, db_session):
    """Sub-pages redirect to the overview until the role gate passes,
    then render their (still stub) content."""
    await _login(client, scopes=ROLES_GRANT)
    await _set_main(client, ALPHA)

    # No roles: redirected to the overview even with the right scope.
    roles_route = respx.get(ROLES_URL).respond(json={"roles": []})
    response = await client.get("/corp/assets", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/corp"

    # Re-respond on the same route (a second respx.get would never match:
    # routes are checked in registration order).
    roles_route.respond(json={"roles": ["Director"]})
    # /corp/assets is the real corporation browser now; its corporation
    # comes from stored membership (no ESI beyond the roles gate).
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()
    response = await client.get("/corp/assets")
    assert response.status_code == 200
    assert "Corporation Assets" in response.text

    # The remaining sub-pages: jobs is real now, wallets is still a stub.
    response = await client.get("/corp/jobs")
    assert response.status_code == 200
    assert "Corporation Jobs" in response.text

    response = await client.get("/corp/wallets")
    assert response.status_code == 200
    assert "Not built yet" in response.text

    # Unknown corp page stays a 404 either way.
    response = await client.get("/corp/nonsense")
    assert response.status_code == 404
