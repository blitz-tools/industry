"""Callback flow tests: happy path, state handling, upsert semantics."""

from urllib.parse import parse_qs, urlparse

import respx
from sqlalchemy import select

from app.models import Character
from tests.conftest import token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
WALLET_URL = "https://esi.test/latest/characters/1234/wallet/"


def _extract_state(redirect_url: str) -> str:
    return parse_qs(urlparse(redirect_url).query)["state"][0]


async def _start_login(client) -> str:
    response = await client.get("/auth/eve/login", follow_redirects=False)
    assert response.status_code == 302
    return _extract_state(response.headers["location"])


@respx.mock
async def test_callback_happy_path(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    respx.get(WALLET_URL).respond(json=4321.5)
    state = await _start_login(client)

    response = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": state}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"

    character = await db_session.get(Character, 1234)
    assert character is not None
    assert character.name == "Test Pilot"
    assert character.owner_hash == "owner-hash-1"
    assert character.refresh_token == "R1"
    assert character.access_token  # JWT from the mocked exchange

    dashboard = await client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Test Pilot" in dashboard.text
    assert "4,321.50" in dashboard.text


@respx.mock
async def test_callback_state_mismatch_writes_nothing(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    await _start_login(client)

    response = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": "forged"}
    )
    assert response.status_code == 400

    rows = (await db_session.execute(select(Character))).scalars().all()
    assert rows == []


@respx.mock
async def test_callback_missing_code(client):
    state = await _start_login(client)
    response = await client.get("/auth/eve/callback", params={"state": state})
    assert response.status_code == 400


@respx.mock
async def test_callback_state_is_one_shot(client, db_session):
    """A replayed callback with the same state must be rejected."""
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    state = await _start_login(client)

    first = await client.get("/auth/eve/callback", params={"code": "abc", "state": state})
    assert first.status_code == 302

    replay = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": state}
    )
    assert replay.status_code == 400


@respx.mock
async def test_callback_token_exchange_failure(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(status_code=502, json={"error": "server_error"})
    state = await _start_login(client)

    response = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": state}
    )
    assert response.status_code == 502
    rows = (await db_session.execute(select(Character))).scalars().all()
    assert rows == []


@respx.mock
async def test_reauth_with_changed_owner_hash_overwrites_tokens(client, db_session):
    """Owner-hash change = character transferred; old grants replaced."""
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    respx.post(SSO_TOKEN_URL).respond(
        json=token_response(owner="new-owner", refresh_token="R2", name="Renamed")
    )
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    characters = (await db_session.execute(select(Character))).scalars().all()
    assert len(characters) == 1
    character = characters[0]
    assert character.owner_hash == "new-owner"
    assert character.refresh_token == "R2"
    assert character.name == "Renamed"


@respx.mock
async def test_dashboard_requires_login(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    respx.get(WALLET_URL).respond(json=0.0)

    unauthenticated = await client.get("/dashboard")
    assert unauthenticated.status_code == 302
    assert unauthenticated.headers["location"] == "/"

    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})
    assert (await client.get("/dashboard")).status_code == 200

    # Logout keeps the DB row; the page is gated again until re-login.
    await client.get("/auth/logout")
    gated = await client.get("/dashboard")
    assert gated.status_code == 302
    assert await db_session.get(Character, 1234) is not None


@respx.mock
async def test_forget_removes_character(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    revoke = respx.post("https://sso.test/v2/oauth/revoke").respond(status_code=200)
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.post("/characters/1234/forget")
    assert response.status_code == 303
    assert await db_session.get(Character, 1234) is None
    assert revoke.called


@respx.mock
async def test_forget_tolerates_revoke_failure(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    respx.post("https://sso.test/v2/oauth/revoke").respond(status_code=500)
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.post("/characters/1234/forget")
    assert response.status_code == 303
    assert await db_session.get(Character, 1234) is None
