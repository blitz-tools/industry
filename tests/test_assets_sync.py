"""Asset sync tests: multi-page snapshot pull, container-chain parent
resolution, universe resolution inside the sync, outcome recording
(reauth / no-scope / error), replace semantics, and the never-raising
background tick."""

from datetime import timedelta

import httpx
import respx
from sqlalchemy import select

from app.db import utc_now
from app.esi.assets import sync_all_characters, sync_tick
from app.esi.client import ESIClient
from app.esi.universe import UniverseResolver
from app.models import (
    Asset,
    AssetSync,
    Character,
    UniverseLocation,
    UniverseRegion,
    UniverseType,
)
from tests.conftest import TEST_SETTINGS

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
STATION_URL = "https://esi.test/latest/universe/stations/60003743/"
SYSTEM_URL = "https://esi.test/latest/universe/systems/30000142/"
CONSTELLATION_URL = "https://esi.test/latest/universe/constellations/20000020/"
REGION_URL = "https://esi.test/latest/universe/regions/10000016/"
TYPE_1230_URL = "https://esi.test/latest/universe/types/1230/"
TYPE_1231_URL = "https://esi.test/latest/universe/types/1231/"

PAST_EXPIRES = "Thu, 01 Jan 2026 00:00:00 GMT"
FUTURE_EXPIRES = "Wed, 31 Dec 2031 00:00:00 GMT"

WITH_ASSETS = "publicData esi-wallet.read_character_wallet.v1 esi-assets.read_assets.v1"

STATION_ID = 60003743
CONTAINER_ITEM_ID = 3


def _make_esi(app, db_session) -> ESIClient:
    return ESIClient(
        app.state.http,
        TEST_SETTINGS,
        db_session,
        clock=app.state.esi_clock,
        limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


def _make_resolver(db_session, esi) -> UniverseResolver:
    return UniverseResolver(db_session, esi, settings=TEST_SETTINGS)


async def _seed_character(
    db_session,
    character_id: int = 1234,
    name: str = "Test Pilot",
    scopes: str = WITH_ASSETS,
    fresh_token: bool = True,
) -> Character:
    character = Character(
        character_id=character_id,
        name=name,
        owner_hash=f"owner-{character_id}",
        scopes=scopes,
        access_token=f"tok-{character_id}",
        access_token_expires_at=utc_now()
        + (timedelta(minutes=30) if fresh_token else -timedelta(minutes=5)),
        refresh_token=f"R-{character_id}",
    )
    db_session.add(character)
    await db_session.commit()
    return character


def _assets_url(character_id: int) -> str:
    return f"https://esi.test/latest/characters/{character_id}/assets/"


def _mock_assets(character_id: int, pages: list[list[dict]], **extra_headers):
    return respx.get(_assets_url(character_id)).mock(
        side_effect=[
            httpx.Response(
                200,
                json=page,
                headers={"X-Pages": str(len(pages)), **extra_headers},
            )
            for page in pages
        ]
    )


def _mock_universe() -> None:
    respx.get(STATION_URL).respond(
        json={"name": "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
              "system_id": 30000142}
    )
    respx.get(SYSTEM_URL).respond(json={"name": "Jita", "constellation_id": 20000020})
    respx.get(CONSTELLATION_URL).respond(json={"region_id": 10000016})
    respx.get(REGION_URL).respond(json={"name": "The Forge"})
    respx.get(TYPE_1230_URL).respond(
        json={"name": "Veldspar", "volume": 0.1, "group_id": 18}
    )
    respx.get(TYPE_1231_URL).respond(
        json={"name": "Iteron Mark V", "volume": 24500.0, "group_id": 26}
    )


def _hangar_item(item_id: int, type_id: int, quantity: int = 1) -> dict:
    return {
        "item_id": item_id,
        "type_id": type_id,
        "quantity": quantity,
        "location_id": STATION_ID,
        "location_flag": "Hangar",
        "location_type": "station",
        "is_singleton": False,
    }


@respx.mock
async def test_sync_pulls_pages_resolves_parents_and_universe(app, db_session):
    character = await _seed_character(db_session)
    esi = _make_esi(app, db_session)
    resolver = _make_resolver(db_session, esi)
    _mock_assets(
        character.character_id,
        [
            [_hangar_item(1, 1230, 500), _hangar_item(2, 1231)],
            # A container ship in the station, and an item inside it.
            [
                _hangar_item(CONTAINER_ITEM_ID, 1231),
                {
                    **_hangar_item(4, 1230, 50),
                    "location_id": CONTAINER_ITEM_ID,
                    "location_type": "item",
                    "location_flag": "Cargo",
                },
            ],
        ],
    )
    _mock_universe()

    outcomes = await sync_all_characters(db_session, esi, [character], resolver=resolver)

    assert outcomes[0].status == "synced"
    assert outcomes[0].item_count == 4

    rows = {
        row.item_id: row
        for row in (await db_session.execute(select(Asset))).scalars()
    }
    assert set(rows) == {1, 2, CONTAINER_ITEM_ID, 4}
    # Everything rolls up to the station, including the container's contents.
    assert all(row.parent_location_id == STATION_ID for row in rows.values())
    assert rows[4].location_id == CONTAINER_ITEM_ID  # raw location preserved

    # Universe resolution ran inside the sync.
    assert (await db_session.get(UniverseType, 1230)).name == "Veldspar"
    station = await db_session.get(UniverseLocation, STATION_ID)
    assert station.system_id == 30000142
    assert (await db_session.get(UniverseRegion, 10000016)).name == "The Forge"

    sync_row = await db_session.get(AssetSync, ("character", character.character_id))
    assert sync_row.status == "ok"


@respx.mock
async def test_resync_replaces_snapshot(app, db_session):
    character = await _seed_character(db_session)
    esi = _make_esi(app, db_session)
    resolver = _make_resolver(db_session, esi)
    _mock_universe()
    # First sync: one page holding item 1. Second sync (cache expired): the
    # snapshot has changed — item 1 is gone, item 2 arrived.
    route = respx.get(_assets_url(character.character_id)).mock(
        side_effect=[
            httpx.Response(
                200, json=[_hangar_item(1, 1230, 500)], headers={"X-Pages": "1"}
            ),
            httpx.Response(
                200, json=[_hangar_item(2, 1231)], headers={"X-Pages": "1"}
            ),
        ]
    )

    await sync_all_characters(db_session, esi, [character], resolver=resolver)
    await sync_all_characters(db_session, esi, [character], resolver=resolver)

    assert route.call_count == 2
    rows = {
        row.item_id for row in (await db_session.execute(select(Asset))).scalars()
    }
    assert rows == {2}


@respx.mock
async def test_fresh_window_resync_is_zero_http(app, db_session):
    """ESI's Expires window is compliance, not optimization: a repeat sync
    within it makes no requests at all (X-Pages survives via the cache)."""
    character = await _seed_character(db_session)
    esi = _make_esi(app, db_session)
    resolver = _make_resolver(db_session, esi)
    _mock_universe()
    route = _mock_assets(
        character.character_id,
        [[_hangar_item(1, 1230, 500)], [_hangar_item(2, 1231)]],
        Expires=FUTURE_EXPIRES,
    )

    await sync_all_characters(db_session, esi, [character], resolver=resolver)
    await sync_all_characters(db_session, esi, [character], resolver=resolver)

    assert route.call_count == 2  # exactly the first pass's two pages


@respx.mock
async def test_reauth_recorded_snapshot_and_siblings_retained(app, db_session):
    expired = await _seed_character(db_session, 1234, "Alpha Pilot", fresh_token=False)
    healthy = await _seed_character(db_session, 5678, "Bravo Pilot")
    esi = _make_esi(app, db_session)
    resolver = _make_resolver(db_session, esi)
    respx.post(SSO_TOKEN_URL).respond(
        status_code=400, json={"error": "invalid_grant"}
    )
    _mock_universe()
    bravo_route = _mock_assets(healthy.character_id, [[_hangar_item(9, 1230, 10)]])

    outcomes = await sync_all_characters(
        db_session, esi, [expired, healthy], resolver=resolver
    )

    by_id = {outcome.owner_id: outcome for outcome in outcomes}
    assert by_id[1234].status == "reauth"
    assert by_id[5678].status == "synced"
    assert bravo_route.call_count == 1

    owner_ids = {
        row.owner_id for row in (await db_session.execute(select(Asset))).scalars()
    }
    assert owner_ids == {5678}

    alpha_sync = await db_session.get(AssetSync, ("character", 1234))
    assert alpha_sync.status == "reauth"


@respx.mock
async def test_no_scope_character_is_skipped(app, db_session):
    character = await _seed_character(db_session, scopes="publicData")
    esi = _make_esi(app, db_session)
    resolver = _make_resolver(db_session, esi)
    route = _mock_assets(character.character_id, [[_hangar_item(1, 1230)]])

    outcomes = await sync_all_characters(db_session, esi, [character], resolver=resolver)

    assert outcomes[0].status == "no-scope"
    assert route.call_count == 0  # a scopeless call is a guaranteed 403
    sync_row = await db_session.get(AssetSync, ("character", 1234))
    assert sync_row.status == "no-scope"
    assert (await db_session.execute(select(Asset))).scalars().first() is None


@respx.mock
async def test_container_cycle_terminates(app, db_session):
    character = await _seed_character(db_session)
    esi = _make_esi(app, db_session)
    resolver = _make_resolver(db_session, esi)
    _mock_universe()
    # Two containers referencing each other; the walk must not hang.
    _mock_assets(
        character.character_id,
        [
            [
                {
                    **_hangar_item(10, 1231),
                    "location_id": 11,
                    "location_type": "item",
                },
                {
                    **_hangar_item(11, 1231),
                    "location_id": 10,
                    "location_type": "item",
                },
            ]
        ],
    )

    outcomes = await sync_all_characters(db_session, esi, [character], resolver=resolver)

    assert outcomes[0].status == "synced"
    rows = list((await db_session.execute(select(Asset))).scalars())
    assert len(rows) == 2
    assert {row.parent_location_id for row in rows} == {10, 11}


@respx.mock
async def test_sync_tick_survives_esi_failure(app, db_session):
    """The background loop must never die: a hard ESI error is recorded,
    not raised."""
    character = await _seed_character(db_session)
    respx.get(_assets_url(character.character_id)).respond(
        status_code=500, json="esi broke"
    )

    await sync_tick(app.state.session_factory, app.state.http, TEST_SETTINGS)

    sync_row = await db_session.get(AssetSync, ("character", 1234))
    assert sync_row is not None
    assert sync_row.status == "error"
    assert "500" in sync_row.detail
