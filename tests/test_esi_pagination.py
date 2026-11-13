"""ESIClient pagination and public-GET tests.

get_paginated walks X-Pages; the header is persisted in the ETag cache so
a fresh-window repeat iterates with zero HTTP calls. get_public serves
universe routes without a Bearer token, keyed under owner 0.
"""

from datetime import timedelta

import httpx
import pytest
import respx
from sqlalchemy import select

from app.db import utc_now
from app.esi.client import ESIClient, ESIError, ESIStatusError
from app.models import Character, EsiCache
from tests.conftest import TEST_SETTINGS

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
ASSETS_URL = "https://esi.test/latest/characters/1234/assets/"
TYPE_URL = "https://esi.test/latest/universe/types/1230/"
WALLET_URL = "https://esi.test/latest/characters/1234/wallet/"

PAST_EXPIRES = "Thu, 01 Jan 2026 00:00:00 GMT"
FUTURE_EXPIRES = "Wed, 31 Dec 2031 00:00:00 GMT"


def _make_client(app, db_session) -> ESIClient:
    return ESIClient(
        app.state.http,
        TEST_SETTINGS,
        db_session,
        clock=app.state.esi_clock,
        limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


async def _seed_character(db_session) -> Character:
    character = Character(
        character_id=1234,
        name="Test Pilot",
        owner_hash="owner-hash-1",
        scopes="publicData esi-wallet.read_character_wallet.v1 esi-assets.read_assets.v1",
        access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R1",
    )
    db_session.add(character)
    await db_session.commit()
    return character


@respx.mock
async def test_get_paginated_walks_all_pages(app, db_session):
    character = await _seed_character(db_session)
    esi = _make_client(app, db_session)
    route = respx.get(ASSETS_URL).mock(
        side_effect=[
            httpx.Response(
                200, json=[{"item_id": 1}], headers={"X-Pages": "3"}
            ),
            httpx.Response(200, json=[{"item_id": 2}]),
            httpx.Response(200, json=[{"item_id": 3}]),
        ]
    )

    items = await esi.get_paginated(character, "/characters/{character_id}/assets/")

    assert [item["item_id"] for item in items] == [1, 2, 3]
    assert route.call_count == 3
    pages = [str(call.request.url) for call in route.calls]
    assert "page=1" in pages[0] and "page=2" in pages[1] and "page=3" in pages[2]


@respx.mock
async def test_get_paginated_fresh_window_repeat_is_zero_http(app, db_session):
    """The page count must survive a fresh-window hit: X-Pages is persisted
    with the cache row, so the second full walk makes no requests."""
    character = await _seed_character(db_session)
    esi = _make_client(app, db_session)
    route = respx.get(ASSETS_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json=[{"item_id": 1}],
                headers={"X-Pages": "2", "Expires": FUTURE_EXPIRES},
            ),
            httpx.Response(
                200, json=[{"item_id": 2}], headers={"Expires": FUTURE_EXPIRES}
            ),
        ]
    )

    first = await esi.get_paginated(character, "/characters/{character_id}/assets/")
    second = await esi.get_paginated(character, "/characters/{character_id}/assets/")

    assert first == second
    assert route.call_count == 2  # entirely served from the fresh window

    rows = (await db_session.execute(select(EsiCache))).scalars().all()
    page_one = next(row for row in rows if '"page":1' in row.params_json)
    assert page_one.headers_json is not None
    assert "x-pages" in page_one.headers_json


@respx.mock
async def test_get_paginated_defaults_to_single_page(app, db_session):
    """A missing or garbage X-Pages means one page."""
    character = await _seed_character(db_session)
    esi = _make_client(app, db_session)
    route = respx.get(ASSETS_URL).respond(json=[{"item_id": 9}])

    items = await esi.get_paginated(character, "/characters/{character_id}/assets/")

    assert items == [{"item_id": 9}]
    assert route.call_count == 1


@respx.mock
async def test_get_public_sends_no_authorization(app, db_session):
    esi = _make_client(app, db_session)
    route = respx.get(TYPE_URL).respond(
        json={"name": "Veldspar", "volume": 0.1}, headers={"Expires": FUTURE_EXPIRES}
    )

    first = await esi.get_public("/universe/types/1230/")
    second = await esi.get_public("/universe/types/1230/")

    assert first["name"] == "Veldspar"
    assert second == first
    assert route.call_count == 1
    assert "Authorization" not in route.calls.last.request.headers
    assert route.calls.last.request.headers["User-Agent"] == TEST_SETTINGS.esi_user_agent

    # Cache rows key under the public owner.
    row = (await db_session.execute(select(EsiCache))).scalars().one()
    assert row.character_id == 0


@respx.mock
async def test_status_error_carries_code(app, db_session):
    character = await _seed_character(db_session)
    esi = _make_client(app, db_session)
    respx.get(WALLET_URL).respond(status_code=404, json="not found")

    with pytest.raises(ESIStatusError) as exc_info:
        await esi.get(character, "/characters/{character_id}/wallet/")

    assert exc_info.value.status_code == 404
    assert isinstance(exc_info.value, ESIError)
    assert "404" in str(exc_info.value)
