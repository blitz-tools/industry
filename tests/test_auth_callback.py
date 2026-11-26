"""Callback flow tests: happy path, state handling, upsert semantics."""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import create_app
from app.models import Character, UniverseCorporation
from tests.conftest import (
    TEST_SETTINGS,
    make_access_token,
    mock_roster_metadata,
    token_response,
)

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
    mock_roster_metadata()
    state = await _start_login(client)

    response = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": state}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"  # plain sign-in

    character = await db_session.get(Character, 1234)
    assert character is not None
    assert character.name == "Test Pilot"
    assert character.owner_hash == "owner-hash-1"
    assert character.refresh_token == "R1"
    assert character.access_token  # JWT from the mocked exchange

    dashboard = await client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "4,321.50" in dashboard.text  # single character: total == its wallet

    characters = await client.get("/characters")
    assert characters.status_code == 200
    assert "Test Pilot" in characters.text
    assert "4,321.50" in characters.text
    assert "Add character" in characters.text
    # Row metadata: corporation is the panel header, the rest labeled
    # (muted label span, white value span).
    assert "Federal Freight" in characters.text
    assert '<span class="meta-label">Alliance:</span>' in characters.text
    assert '<span class="meta-value">Eve University</span>' in characters.text
    assert '<span class="meta-label">Location:</span>' in characters.text
    assert '<span class="meta-value">Jita</span>' in characters.text
    assert '<span class="meta-label">Training:</span>' in characters.text
    assert '<span class="meta-value">Hull Upgrades V</span>' in characters.text
    assert "Corporation:" not in characters.text
    assert 'aria-label="Re-Auth"' in characters.text  # per-card re-auth button
    # Roster auth buttons return to the roster after the SSO round trip.
    assert characters.text.count('href="/auth/eve/login?next=/characters"') == 2
    # Authorized against the current scope list: no issues, so no
    # notification box and no issue tint.
    assert "Scopes out of sync" not in characters.text
    assert 'class="notify"' not in characters.text
    assert "has-issue" not in characters.text
    # The roster render persists corporation membership + name, so the
    # assets page can group by corporation without touching ESI.
    db_session.expire_all()
    character = await db_session.get(Character, 1234)
    assert character.corporation_id == 98000001
    corp = await db_session.get(UniverseCorporation, 98000001)
    assert corp is not None and corp.name == "Federal Freight"


@respx.mock
async def test_login_next_returns_to_roster(client, db_session):
    """?next=/characters (the roster's Re-Auth / Add-character buttons)
    lands back on the roster; a plain sign-in keeps the dashboard, and
    unknown destinations fall back rather than redirecting off-site."""
    respx.post(SSO_TOKEN_URL).respond(json=token_response())

    response = await client.get(
        "/auth/eve/login", params={"next": "/characters"}, follow_redirects=False
    )
    state = _extract_state(response.headers["location"])
    response = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": state}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/characters"

    # Open-redirect guard: anything not whitelisted falls back.
    response = await client.get(
        "/auth/eve/login", params={"next": "https://evil.example"}, follow_redirects=False
    )
    state = _extract_state(response.headers["location"])
    response = await client.get(
        "/auth/eve/callback", params={"code": "abc", "state": state}
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


@respx.mock
async def test_roster_degrades_when_scope_missing(client, db_session):
    """Location/skill-queue 403 (a character authorized before those scopes
    were registered) renders em-dashes, not a page failure."""
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    respx.get(WALLET_URL).respond(json=10.0)
    mock_roster_metadata()
    respx.get("https://esi.test/latest/characters/1234/location/").respond(
        status_code=403, json="forbidden"
    )
    respx.get("https://esi.test/latest/characters/1234/skillqueue/").respond(
        status_code=403, json="forbidden"
    )
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.get("/characters")

    assert response.status_code == 200
    assert '<span class="meta-label">Location:</span>' in response.text
    assert '<span class="meta-value">—</span>' in response.text
    assert '<span class="meta-label">Training:</span>' in response.text
    assert "Federal Freight" in response.text  # public data is unaffected


@respx.mock
async def test_roster_skips_calls_without_scope(client, db_session):
    """Location/skill-queue endpoints are not called when the stored grant
    lacks those scopes — a scopeless call is a guaranteed 403 and burns
    ESI's error-limit budget."""
    respx.post(SSO_TOKEN_URL).respond(
        json=token_response(
            access_token=make_access_token(
                scopes=["publicData", "esi-wallet.read_character_wallet.v1"]
            )
        )
    )
    respx.get(WALLET_URL).respond(json=10.0)
    routes = mock_roster_metadata()
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.get("/characters")

    assert response.status_code == 200
    assert routes["location"].call_count == 0
    assert routes["skillqueue"].call_count == 0
    assert '<span class="meta-label">Location:</span>' in response.text
    assert '<span class="meta-value">—</span>' in response.text
    assert '<span class="meta-label">Training:</span>' in response.text
    # The row is issue-tinted, and its notification box flags the grant
    # as predating the current scope list — the whole box carries the
    # missing-scope tooltip.
    assert 'class="roster-row has-issue"' in response.text
    assert 'class="notify"' in response.text
    assert "Scopes out of sync (3)" in response.text
    assert 'title="Missing: esi-assets.read_assets.v1' in response.text


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
async def test_pages_require_login(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    respx.get(WALLET_URL).respond(json=0.0)
    mock_roster_metadata()

    for path in ("/dashboard", "/characters"):
        unauthenticated = await client.get(path)
        assert unauthenticated.status_code == 302
        assert unauthenticated.headers["location"] == "/"

    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})
    assert (await client.get("/dashboard")).status_code == 200
    assert (await client.get("/characters")).status_code == 200

    # Logout keeps the DB row; the pages are gated again until re-login.
    await client.get("/auth/logout")
    gated = await client.get("/dashboard")
    assert gated.status_code == 302
    assert await db_session.get(Character, 1234) is not None


@respx.mock
async def test_index_renders_login_page_when_unauthenticated(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "Sign in with EVE Online" in response.text
    # No sidebar chrome on the login page.
    assert "sidebar" not in response.text


@respx.mock
async def test_dashboard_counts_accounts(client, db_session):
    """Two characters sharing an owner hash are one account."""
    respx.post(SSO_TOKEN_URL).mock(
        side_effect=[
            httpx.Response(200, json=token_response()),  # first login: 1234
            httpx.Response(  # second login: 5678, same owner hash
                200, json=token_response(character_id=5678, name="Alt Pilot")
            ),
        ]
    )
    respx.get("https://esi.test/latest/characters/1234/wallet/").respond(json=100.0)
    respx.get("https://esi.test/latest/characters/5678/wallet/").respond(json=50.0)

    for _ in range(2):
        state = await _start_login(client)
        await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "150.00" in response.text  # summed total
    assert '<p class="stat-value">2</p>' in response.text
    assert "characters" in response.text
    assert '<p class="stat-value">1</p>' in response.text
    assert "EVE account" in response.text


@respx.mock
async def test_forget_removes_character(client, db_session):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    revoke = respx.post("https://sso.test/v2/oauth/revoke").respond(status_code=200)
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.post("/characters/1234/forget")
    assert response.status_code == 303
    assert response.headers["location"] == "/characters"  # stay on the roster
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
    assert response.headers["location"] == "/characters"
    assert await db_session.get(Character, 1234) is None


async def test_dev_auto_reload_gated_by_flag(app, client):
    """The dev-version endpoint and refresh script exist only when
    DEV_AUTO_RELOAD is set; production never serves either."""
    # Default app (TEST_SETTINGS): neither endpoint nor script.
    assert (await client.get("/__dev/version")).status_code == 404
    assert "dev-reload.js" not in (await client.get("/")).text

    dev_app = create_app(TEST_SETTINGS.model_copy(update={"dev_auto_reload": True}))
    async with AsyncClient(
        transport=ASGITransport(app=dev_app), base_url="http://testserver"
    ) as dev_client:
        from app.main import DEV_PAUSE_MARKER

        marker = Path(DEV_PAUSE_MARKER)
        # The developer may be holding reloads right now (the repo is the
        # dev container's bind mount) — save and restore that state.
        was_paused = marker.exists()
        if was_paused:
            marker.unlink()

        first = await dev_client.get("/__dev/version")
        second = await dev_client.get("/__dev/version")
        assert first.status_code == 200
        assert first.text == second.text  # stable until files change
        index = await dev_client.get("/")
        assert "dev-reload.js" in index.text
        # Pages embed their render-time token, so the poller's baseline is
        # always correct — even for a page loaded while reloads are paused.
        assert f'data-dev-version="{first.text}"' in index.text

        # The pause marker holds browsers' reloads during development;
        # removing it lets the real token through again.
        marker.touch()
        try:
            assert (await dev_client.get("/__dev/version")).text == "paused"
            if not was_paused:
                marker.unlink()
                resumed = await dev_client.get("/__dev/version")
                assert resumed.text not in ("paused", "")
        finally:
            if was_paused:
                marker.touch()
            else:
                marker.unlink(missing_ok=True)


@respx.mock
async def test_roster_shows_paused_queue(client, db_session):
    """A queue holding skills that aren't training (an Omega-lapsed
    character: entries without finish dates) reads as Paused, not
    unknown; an empty queue still reads as an em-dash."""
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    respx.get(WALLET_URL).respond(json=10.0)
    mock_roster_metadata()
    queue = respx.get("https://esi.test/latest/characters/1234/skillqueue/")
    queue.respond(
        json=[{"skill_id": 17940, "queue_position": 0, "finished_level": 5}]
    )
    state = await _start_login(client)
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})

    response = await client.get("/characters")
    assert '<span class="meta-value">Paused</span>' in response.text

    queue.respond(json=[])
    response = await client.get("/characters")
    assert '<span class="meta-value">—</span>' in response.text
    assert "Paused" not in response.text
