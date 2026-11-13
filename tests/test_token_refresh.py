"""Token refresh tests: rotation persistence, fast path, invalid_grant."""

from datetime import timedelta

import respx

from app.db import utc_now
from app.models import Character
from tests.conftest import token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
WALLET_URL = "https://esi.test/latest/characters/1234/wallet/"


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    from urllib.parse import parse_qs, urlparse

    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _seed_expired_character(db_session) -> Character:
    character = await db_session.get(Character, 1234)
    character.access_token = "stale-token"
    character.access_token_expires_at = utc_now() - timedelta(minutes=5)
    await db_session.commit()
    return character


@respx.mock
async def test_expired_token_triggers_rotation_and_persists(client, db_session):
    await _login(client)
    await _seed_expired_character(db_session)

    wallet = respx.get(WALLET_URL).respond(json=4321.5)
    respx.post(SSO_TOKEN_URL).respond(
        json={
            "access_token": "A2",
            "refresh_token": "R2",
            "expires_in": 1199,
        }
    )

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "4,321.50" in response.text

    # The wallet call used the refreshed token…
    assert wallet.calls.last.request.headers["Authorization"] == "Bearer A2"
    # …and rotation was persisted. expire_all() drops the assertion session's
    # cached instance so we read what the app actually committed.
    db_session.expire_all()
    character = await db_session.get(Character, 1234)
    assert character.refresh_token == "R2"
    assert character.access_token == "A2"


@respx.mock
async def test_fresh_token_skips_refresh_endpoint(client, db_session):
    await _login(client)

    # Any call to the token endpoint during the dashboard request proves a
    # needless refresh. Snapshot the count first: the login exchange above
    # legitimately hit this route, and a route without a response would make
    # an actual refresh fail loudly anyway.
    token_route = respx.post(SSO_TOKEN_URL)
    calls_before = len(token_route.calls)
    respx.get(WALLET_URL).respond(json=99.0)

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "99.00" in response.text
    assert len(token_route.calls) == calls_before


@respx.mock
async def test_invalid_grant_renders_reauth_not_failure(client, db_session):
    await _login(client)
    await _seed_expired_character(db_session)

    respx.post(SSO_TOKEN_URL).respond(status_code=400, json={"error": "invalid_grant"})

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "re-authorize" in response.text
    # Row is kept so the user can re-authorize the same character.
    assert await db_session.get(Character, 1234) is not None
