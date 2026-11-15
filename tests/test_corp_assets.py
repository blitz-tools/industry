"""Corporation asset sync and page tests: the role-gated corp sync
(snapshot pull, gate failure recording, office rows), the corporation
asset browser (DB-pure renders apart from the render-time role gate),
and the per-structure fragments without the owner column.

Gate failures must never touch the corp endpoints — the ESI calls the
gate exists to protect are asserted uncalled (respx routes registered
with call_count 0).
"""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import respx
from sqlalchemy import select

from app.assets import corporation_offices, system_groups
from app.db import utc_now
from app.esi.assets import OWNER_CORPORATION, sync_corporation, sync_tick
from app.esi.client import ESIClient
from app.esi.universe import UniverseResolver
from app.models import (
    Asset,
    AssetSync,
    Character,
    UniverseCategory,
    UniverseGroup,
    UniverseLocation,
    UniverseRegion,
    UniverseType,
)
from tests.conftest import TEST_SETTINGS, make_access_token, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
ROLES_URL = "https://esi.test/latest/characters/1234/roles/"
CORP_ASSETS_URL = "https://esi.test/latest/corporations/98000001/assets/"

STATION_URL = "https://esi.test/latest/universe/stations/6001/"
STATION2_URL = "https://esi.test/latest/universe/stations/6002/"
SYSTEM_URL = "https://esi.test/latest/universe/systems/3001/"
CONSTELLATION_URL = "https://esi.test/latest/universe/constellations/2001/"
REGION_URL = "https://esi.test/latest/universe/regions/1001/"
TYPE_MINERAL_URL = "https://esi.test/latest/universe/types/1230/"
TYPE_OTHER_URL = "https://esi.test/latest/universe/types/1231/"
OFFICE_TYPE_URL = "https://esi.test/latest/universe/types/27/"
GROUP_MINERAL_URL = "https://esi.test/latest/universe/groups/18/"
CATEGORY_MATERIAL_URL = "https://esi.test/latest/universe/categories/4/"

ALPHA = 1234
CORP_ID = 98000001
STATION = 6001
STATION2 = 6002
SYSTEM = 3001
REGION = 1001
TYPE_MINERAL = 1230
TYPE_OTHER = 1231
TYPE_OFFICE = 27
# Office contents hang off container ids ESI never describes as rows —
# the live Upwell-office shape.
OFFICE_CONTAINER = 990001
EMPTY_OFFICE_CONTAINER = 990002

STATION_NAME = "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
STATION2_NAME = "Amarr VIII (Oris) - Emperor Family Academy"

# A main whose grant covers everything the corp sync needs.
FULL_GRANT = (
    "publicData esi-characters.read_corporation_roles.v1 "
    "esi-assets.read_corporation_assets.v1"
)


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


async def _seed_main(
    db_session,
    *,
    scopes: str = FULL_GRANT,
    corporation_id: int | None = CORP_ID,
    fresh_token: bool = True,
) -> Character:
    main = Character(
        character_id=ALPHA,
        name="Main Pilot",
        owner_hash="owner-main",
        scopes=scopes,
        access_token="tok-main",
        access_token_expires_at=utc_now()
        + (timedelta(minutes=30) if fresh_token else -timedelta(minutes=5)),
        refresh_token="R-main",
        is_main=True,
        corporation_id=corporation_id,
    )
    db_session.add(main)
    await db_session.commit()
    return main


def _mock_roles(roles: list[str]):
    return respx.get(ROLES_URL).respond(json={"roles": roles})


def _mock_corp_assets(pages: list[list[dict]]):
    return respx.get(CORP_ASSETS_URL).mock(
        side_effect=[
            httpx.Response(
                200, json=page, headers={"X-Pages": str(len(pages))}
            )
            for page in pages
        ]
    )


def _mock_universe() -> None:
    respx.get(STATION_URL).respond(
        json={"name": STATION_NAME, "system_id": SYSTEM}
    )
    respx.get(STATION2_URL).respond(
        json={"name": STATION2_NAME, "system_id": SYSTEM}
    )
    respx.get(SYSTEM_URL).respond(
        json={"name": "Jita", "constellation_id": 2001}
    )
    respx.get(CONSTELLATION_URL).respond(json={"region_id": REGION})
    respx.get(REGION_URL).respond(json={"name": "The Forge"})
    respx.get(TYPE_MINERAL_URL).respond(
        json={"name": "Veldspar", "volume": 0.1, "group_id": 18}
    )
    respx.get(TYPE_OTHER_URL).respond(
        json={"name": "Office", "volume": None, "group_id": 18}
    )
    respx.get(OFFICE_TYPE_URL).respond(
        json={"name": "Office", "volume": None, "group_id": 18}
    )
    respx.get(GROUP_MINERAL_URL).respond(json={"name": "Mineral", "category_id": 4})
    respx.get(CATEGORY_MATERIAL_URL).respond(json={"name": "Material"})


def _corp_asset(
    item_id: int,
    type_id: int,
    quantity: int,
    flag: str,
    station: int = STATION,
    location_type: str = "station",
) -> dict:
    return {
        "item_id": item_id,
        "type_id": type_id,
        "quantity": quantity,
        "location_id": station,
        "location_type": location_type,
        "location_flag": flag,
        "is_singleton": False,
    }


async def _login(client, scopes: list[str] | None = None):
    """Create ALPHA through the SSO flow; `scopes` overrides the grant
    (the corporation gate needs the roles + corp-assets scopes)."""
    access_token = (
        make_access_token(scopes=scopes) if scopes is not None else None
    )
    respx.post(SSO_TOKEN_URL).respond(
        json=token_response(name="Alpha Pilot", access_token=access_token)
    )
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


# --- Corporation sync ----------------------------------------------------------


@respx.mock
async def test_sync_corporation_assets(app, db_session):
    await _seed_main(db_session)
    _mock_roles(["Director"])
    corp_route = _mock_corp_assets(
        [
            [
                # The live office shape: contents and the marker share an
                # item-typed container id that is never an asset row.
                _corp_asset(
                    1, TYPE_MINERAL, 5000, "CorpSAG2",
                    station=OFFICE_CONTAINER, location_type="item",
                ),
                _corp_asset(
                    2, TYPE_OFFICE, 1, "OfficeFolder",
                    station=OFFICE_CONTAINER, location_type="item",
                ),
            ],
            [_corp_asset(3, TYPE_MINERAL, 200, "CorpSAG1", station=STATION2)],
        ]
    )
    _mock_universe()

    esi = _make_esi(app, db_session)
    outcomes = await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )

    # The grant holds the roles + corp-assets scopes only, so the
    # blueprints and jobs kinds trip their own scope gates (their
    # endpoints are unmocked — calling one would fail the test).
    assert [outcome.status for outcome in outcomes] == [
        "synced", "no-scope", "no-scope",
    ]
    assert outcomes[0].item_count == 3
    assert corp_route.call_count == 2  # both pages walked
    rows = {
        row.item_id: row
        for row in (
            await db_session.execute(
                select(Asset).where(Asset.owner_type == OWNER_CORPORATION)
            )
        ).scalars()
    }
    assert set(rows) == {1, 2, 3}
    assert all(row.owner_id == CORP_ID for row in rows.values())
    assert rows[2].location_flag == "OfficeFolder"
    sync = await db_session.get(AssetSync, (OWNER_CORPORATION, CORP_ID))
    assert sync.status == "ok"
    # Column tuples: rows were seeded/updated through another session.
    flags = dict(
        (
            await db_session.execute(
                select(Asset.item_id, Asset.parent_location_id)
            )
        ).all()
    )
    assert flags == {
        1: OFFICE_CONTAINER,
        2: OFFICE_CONTAINER,
        3: STATION2,
    }
    # No character holds the structures scope: the office container parks
    # as a restricted structure (no ESI attempt, no 401 burn every pass).
    parked = await db_session.get(UniverseLocation, OFFICE_CONTAINER)
    assert parked is not None
    assert parked.restricted
    assert parked.name == f"Structure #{OFFICE_CONTAINER}"


@respx.mock
async def test_sync_corporation_no_main(app, db_session):
    esi = _make_esi(app, db_session)
    outcomes = await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )
    assert outcomes is None


@respx.mock
async def test_sync_corporation_gate_no_roles_scope(app, db_session):
    # Roles scope absent (the gate's own scope): gate must trip first.
    await _seed_main(
        db_session, scopes="publicData esi-assets.read_corporation_assets.v1"
    )
    corp_route = respx.get(CORP_ASSETS_URL).respond(json=[])

    esi = _make_esi(app, db_session)
    outcomes = await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )

    assert [outcome.status for outcome in outcomes] == ["no-scope"]
    assert corp_route.call_count == 0
    sync = await db_session.get(AssetSync, (OWNER_CORPORATION, CORP_ID))
    assert sync.status == "no-scope"


@respx.mock
async def test_sync_corporation_gate_insufficient_roles(app, db_session):
    await _seed_main(db_session)
    _mock_roles(["Personnel_Manager"])
    corp_route = respx.get(CORP_ASSETS_URL).respond(json=[])

    esi = _make_esi(app, db_session)
    outcomes = await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )

    assert [outcome.status for outcome in outcomes] == ["no-roles"]
    assert corp_route.call_count == 0
    sync = await db_session.get(AssetSync, (OWNER_CORPORATION, CORP_ID))
    assert sync.status == "no-roles"
    assert "Director" in sync.detail


@respx.mock
async def test_sync_corporation_missing_assets_scope(app, db_session):
    await _seed_main(
        db_session, scopes="publicData esi-characters.read_corporation_roles.v1"
    )
    _mock_roles(["Director"])
    corp_route = respx.get(CORP_ASSETS_URL).respond(json=[])

    esi = _make_esi(app, db_session)
    outcomes = await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )

    assert [outcome.status for outcome in outcomes] == [
        "no-scope", "no-scope", "no-scope",
    ]
    assert "read_corporation_assets" in outcomes[0].detail
    assert corp_route.call_count == 0


@respx.mock
async def test_sync_corporation_reauth(app, db_session):
    await _seed_main(db_session, fresh_token=False)
    _mock_roles(["Director"])
    respx.post(SSO_TOKEN_URL).respond(json={"error": "invalid_grant"}, status_code=400)

    esi = _make_esi(app, db_session)
    outcomes = await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )

    assert [outcome.status for outcome in outcomes] == ["reauth"]
    sync = await db_session.get(AssetSync, (OWNER_CORPORATION, CORP_ID))
    assert sync.status == "reauth"


@respx.mock
async def test_sync_resolves_office_structure(app, db_session):
    """Office containers resolve as structures when a character holds the
    structures scope — the office panel gets a real name and system."""
    await _seed_main(
        db_session, scopes=f"{FULL_GRANT} esi-universe.read_structures.v1"
    )
    _mock_roles(["Director"])
    _mock_corp_assets(
        [
            [
                _corp_asset(
                    1, TYPE_MINERAL, 10, "CorpSAG1",
                    station=OFFICE_CONTAINER, location_type="item",
                ),
                _corp_asset(
                    2, TYPE_OFFICE, 1, "OfficeFolder",
                    station=OFFICE_CONTAINER, location_type="item",
                ),
            ]
        ]
    )
    _mock_universe()
    respx.get(
        f"https://esi.test/latest/universe/structures/{OFFICE_CONTAINER}/"
    ).respond(json={"name": "Blitz Fort", "solar_system_id": SYSTEM})

    esi = _make_esi(app, db_session)
    await sync_corporation(
        db_session, esi, resolver=_make_resolver(db_session, esi)
    )

    location = await db_session.get(UniverseLocation, OFFICE_CONTAINER)
    assert location is not None
    assert location.name == "Blitz Fort"
    assert location.system_id == SYSTEM
    assert not location.restricted

    view = await system_groups(
        db_session, owner_ids=[CORP_ID], owner_type=OWNER_CORPORATION
    )
    panels = [
        (group.name, structure.name, structure.is_office)
        for group in view.groups
        for structure in group.structures
    ]
    assert ("Jita", "Blitz Fort", True) in panels


@respx.mock
async def test_sync_tick_includes_corporation(app, db_session):
    """The background tick syncs the main's corporation alongside the
    characters (the main's own character sync records no-scope without
    touching ESI — it holds no character-assets scope)."""
    await _seed_main(db_session)
    _mock_roles(["Director"])
    _mock_corp_assets([[_corp_asset(1, TYPE_MINERAL, 10, "CorpSAG1")]])
    _mock_universe()

    await sync_tick(app.state.session_factory, app.state.http, TEST_SETTINGS)

    rows = list(
        (
            await db_session.execute(
                select(Asset).where(Asset.owner_type == OWNER_CORPORATION)
            )
        ).scalars()
    )
    assert [row.item_id for row in rows] == [1]


# --- Corporation assets page ---------------------------------------------------


def _corp_row(item_id, type_id, quantity, parent, flag, *, singleton=False) -> Asset:
    return Asset(
        owner_type=OWNER_CORPORATION, owner_id=CORP_ID, item_id=item_id,
        type_id=type_id, quantity=quantity, location_id=parent,
        location_flag=flag, location_type="item",
        parent_location_id=parent, is_blueprint_copy=False,
        is_singleton=singleton,
    )


async def _seed_corp_world(db_session) -> None:
    """A synced-looking corporation snapshot in the live office shape:
    an office container (contents + the type-27 Office marker under one
    unresolvable parent id), a marker-only office, and plain station
    hangars — plus the universe rows that label the resolvable parts."""
    db_session.add_all(
        [
            UniverseLocation(
                location_id=STATION, kind="station", name=STATION_NAME, system_id=SYSTEM
            ),
            UniverseLocation(
                location_id=STATION2, kind="station", name=STATION2_NAME, system_id=SYSTEM
            ),
            UniverseLocation(
                location_id=SYSTEM, kind="solar_system", name="Jita", region_id=REGION
            ),
            UniverseRegion(region_id=REGION, name="The Forge"),
            UniverseType(type_id=TYPE_MINERAL, name="Veldspar", volume=0.1, group_id=18),
            UniverseGroup(group_id=18, name="Mineral", category_id=4),
            UniverseCategory(category_id=4, name="Material"),
            # Office with contents: marker + hangar rows share the parent.
            _corp_row(1, TYPE_MINERAL, 5000, OFFICE_CONTAINER, "CorpSAG2"),
            _corp_row(2, TYPE_MINERAL, 200, OFFICE_CONTAINER, "CorpSAG5"),
            _corp_row(3, TYPE_OFFICE, 1, OFFICE_CONTAINER, "OfficeFolder",
                      singleton=True),
            # Office holding nothing but its marker.
            _corp_row(4, TYPE_OFFICE, 1, EMPTY_OFFICE_CONTAINER, "OfficeFolder",
                      singleton=True),
            # Plain station hangars, no office involved.
            _corp_row(5, TYPE_MINERAL, 100, STATION, "CorpSAG1"),
            _corp_row(6, TYPE_MINERAL, 50, STATION2, "CorpSAG3"),
        ]
    )
    await db_session.commit()


async def _login_with_main(client, db_session):
    await _login(client, scopes=FULL_GRANT.split())
    await client.post(f"/characters/{ALPHA}/main")
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()


@respx.mock
async def test_corp_assets_page_renders(client, db_session):
    await _login_with_main(client, db_session)
    await _seed_corp_world(db_session)
    corp_route = respx.get(CORP_ASSETS_URL).respond(json=[])
    roles_route = respx.get(ROLES_URL).respond(json={"roles": ["Director"]})

    response = await client.get("/corp/assets")

    assert response.status_code == 200
    assert "Corporation Assets" in response.text
    assert STATION_NAME in response.text
    assert STATION2_NAME in response.text
    # The office box is static (header + note): the offices themselves
    # live in the structure list, as panels — the marker-only office
    # included.
    assert "Offices" in response.text
    assert "Rented offices" in response.text
    assert f"Office #{OFFICE_CONTAINER}" not in response.text
    assert f'data-location-id="{OFFICE_CONTAINER}"' in response.text
    assert f'data-location-id="{EMPTY_OFFICE_CONTAINER}"' in response.text
    # DB-pure render apart from the role gate: no corp endpoint touched.
    assert corp_route.call_count == 0
    assert roles_route.call_count == 1


@respx.mock
async def test_corp_offices_empty_when_no_offices(client, db_session):
    """Regression: with no office rows at all the counts aggregate must
    not emit a phantom (None, 0) office."""
    await _login_with_main(client, db_session)
    db_session.add_all(
        [
            UniverseLocation(
                location_id=STATION, kind="station", name=STATION_NAME, system_id=SYSTEM
            ),
            _corp_row(5, TYPE_MINERAL, 100, STATION, "CorpSAG1"),
        ]
    )
    await db_session.commit()

    offices = await corporation_offices(db_session, CORP_ID)
    assert offices == []


@respx.mock
async def test_corp_assets_page_office_counts(client, db_session):
    await _login_with_main(client, db_session)
    await _seed_corp_world(db_session)

    offices = await corporation_offices(db_session, CORP_ID)
    # Both offices listed with separate counts (regression: a missing
    # GROUP BY collapsed them); the marker item is not counted.
    assert [(office.name, office.item_count) for office in offices] == [
        (f"Office #{OFFICE_CONTAINER}", 2),
        (f"Office #{EMPTY_OFFICE_CONTAINER}", 0),
    ]


@respx.mock
async def test_corp_assets_page_gated(client, db_session):
    await _login(client)

    # No main: redirected to the overview.
    response = await client.get("/corp/assets", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/corp"

    # A main without the Director/CEO role: same redirect, gate reason
    # explained on the overview.
    await client.post(f"/characters/{ALPHA}/main")
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()
    respx.get(ROLES_URL).respond(json={"roles": []})
    response = await client.get("/corp/assets", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/corp"


@respx.mock
async def test_corp_structure_fragment(client, db_session):
    await _login_with_main(client, db_session)
    await _seed_corp_world(db_session)

    response = await client.get(f"/corp/assets/structure/{OFFICE_CONTAINER}")

    assert response.status_code == 200
    # Office contents nest under a collapsed "Office" expander.
    assert '<details class="office-folder">' in response.text
    assert "Veldspar" in response.text
    # The type-27 Office marker row is hidden — the office is implied by
    # the expander itself.
    assert "Unknown type #27" not in response.text
    # One owner (the corporation): no owner column in corp panels.
    assert "owner-cell" not in response.text
    # Fragment links stay on the corp route.
    assert f"/corp/assets/structure/{OFFICE_CONTAINER}?" in response.text

    # Browsing (a sort or a later page) re-renders the expander open.
    response = await client.get(
        f"/corp/assets/structure/{OFFICE_CONTAINER}?sort=type"
    )
    assert '<details class="office-folder" open>' in response.text

    # Non-office locations have no nested expander.
    response = await client.get(f"/corp/assets/structure/{STATION}")
    assert "office-folder" not in response.text


@respx.mock
async def test_corp_assets_sync_button(client, db_session):
    await _login_with_main(client, db_session)
    _mock_roles(["Director"])
    _mock_corp_assets([[_corp_asset(1, TYPE_MINERAL, 10, "CorpSAG1")]])
    _mock_universe()

    response = await client.post(
        "/corp/assets/sync",
        data={"region": "", "category": "materials"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/corp/assets?category=materials"
    rows = list(
        (
            await db_session.execute(
                select(Asset).where(Asset.owner_type == OWNER_CORPORATION)
            )
        ).scalars()
    )
    assert [row.item_id for row in rows] == [1]
