"""Character blueprints, skills, and industry jobs: per-kind scope gates,
the dead-token short-circuit across kinds, snapshot rows, and the pages
that read them (DB-pure renders, character filter, active-vs-history
jobs, the skills overview/table split)."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import respx
from sqlalchemy import select

from app.db import utc_now
from app.models import (
    Blueprint,
    Character,
    CharacterLoyalty,
    DataSync,
    IndustryJob,
    Skill,
    UniverseCorporation,
    UniverseLocation,
    UniverseType,
)
from tests.conftest import make_access_token, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
ASSETS_URL = "https://esi.test/latest/characters/1234/assets/"
BLUEPRINTS_URL = "https://esi.test/latest/characters/1234/blueprints/"
SKILLS_URL = "https://esi.test/latest/characters/1234/skills/"
LOYALTY_URL = "https://esi.test/latest/characters/1234/loyalty/points/"
JOBS_URL = "https://esi.test/latest/characters/1234/industry/jobs/"

ALPHA = 1234
STATION = 6001
STRUCTURE = 1022167642188  # "Amamake - Fort Amamake"
TYPE_BPO = 999  # "Typhoon Blueprint"
TYPE_BPC = 998  # "Panther Blueprint"
SKILL_INDUSTRY = 3380  # "Industry"
SKILL_ADVANCED = 3388  # "Advanced Industry"
LP_CORP = 1000001  # the offering corporation
LP_WRONG_CURRENCY_CORP = 1000002  # balance in a non-offering store

FULL_GRANT = (
    "publicData esi-assets.read_assets.v1 esi-characters.read_blueprints.v1 "
    "esi-skills.read_skills.v1 esi-characters.read_loyalty.v1 "
    "esi-industry.read_character_jobs.v1 "
    "esi-universe.read_structures.v1"
)

STATION_NAME = "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
STRUCTURE_NAME = "Amamake - Fort Amamake"


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


def _character(scopes: str = FULL_GRANT) -> Character:
    return Character(
        character_id=ALPHA,
        name="Alpha Pilot",
        owner_hash="owner-alpha",
        scopes=scopes,
        access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R",
    )


def _blueprint_payload() -> list[dict]:
    return [
        {
            "item_id": 200,
            "type_id": TYPE_BPO,
            "location_id": STATION,
            "location_flag": "Hangar",
            "quantity": 1,
            "runs": -1,
            "material_efficiency": 10,
            "time_efficiency": 14,
        },
        {
            "item_id": 201,
            "type_id": TYPE_BPC,
            "location_id": STATION,
            "location_flag": "Hangar",
            "quantity": -2,
            "runs": 5,
            "material_efficiency": 0,
            "time_efficiency": 0,
        },
        {
            # Sits in a structure hangar: the location names the structure
            # directly (no snapshot hop), so the blueprints sync resolves
            # it like any untyped location id.
            "item_id": 202,
            "type_id": TYPE_BPO,
            "location_id": STRUCTURE,
            "location_flag": "Hangar",
            "quantity": 1,
            "runs": -1,
            "material_efficiency": 2,
            "time_efficiency": 4,
        },
    ]


def _skills_payload() -> dict:
    return {
        "skills": [
            {
                "skill_id": SKILL_INDUSTRY,
                "trained_skill_level": 5,
                "active_skill_level": 5,
                "skillpoints_in_skill": 256000,
            },
            {
                "skill_id": SKILL_ADVANCED,
                "trained_skill_level": 4,
                "active_skill_level": 5,  # implant boost
                "skillpoints_in_skill": 90510,
            },
        ],
        "total_sp": 346510,
    }


def _loyalty_payload() -> list[dict]:
    return [
        {"corporation_id": LP_CORP, "points": 200_000},
        {"corporation_id": LP_WRONG_CURRENCY_CORP, "points": 632_000},
    ]


def _jobs_payload() -> list[dict]:
    return [
        {
            "job_id": 10,
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
            "job_id": 11,
            "installer_id": ALPHA,
            "activity_id": 3,
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


def _seed_type_names(db_session) -> None:
    """The syncs' best-effort name resolution reads these as existing, so
    no /universe/types/ call is needed (or mocked). The station is
    pre-resolved so the blueprints kind's location pass skips it."""
    db_session.add_all(
        [
            UniverseType(type_id=TYPE_BPO, name="Typhoon Blueprint"),
            UniverseType(type_id=TYPE_BPC, name="Panther Blueprint"),
            UniverseType(type_id=SKILL_INDUSTRY, name="Industry"),
            UniverseType(type_id=SKILL_ADVANCED, name="Advanced Industry"),
            UniverseLocation(location_id=STATION, kind="station", name=STATION_NAME),
        ]
    )


def _mock_character_endpoints():
    respx.get(ASSETS_URL).respond(json=[], headers={"X-Pages": "1"})
    respx.get(BLUEPRINTS_URL).respond(
        json=_blueprint_payload(), headers={"X-Pages": "1"}
    )
    respx.get(SKILLS_URL).respond(json=_skills_payload())
    respx.get(LOYALTY_URL).respond(json=_loyalty_payload())
    respx.get(JOBS_URL).respond(json=_jobs_payload(), headers={"X-Pages": "1"})
    # The loyalty kind's best-effort name pass reads the corporations.
    respx.get(f"https://esi.test/latest/corporations/{LP_CORP}/").respond(
        json={"name": "Test Liberation Force"}
    )
    respx.get(f"https://esi.test/latest/corporations/{LP_WRONG_CURRENCY_CORP}/").respond(
        json={"name": "Paragon Syndicate"}
    )
    # The structure-located blueprint resolves through the scoped
    # structures endpoint (docking access assumed).
    respx.get(f"https://esi.test/latest/universe/structures/{STRUCTURE}/").respond(
        json={"name": STRUCTURE_NAME, "solar_system_id": 30002537}
    )


def _make_esi(app, db_session):
    from app.esi.client import ESIClient
    from tests.conftest import TEST_SETTINGS

    return ESIClient(
        app.state.http, TEST_SETTINGS, db_session,
        clock=app.state.esi_clock, limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


# --- Sync ----------------------------------------------------------------------


@respx.mock
async def test_sync_character_data(app, db_session):
    from app.esi.assets import sync_all_characters
    from app.esi.universe import UniverseResolver
    from tests.conftest import TEST_SETTINGS

    character = _character()
    db_session.add(character)
    _seed_type_names(db_session)
    await db_session.commit()
    _mock_character_endpoints()

    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    outcomes = await sync_all_characters(
        db_session, esi, [character], resolver=resolver
    )

    assert [outcome.status for outcome in outcomes] == [
        "synced", "synced", "synced", "synced", "synced",
    ]
    assert outcomes[1].item_count == 3
    assert outcomes[2].item_count == 2
    assert outcomes[3].item_count == 2
    assert outcomes[4].item_count == 2

    blueprints = {
        row.item_id: row
        for row in (
            await db_session.execute(
                select(Blueprint).where(Blueprint.owner_id == ALPHA)
            )
        ).scalars()
    }
    assert set(blueprints) == {200, 201, 202}
    # The structure-located blueprint's location resolved on its own (no
    # snapshot hop exists for it).
    structure = await db_session.get(UniverseLocation, STRUCTURE)
    assert structure is not None
    assert structure.name == STRUCTURE_NAME
    assert blueprints[200].runs == -1
    assert blueprints[200].material_efficiency == 10
    assert blueprints[201].runs == 5

    skills = {
        row.skill_id: row
        for row in (
            await db_session.execute(select(Skill).where(Skill.owner_id == ALPHA))
        ).scalars()
    }
    assert set(skills) == {SKILL_INDUSTRY, SKILL_ADVANCED}
    assert skills[SKILL_INDUSTRY].trained_skill_level == 5
    assert skills[SKILL_ADVANCED].trained_skill_level == 4
    assert skills[SKILL_ADVANCED].active_skill_level == 5
    assert skills[SKILL_ADVANCED].skillpoints_in_skill == 90510

    jobs = {
        row.job_id: row
        for row in (
            await db_session.execute(
                select(IndustryJob).where(IndustryJob.owner_id == ALPHA)
            )
        ).scalars()
    }
    assert set(jobs) == {10, 11}
    assert jobs[10].status == "active"
    assert jobs[11].completed_date is not None
    assert jobs[11].activity_id == 3

    loyalty = {
        row.corporation_id: row
        for row in (
            await db_session.execute(
                select(CharacterLoyalty).where(
                    CharacterLoyalty.character_id == ALPHA
                )
            )
        ).scalars()
    }
    assert set(loyalty) == {LP_CORP, LP_WRONG_CURRENCY_CORP}
    assert loyalty[LP_CORP].points == 200_000
    assert loyalty[LP_WRONG_CURRENCY_CORP].points == 632_000
    # The best-effort name pass cached the store corporations.
    corp = await db_session.get(UniverseCorporation, LP_CORP)
    assert corp is not None and corp.name == "Test Liberation Force"

    for kind in ("char-blueprints", "char-skills", "char-loyalty", "char-jobs"):
        sync = await db_session.get(DataSync, (kind, "character", ALPHA))
        assert sync.status == "ok"


@respx.mock
async def test_sync_character_missing_scope(app, db_session):
    from app.esi.assets import sync_all_characters
    from app.esi.universe import UniverseResolver
    from tests.conftest import TEST_SETTINGS

    character = _character(scopes="publicData esi-assets.read_assets.v1")
    db_session.add(character)
    await db_session.commit()
    _mock_character_endpoints()

    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    outcomes = await sync_all_characters(
        db_session, esi, [character], resolver=resolver
    )

    # Assets sync (empty); the four data kinds trip their own scope gates
    # without touching their endpoints.
    assert [outcome.status for outcome in outcomes] == [
        "synced", "no-scope", "no-scope", "no-scope", "no-scope",
    ]
    assert respx.get(BLUEPRINTS_URL).call_count == 0
    assert respx.get(SKILLS_URL).call_count == 0
    assert respx.get(LOYALTY_URL).call_count == 0
    assert respx.get(JOBS_URL).call_count == 0
    sync = await db_session.get(DataSync, ("char-blueprints", "character", ALPHA))
    assert sync.status == "no-scope"
    assert "read_blueprints" in sync.detail


@respx.mock
async def test_reauth_short_circuits_remaining_kinds(app, db_session):
    from app.esi.assets import sync_all_characters
    from app.esi.universe import UniverseResolver
    from tests.conftest import TEST_SETTINGS

    character = _character()
    character.access_token_expires_at = utc_now() - timedelta(minutes=1)
    db_session.add(character)
    await db_session.commit()
    # A dead refresh token: SSO rejects it and the first authenticated
    # fetch raises ReauthorizationRequired.
    respx.post(SSO_TOKEN_URL).respond(status_code=400, json={"error": "invalid_grant"})
    _mock_character_endpoints()

    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    outcomes = await sync_all_characters(
        db_session, esi, [character], resolver=resolver
    )

    assert [outcome.status for outcome in outcomes] == [
        "reauth", "reauth", "reauth", "reauth", "reauth",
    ]
    # The assets fetch fails the refresh before any data endpoint is
    # touched; the short-circuit keeps the other kinds from re-attempting
    # the same dead refresh.
    assert respx.get(BLUEPRINTS_URL).call_count == 0
    assert respx.get(SKILLS_URL).call_count == 0
    assert respx.get(LOYALTY_URL).call_count == 0
    assert respx.get(JOBS_URL).call_count == 0
    for kind in ("char-blueprints", "char-skills", "char-loyalty", "char-jobs"):
        sync = await db_session.get(DataSync, (kind, "character", ALPHA))
        assert sync.status == "reauth"


# --- Pages ---------------------------------------------------------------------


async def _seed_data_world(db_session) -> None:
    """A synced-looking character: blueprints at a station, a skill sheet,
    and jobs in both active and terminal states. The character itself
    comes from the login; only the synced-looking data is seeded."""
    db_session.add_all(
        [
            UniverseType(type_id=TYPE_BPO, name="Typhoon Blueprint"),
            UniverseType(type_id=TYPE_BPC, name="Panther Blueprint"),
            UniverseType(type_id=SKILL_INDUSTRY, name="Industry"),
            UniverseType(type_id=SKILL_ADVANCED, name="Advanced Industry"),
            UniverseLocation(location_id=STATION, kind="station", name=STATION_NAME),
            UniverseLocation(
                location_id=STRUCTURE, kind="structure", name=STRUCTURE_NAME
            ),
            Blueprint(
                owner_type="character", owner_id=ALPHA, item_id=200,
                type_id=TYPE_BPO, location_id=STATION, location_flag="Hangar",
                quantity=1, runs=-1, material_efficiency=10, time_efficiency=14,
            ),
            Blueprint(
                owner_type="character", owner_id=ALPHA, item_id=201,
                type_id=TYPE_BPC, location_id=STATION, location_flag="Hangar",
                quantity=-2, runs=5, material_efficiency=0, time_efficiency=0,
            ),
            Blueprint(
                owner_type="character", owner_id=ALPHA, item_id=202,
                type_id=TYPE_BPO, location_id=STRUCTURE, location_flag="Hangar",
                quantity=1, runs=-1, material_efficiency=2, time_efficiency=4,
            ),
            Skill(
                owner_type="character", owner_id=ALPHA, skill_id=SKILL_INDUSTRY,
                trained_skill_level=5, active_skill_level=5,
                skillpoints_in_skill=256000,
            ),
            Skill(
                owner_type="character", owner_id=ALPHA, skill_id=SKILL_ADVANCED,
                trained_skill_level=4, active_skill_level=5,
                skillpoints_in_skill=90510,
            ),
            IndustryJob(
                owner_type="character", owner_id=ALPHA, job_id=10,
                installer_id=ALPHA, activity_id=1, blueprint_type_id=TYPE_BPO,
                runs=10, successful_runs=None, status="active",
                start_date=utc_now() - timedelta(hours=2),
                end_date=utc_now() + timedelta(hours=10),
                station_id=STATION,
            ),
            IndustryJob(
                owner_type="character", owner_id=ALPHA, job_id=11,
                installer_id=ALPHA, activity_id=3, blueprint_type_id=TYPE_BPC,
                runs=4, successful_runs=4, status="delivered",
                start_date=utc_now() - timedelta(days=2),
                end_date=utc_now() - timedelta(days=1),
                completed_date=utc_now() - timedelta(days=1),
                station_id=STATION,
            ),
        ]
    )
    for kind in ("char-blueprints", "char-skills", "char-jobs"):
        db_session.add(
            DataSync(
                kind=kind, owner_type="character", owner_id=ALPHA,
                status="ok", synced_at=utc_now(),
            )
        )
    await db_session.commit()


@respx.mock
async def test_blueprints_page(client, db_session):
    await _login(client)
    await _seed_data_world(db_session)

    response = await client.get("/blueprints")

    assert response.status_code == 200
    assert "Typhoon Blueprint" in response.text
    assert "Panther Blueprint" in response.text
    assert "Original" in response.text
    assert "Copy" in response.text
    assert "Alpha Pilot" in response.text  # owner column
    assert STATION_NAME in response.text
    assert STRUCTURE_NAME in response.text  # resolved, not "Location #id"
    assert f"#{STRUCTURE}" not in response.text
    # ESI's quantity sentinels never render.
    assert ">-2<" not in response.text
    # The character filter narrows to one owner; an unknown id (stale URL)
    # falls back to every character rather than an empty page.
    response = await client.get(f"/blueprints?char={ALPHA}")
    assert response.status_code == 200
    assert "Typhoon Blueprint" in response.text
    response = await client.get("/blueprints?char=999999")
    assert response.status_code == 200
    assert "Typhoon Blueprint" in response.text


@respx.mock
async def test_skills_page_overview_and_sheet(client, db_session):
    await _login(client)
    await _seed_data_world(db_session)

    response = await client.get("/skills")
    assert response.status_code == 200
    assert "Alpha Pilot" in response.text
    assert "2 skills" in response.text
    assert "346,510" in response.text  # summed skillpoints
    # Sheet hidden in the overview — "Advanced Industry" is the sentinel
    # because the nav group is itself named "Industry".
    assert "Advanced Industry" not in response.text

    response = await client.get(f"/skills?char={ALPHA}")
    assert response.status_code == 200
    assert "Advanced Industry" in response.text
    assert "Advanced Industry" in response.text
    assert "V" in response.text
    # Trained IV with an active implant boost reads distinctly.
    assert "IV" in response.text


@respx.mock
async def test_jobs_page_active_vs_history(client, db_session):
    await _login(client)
    await _seed_data_world(db_session)

    response = await client.get("/jobs")
    assert response.status_code == 200
    assert "Manufacturing" in response.text
    assert "Alpha Pilot" in response.text
    assert "active" in response.text
    assert "delivered" not in response.text

    response = await client.get("/jobs?all=1")
    assert response.status_code == 200
    assert "delivered" in response.text
    assert "Research TE" in response.text


@respx.mock
async def test_sync_button_shared_route(client, db_session):
    await _login(client, scopes=FULL_GRANT.split())
    _mock_character_endpoints()
    _seed_type_names(db_session)
    await db_session.commit()

    response = await client.post(
        "/character/sync", data={"back": "/jobs", "char": str(ALPHA)},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/jobs?char={ALPHA}"
    rows = list(
        (
            await db_session.execute(
                select(Blueprint).where(Blueprint.owner_id == ALPHA)
            )
        ).scalars()
    )
    assert len(rows) == 3

    # Unknown back targets fall back to the blueprints page; a garbage
    # character filter is dropped rather than threaded through.
    response = await client.post(
        "/character/sync", data={"back": "https://evil.example", "char": "nope"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/blueprints"
