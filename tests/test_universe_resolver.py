"""UniverseResolver tests: resolution, persistence, restricted structures,
and the system → constellation → region hop.

All resolution is best-effort: failures degrade to placeholders instead of
raising, and 403-restricted structures are not retried within the
structure_retry_days window (every 403 burns ESI's error-limit budget).
"""

from datetime import timedelta

import httpx
import respx
from sqlalchemy import select, update

from app.db import utc_now
from app.esi.client import ESIClient
from app.esi.universe import UniverseResolver
from app.models import Character, UniverseLocation, UniverseRegion
from tests.conftest import TEST_SETTINGS

STATION_URL = "https://esi.test/latest/universe/stations/60003743/"
STRUCTURE_URL = "https://esi.test/latest/universe/structures/1000000000001/"
SYSTEM_URL = "https://esi.test/latest/universe/systems/30000142/"
CONSTELLATION_URL = "https://esi.test/latest/universe/constellations/20000020/"
REGION_URL = "https://esi.test/latest/universe/regions/10000016/"
TYPE_URL = "https://esi.test/latest/universe/types/1230/"


def _make_resolver(app, db_session) -> UniverseResolver:
    esi = ESIClient(
        app.state.http,
        TEST_SETTINGS,
        db_session,
        clock=app.state.esi_clock,
        limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )
    return UniverseResolver(db_session, esi, settings=TEST_SETTINGS)


async def _seed_character(
    db_session, character_id: int = 1234, name: str = "Test Pilot"
) -> Character:
    character = Character(
        character_id=character_id,
        name=name,
        owner_hash=f"owner-{character_id}",
        scopes="publicData esi-assets.read_assets.v1",
        access_token=f"tok-{character_id}",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token=f"R-{character_id}",
    )
    db_session.add(character)
    await db_session.commit()
    return character


@respx.mock
async def test_station_resolves_and_persists(app, db_session):
    resolver = _make_resolver(app, db_session)
    route = respx.get(STATION_URL).respond(
        json={"name": "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
              "system_id": 30000142}
    )

    infos = await resolver.resolve_locations([(60003743, "station")])

    assert infos[60003743].name == "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
    assert infos[60003743].system_id == 30000142
    assert not infos[60003743].restricted

    # Second resolve is served from the DB: zero HTTP.
    again = await resolver.resolve_locations([(60003743, "station")])
    assert again[60003743].name == infos[60003743].name
    assert route.call_count == 1


@respx.mock
async def test_structure_resolves_via_character_token(app, db_session):
    character = await _seed_character(db_session)
    resolver = _make_resolver(app, db_session)
    route = respx.get(STRUCTURE_URL).respond(
        json={"name": "Fort Knocks", "solar_system_id": 30000142}
    )

    infos = await resolver.resolve_locations(
        [(1000000000001, "structure")], characters=[character]
    )

    assert infos[1000000000001].name == "Fort Knocks"
    assert infos[1000000000001].system_id == 30000142
    assert route.calls.last.request.headers["Authorization"] == "Bearer tok-1234"


@respx.mock
async def test_structure_tries_next_character_on_403(app, db_session):
    first = await _seed_character(db_session, 1234, "Alpha Pilot")
    second = await _seed_character(db_session, 5678, "Bravo Pilot")
    resolver = _make_resolver(app, db_session)
    route = respx.get(STRUCTURE_URL).mock(
        side_effect=[
            httpx.Response(403, json="forbidden"),
            httpx.Response(200, json={"name": "Fort Knocks", "solar_system_id": 42}),
        ]
    )

    infos = await resolver.resolve_locations(
        [(1000000000001, "structure")], characters=[first, second]
    )

    assert infos[1000000000001].name == "Fort Knocks"
    assert route.call_count == 2
    assert route.calls.last.request.headers["Authorization"] == "Bearer tok-5678"


@respx.mock
async def test_structure_all_refused_is_restricted_without_retry(app, db_session):
    character = await _seed_character(db_session)
    resolver = _make_resolver(app, db_session)
    route = respx.get(STRUCTURE_URL).respond(status_code=403, json="forbidden")

    infos = await resolver.resolve_locations(
        [(1000000000001, "structure")], characters=[character]
    )
    again = await resolver.resolve_locations(
        [(1000000000001, "structure")], characters=[character]
    )

    assert infos[1000000000001].restricted
    assert infos[1000000000001].name == "Structure #1000000000001"
    assert infos[1000000000001].system_id is None
    assert again[1000000000001].restricted
    assert route.call_count == 1  # parked: no retry inside the window

    row = await db_session.get(UniverseLocation, 1000000000001)
    assert row is not None and row.restricted


@respx.mock
async def test_restricted_structure_retried_after_window(app, db_session):
    character = await _seed_character(db_session)
    resolver = _make_resolver(app, db_session)
    db_session.add(
        UniverseLocation(
            location_id=1000000000001,
            kind="structure",
            name="Structure #1000000000001",
            restricted=True,
        )
    )
    await db_session.commit()
    # Age the row past structure_retry_days (7 in TEST_SETTINGS default).
    await db_session.execute(
        update(UniverseLocation)
        .where(UniverseLocation.location_id == 1000000000001)
        .values(updated_at=utc_now() - timedelta(days=8))
    )
    await db_session.commit()

    route = respx.get(STRUCTURE_URL).respond(
        json={"name": "Fort Knocks", "solar_system_id": 30000142}
    )

    infos = await resolver.resolve_locations(
        [(1000000000001, "structure")], characters=[character]
    )

    assert route.call_count == 1
    assert infos[1000000000001].name == "Fort Knocks"
    assert not infos[1000000000001].restricted

    rows = (
        (
            await db_session.execute(
                select(UniverseLocation).where(
                    UniverseLocation.location_id == 1000000000001
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1  # updated in place, not duplicated


@respx.mock
async def test_types_resolve_and_skip_stored(app, db_session):
    resolver = _make_resolver(app, db_session)
    route = respx.get(TYPE_URL).respond(
        json={"name": "Veldspar", "volume": 0.1, "packaged_volume": 0.1, "group_id": 18}
    )

    await resolver.ensure_types([1230, 1230])
    await resolver.ensure_types([1230])

    assert route.call_count == 1
    stored = await resolver.get_type(1230)
    assert stored is not None
    assert stored.name == "Veldspar"
    assert stored.volume == 0.1


@respx.mock
async def test_ensure_systems_resolves_region_hop(app, db_session):
    resolver = _make_resolver(app, db_session)
    respx.get(SYSTEM_URL).respond(
        json={"name": "Jita", "constellation_id": 20000020}
    )
    respx.get(CONSTELLATION_URL).respond(json={"region_id": 10000016})
    respx.get(REGION_URL).respond(json={"name": "The Forge"})

    result = await resolver.ensure_systems([30000142])

    assert result[30000142].name == "Jita"
    assert result[30000142].region_id == 10000016
    assert result[30000142].region_name == "The Forge"

    # Repeat: everything cached, zero HTTP.
    with respx.mock:
        again = await resolver.ensure_systems([30000142])
    assert again[30000142].region_name == "The Forge"
    assert await db_session.get(UniverseRegion, 10000016) is not None


@respx.mock
async def test_resolution_failures_degrade_instead_of_raising(app, db_session):
    resolver = _make_resolver(app, db_session)
    respx.get(STATION_URL).respond(status_code=404, json="no such station")
    respx.get(TYPE_URL).respond(status_code=404, json="no such type")
    respx.get("https://esi.test/latest/universe/systems/987654/").respond(
        status_code=404, json="no such system"
    )

    infos = await resolver.resolve_locations([(60003743, "station")])
    await resolver.ensure_types([1230])
    systems = await resolver.ensure_systems([987654])

    assert infos[60003743].name is None
    assert await resolver.get_type(1230) is None
    assert systems[987654].name is None
    assert systems[987654].region_id is None
