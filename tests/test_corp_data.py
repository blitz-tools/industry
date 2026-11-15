"""Corporation blueprints and industry jobs: sync (per-kind scope gates,
snapshot rows, date parsing, gate-failure recording across all kinds)
and the pages that read them (DB-pure renders apart from the role gate,
active-vs-history jobs filter, installer resolution through tracked
characters)."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import respx
from sqlalchemy import select

from app.db import utc_now
from app.models import (
    Asset,
    Blueprint,
    Character,
    DataSync,
    IndustryJob,
    UniverseLocation,
    UniverseType,
)
from tests.conftest import make_access_token, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
ROLES_URL = "https://esi.test/latest/characters/1234/roles/"
CORP_BLUEPRINTS_URL = "https://esi.test/latest/corporations/98000001/blueprints/"
CORP_JOBS_URL = "https://esi.test/latest/corporations/98000001/industry/jobs/"

ALPHA = 1234
CORP_ID = 98000001
STATION = 6001
TYPE_BPO = 999  # "Typhoon Blueprint"
TYPE_BPC = 998
# An office item id — blueprints "inside" an office point at it.
OFFICE_ITEM = 1055568775746

FULL_GRANT = (
    "publicData esi-characters.read_corporation_roles.v1 "
    "esi-corporations.read_blueprints.v1 "
    "esi-industry.read_corporation_jobs.v1"
)

STATION_NAME = "Jita IV - Moon 4 - Caldari Navy Assembly Plant"


async def _login(client, scopes: list[str] | None = None):
    access_token = (
        make_access_token(scopes=scopes, name="Alpha Pilot")
        if scopes is not None
        else None
    )
    respx.post(SSO_TOKEN_URL).respond(
        json=token_response(name="Alpha Pilot", access_token=access_token)
    )
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _login_with_main(client, db_session, scopes=None):
    await _login(client, scopes=FULL_GRANT.split() if scopes is None else scopes)
    await client.post(f"/characters/{ALPHA}/main")
    alpha = await db_session.get(Character, ALPHA)
    alpha.corporation_id = CORP_ID
    await db_session.commit()


def _mock_roles(roles: list[str]):
    return respx.get(ROLES_URL).respond(json={"roles": roles})


def _blueprint_payload() -> list[dict]:
    return [
        {
            "item_id": 100,
            "type_id": TYPE_BPO,
            "location_id": STATION,
            "location_flag": "CorpSAG1",
            "quantity": 1,
            "runs": -1,
            "material_efficiency": 10,
            "time_efficiency": 14,
        },
        {
            "item_id": 101,
            "type_id": TYPE_BPC,
            "location_id": STATION,
            "location_flag": "CorpSAG2",
            "quantity": 1,
            "runs": 5,
            "material_efficiency": 0,
            "time_efficiency": 0,
        },
    ]


def _jobs_payload() -> list[dict]:
    return [
        {
            "job_id": 1,
            "installer_id": ALPHA,
            "activity_id": 1,
            "blueprint_type_id": TYPE_BPO,
            "runs": 10,
            "successful_runs": None,
            "status": "active",
            "start_date": "2026-11-15T10:00:00Z",
            "end_date": "2026-11-16T10:00:00Z",
            "completed_date": None,
            "station_id": STATION,
        },
        {
            "job_id": 2,
            "installer_id": ALPHA,
            "activity_id": 9,
            "blueprint_type_id": TYPE_BPC,
            "runs": 4,
            "successful_runs": 4,
            "status": "delivered",
            "start_date": "2026-11-14T10:00:00Z",
            "end_date": "2026-11-14T22:00:00Z",
            "completed_date": "2026-11-14T22:00:05Z",
            "station_id": STATION,
        },
    ]


def _mock_corp_endpoints():
    respx.get(CORP_BLUEPRINTS_URL).respond(
        json=_blueprint_payload(), headers={"X-Pages": "1"}
    )
    respx.get(CORP_JOBS_URL).respond(
        json=_jobs_payload(), headers={"X-Pages": "1"}
    )


# --- Sync ----------------------------------------------------------------------


@respx.mock
async def test_sync_corp_blueprints_and_jobs(app, db_session):
    from app.esi.assets import sync_corporation
    from app.esi.client import ESIClient
    from app.esi.universe import UniverseResolver
    from tests.conftest import TEST_SETTINGS

    main = Character(
        character_id=ALPHA, name="Alpha Pilot", owner_hash="owner-alpha",
        scopes=FULL_GRANT, access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R", is_main=True, corporation_id=CORP_ID,
    )
    db_session.add(main)
    await db_session.commit()
    _mock_roles(["Director"])
    _mock_corp_endpoints()

    esi = ESIClient(
        app.state.http, TEST_SETTINGS, db_session,
        clock=app.state.esi_clock, limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    outcomes = await sync_corporation(db_session, esi, resolver=resolver)

    # Assets kind reports no-scope (the grant holds no character-assets
    # scope and the corp-assets endpoint is not mocked); blueprints and
    # jobs sync. The unmocked corp-assets endpoint would fail the test if
    # called — the implicit scope-gate assertion.
    assert [outcome.status for outcome in outcomes] == ["no-scope", "synced", "synced"]
    assert outcomes[1].item_count == 2
    assert outcomes[2].item_count == 2

    blueprints = {
        row.item_id: row
        for row in (
            await db_session.execute(
                select(Blueprint).where(Blueprint.owner_id == CORP_ID)
            )
        ).scalars()
    }
    assert set(blueprints) == {100, 101}
    assert blueprints[100].runs == -1
    assert blueprints[100].material_efficiency == 10
    assert blueprints[101].runs == 5

    jobs = {
        row.job_id: row
        for row in (
            await db_session.execute(
                select(IndustryJob).where(IndustryJob.owner_id == CORP_ID)
            )
        ).scalars()
    }
    assert set(jobs) == {1, 2}
    assert jobs[1].status == "active"
    assert jobs[1].start_date is not None and jobs[1].start_date.year == 2026
    assert jobs[2].completed_date is not None
    assert jobs[2].activity_id == 9

    for kind in ("corp-blueprints", "corp-jobs"):
        sync = await db_session.get(DataSync, (kind, "corporation", CORP_ID))
        assert sync.status == "ok"


@respx.mock
async def test_sync_blueprints_jobs_missing_scope(app, db_session):
    from app.esi.assets import sync_corporation
    from app.esi.client import ESIClient
    from app.esi.universe import UniverseResolver
    from tests.conftest import TEST_SETTINGS

    # Roles scope only: every kind trips its own scope gate without
    # touching its endpoint.
    main = Character(
        character_id=ALPHA, name="Alpha Pilot", owner_hash="owner-alpha",
        scopes="publicData esi-characters.read_corporation_roles.v1",
        access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R", is_main=True, corporation_id=CORP_ID,
    )
    db_session.add(main)
    await db_session.commit()
    _mock_roles(["Director"])
    bp_route = respx.get(CORP_BLUEPRINTS_URL).respond(json=[])
    jobs_route = respx.get(CORP_JOBS_URL).respond(json=[])

    esi = ESIClient(
        app.state.http, TEST_SETTINGS, db_session,
        clock=app.state.esi_clock, limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    outcomes = await sync_corporation(db_session, esi, resolver=resolver)

    assert [outcome.status for outcome in outcomes] == [
        "no-scope", "no-scope", "no-scope",
    ]
    assert bp_route.call_count == 0
    assert jobs_route.call_count == 0
    sync = await db_session.get(DataSync, ("corp-blueprints", "corporation", CORP_ID))
    assert "read_blueprints" in sync.detail


@respx.mock
async def test_gate_failure_records_all_kinds(app, db_session):
    from app.esi.assets import sync_corporation
    from app.esi.client import ESIClient
    from app.esi.universe import UniverseResolver
    from app.models import AssetSync
    from tests.conftest import TEST_SETTINGS

    main = Character(
        character_id=ALPHA, name="Alpha Pilot", owner_hash="owner-alpha",
        scopes=FULL_GRANT, access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R", is_main=True, corporation_id=CORP_ID,
    )
    db_session.add(main)
    await db_session.commit()
    _mock_roles(["Personnel_Manager"])

    esi = ESIClient(
        app.state.http, TEST_SETTINGS, db_session,
        clock=app.state.esi_clock, limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    outcomes = await sync_corporation(db_session, esi, resolver=resolver)

    assert [outcome.status for outcome in outcomes] == ["no-roles"]
    assets_sync = await db_session.get(AssetSync, ("corporation", CORP_ID))
    assert assets_sync.status == "no-roles"
    for kind in ("corp-blueprints", "corp-jobs"):
        sync = await db_session.get(DataSync, (kind, "corporation", CORP_ID))
        assert sync.status == "no-roles"
        assert "Director" in sync.detail


# --- Pages ---------------------------------------------------------------------


async def _seed_data_world(db_session) -> None:
    """A synced-looking corporation: blueprints at a station and one
    "inside" an office item (ESI reports office contents against the
    office item id — the asset snapshot provides the hop to the office's
    real location), plus jobs in both active and terminal states."""
    db_session.add_all(
        [
            UniverseType(type_id=TYPE_BPO, name="Typhoon Blueprint"),
            UniverseType(type_id=TYPE_BPC, name="Panther Blueprint"),
            UniverseLocation(
                location_id=STATION, kind="station", name=STATION_NAME
            ),
            Blueprint(
                owner_type="corporation", owner_id=CORP_ID, item_id=100,
                type_id=TYPE_BPO, location_id=STATION, location_flag="CorpSAG1",
                quantity=1, runs=-1, material_efficiency=10, time_efficiency=14,
            ),
            Blueprint(
                owner_type="corporation", owner_id=CORP_ID, item_id=101,
                type_id=TYPE_BPC, location_id=STATION, location_flag="CorpSAG2",
                quantity=1, runs=5, material_efficiency=0, time_efficiency=0,
            ),
            # The office item the third blueprint sits in; its parent is
            # the station (a structure office in production, same hop).
            Asset(
                owner_type="corporation", owner_id=CORP_ID, item_id=OFFICE_ITEM,
                type_id=27, quantity=1, location_id=STATION,
                location_flag="OfficeFolder", location_type="item",
                parent_location_id=STATION, is_blueprint_copy=False,
                is_singleton=True,
            ),
            Blueprint(
                owner_type="corporation", owner_id=CORP_ID, item_id=102,
                type_id=TYPE_BPC, location_id=OFFICE_ITEM,
                location_flag="OfficeFolder", quantity=1, runs=25,
                material_efficiency=2, time_efficiency=4,
            ),
            IndustryJob(
                owner_type="corporation", owner_id=CORP_ID, job_id=1,
                installer_id=ALPHA, activity_id=1, blueprint_type_id=TYPE_BPO,
                runs=10, successful_runs=None, status="active",
                start_date=utc_now() - timedelta(hours=2),
                end_date=utc_now() + timedelta(hours=10),
                station_id=STATION,
            ),
            IndustryJob(
                owner_type="corporation", owner_id=CORP_ID, job_id=2,
                installer_id=ALPHA, activity_id=9, blueprint_type_id=TYPE_BPC,
                runs=4, successful_runs=4, status="delivered",
                start_date=utc_now() - timedelta(days=2),
                end_date=utc_now() - timedelta(days=1),
                completed_date=utc_now() - timedelta(days=1),
                station_id=STATION,
            ),
        ]
    )
    await db_session.commit()


@respx.mock
async def test_corp_blueprints_page(client, db_session):
    await _login_with_main(client, db_session)
    await _seed_data_world(db_session)
    roles_route = _mock_roles(["Director"])
    bp_route = respx.get(CORP_BLUEPRINTS_URL).respond(json=[])

    response = await client.get("/corp/blueprints")

    assert response.status_code == 200
    assert "Typhoon Blueprint" in response.text
    assert "Panther Blueprint" in response.text
    assert "Original" in response.text
    assert "Copy" in response.text
    assert "10%" in response.text
    assert STATION_NAME in response.text
    # The office-located blueprint resolves through the asset-snapshot
    # hop (office item → parent location), not a raw "#id" label.
    assert f"Location #{OFFICE_ITEM}" not in response.text
    # ESI's quantity sentinels (-2 copies, -1 originals) never render.
    assert ">-1<" not in response.text and ">-2<" not in response.text
    # DB-pure apart from the role gate.
    assert bp_route.call_count == 0
    assert roles_route.call_count == 1


@respx.mock
async def test_corp_jobs_page_active_vs_history(client, db_session):
    await _login_with_main(client, db_session)
    await _seed_data_world(db_session)
    _mock_roles(["Director"])

    response = await client.get("/corp/jobs")
    assert response.status_code == 200
    assert "Manufacturing" in response.text
    assert "Alpha Pilot" in response.text  # installer via tracked characters
    assert "active" in response.text
    assert "delivered" not in response.text
    assert "Reactions" not in response.text  # delivered job hidden

    response = await client.get("/corp/jobs?all=1")
    assert response.status_code == 200
    assert "Reactions" in response.text
    assert "delivered" in response.text


@respx.mock
async def test_corp_sync_button_shared_route(client, db_session):
    await _login_with_main(client, db_session)
    _mock_roles(["Director"])
    _mock_corp_endpoints()
    # The assets endpoint is in the grant; leave it mocked-out-failure —
    # the shared route syncs all kinds, so give it an empty page set.
    respx.get("https://esi.test/latest/corporations/98000001/assets/").respond(
        json=[], headers={"X-Pages": "1"}
    )

    response = await client.post(
        "/corp/sync", data={"back": "/corp/jobs"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/corp/jobs"
    rows = list(
        (
            await db_session.execute(
                select(Blueprint).where(Blueprint.owner_id == CORP_ID)
            )
        ).scalars()
    )
    assert len(rows) == 2

    # Unknown back targets fall back to the assets page.
    response = await client.post(
        "/corp/sync", data={"back": "https://evil.example"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/corp/assets"


@respx.mock
async def test_corp_data_pages_gated(client, db_session):
    await _login(client)

    response = await client.get("/corp/blueprints", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/corp"

    response = await client.get("/corp/jobs", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/corp"

