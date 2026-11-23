"""Structures registry tests (M3): the split schema's constraints, the
CRUD save path (create/edit/further-registration are one form), default
demotion, the validated supercapital capability, the import card, and
the local system type-ahead. ESI's system lookup is mocked with respx
(save-time resolution, never at render)."""

from urllib.parse import parse_qs, urlparse

import pytest
import respx
from httpx import Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Structure, StructureRegistration, UniverseLocation
from tests.conftest import token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
AMAMAKE = {"name": "Amamake", "security_status": 0.3}
DEEP_SYSTEM = {"name": "UUA-F4", "security_status": -0.6}


async def _login(client):
    """Authenticate through the mocked SSO flow (call inside a respx
    context); returns the session-carrying client."""
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})
    return client


def seed_system(db_session, location_id=30004482, name="Amamake"):
    db_session.add(
        UniverseLocation(
            location_id=location_id, kind="solar_system", name=name
        )
    )


async def seed_structure(db_session, **overrides) -> Structure:
    structure = Structure(
        name=overrides.pop("name", "Test Azbel"),
        structure_type=overrides.pop("structure_type", "azbel"),
        system_id=overrides.pop("system_id", 30004482),
        system_name=overrides.pop("system_name", "Amamake"),
        security_class=overrides.pop("security_class", "low"),
        **overrides,
    )
    db_session.add(structure)
    await db_session.flush()
    return structure


def form_for(structure=None, activity="manufacturing", **fields) -> dict:
    data = {
        "activity": activity,
        "name": "Amamake - Police Weapons Facility",
        "structure_type": "azbel",
        "me_rig": "t1",
        "te_rig": "t1",
        "tax_rate": "0.5%",
        "is_default": "on",
        "system_id": "30004482",
    }
    if structure is not None:
        data["structure_id"] = str(structure.id)
        data["name"] = structure.name
        data["structure_type"] = structure.structure_type
    data.update(fields)
    return data


async def test_create_structure_with_registration(app, client, db_session):
    """The M3 validation scenario, part 1: an Azbel with T1/T1 rigs in a
    known system creates with its registration, security derived from
    ESI at save time, one default."""
    with respx.mock:
        respx.get("https://esi.test/latest/universe/systems/30004482/").respond(
            json=AMAMAKE
        )
        response = await (await _login(client)).post(
            "/structures", data=form_for()
        )
    assert response.status_code == 303, response.text
    structure = (
        await db_session.execute(select(Structure))
    ).scalar_one()
    assert structure.name == "Amamake - Police Weapons Facility"
    assert structure.structure_type == "azbel"
    assert structure.system_id == 30004482
    assert structure.system_name == "Amamake"
    assert structure.security_class == "low"
    assert not structure.supercapital_assembly
    registration = (
        await db_session.execute(select(StructureRegistration))
    ).scalar_one()
    assert registration.activity == "manufacturing"
    assert (registration.me_rig, registration.te_rig) == ("t1", "t1")
    assert registration.tax_rate == pytest.approx(0.005)
    assert registration.is_default


async def test_second_registration_same_structure(app, client, db_session):
    """The M3 validation scenario, part 2: registering the same Azbel
    for invention adds a second registration (rigs not relevant there
    by choice), one structure."""
    structure = await seed_structure(db_session)
    db_session.add(
        StructureRegistration(
            structure_id=structure.id, activity="manufacturing", is_default=True
        )
    )
    await db_session.commit()

    with respx.mock:
        respx.get("https://esi.test/latest/universe/systems/30004482/").respond(
            json=AMAMAKE
        )
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(
                structure, activity="invention", me_rig="none", is_default="on"
            ),
        )
    assert response.status_code == 303, response.text
    registrations = (
        await db_session.execute(select(StructureRegistration))
    ).scalars().all()
    assert {r.activity for r in registrations} == {"manufacturing", "invention"}
    assert len({r.structure_id for r in registrations}) == 1


async def test_default_demotion(app, client, db_session):
    """Setting a new default in a group demotes the previous one —
    exactly one default per activity after the swap."""
    first = await seed_structure(db_session, name="First")
    second = await seed_structure(db_session, name="Second")
    db_session.add_all([
        StructureRegistration(
            structure_id=first.id, activity="manufacturing", is_default=True
        ),
        StructureRegistration(
            structure_id=second.id, activity="manufacturing", is_default=False
        ),
    ])
    await db_session.commit()

    with respx.mock:
        respx.get("https://esi.test/latest/universe/systems/30004482/").respond(
            json=AMAMAKE
        )
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(second, name="Second", is_default="on"),
        )
    assert response.status_code == 303, response.text
    defaults = (
        await db_session.execute(
            select(StructureRegistration).where(
                StructureRegistration.activity == "manufacturing",
                StructureRegistration.is_default,
            )
        )
    ).scalars().all()
    assert len(defaults) == 1
    assert defaults[0].structure_id == second.id


async def test_partial_unique_enforces_one_default(db_session):
    """The partial unique index itself: two defaults on one activity
    cannot coexist at the storage layer."""
    structure = await seed_structure(db_session)
    other = await seed_structure(db_session, name="Other")
    db_session.add(
        StructureRegistration(structure_id=structure.id, activity="copying",
                              is_default=True)
    )
    await db_session.flush()
    db_session.add(
        StructureRegistration(structure_id=other.id, activity="copying",
                              is_default=True)
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_supercapital_requires_nullsec(app, client):
    """The capability is validated, not trusted: a supercap flag on a
    lowsec system fails; the same flag on nullsec saves."""
    with respx.mock:
        low = respx.get(
            "https://esi.test/latest/universe/systems/30004482/"
        ).respond(json=AMAMAKE)
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(supercapital_assembly="on"),
        )
        assert response.status_code == 422
        assert "nullsec" in response.text

        low.mock(return_value=Response(200, json=DEEP_SYSTEM))
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(
                supercapital_assembly="on",
                name="Deep Null Sotiyo",
                structure_type="sotiyo",
            ),
        )
        assert response.status_code == 303, response.text


async def test_supercapital_requires_ec_and_system(app, client):
    with respx.mock:
        # No system selected at all: the flag cannot be validated.
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(supercapital_assembly="on", system_id="",
                          security_class=""),
        )
        assert response.status_code == 422
        # A refinery (reactions) cannot host the capability either way.
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(
                supercapital_assembly="on",
                activity="reactions",
                structure_type="tatara",
                system_id="",
                security_class="null",
            ),
        )
        assert response.status_code == 422
        assert "engineering-complex" in response.text


async def test_reactions_only_in_refineries(app, client):
    with respx.mock:
        respx.get("https://esi.test/latest/universe/systems/30004482/").respond(
            json=AMAMAKE
        )
        response = await (await _login(client)).post(
            "/structures", data=form_for(activity="reactions")
        )
        assert response.status_code == 422
        assert "cannot host" in response.text

        response = await (await _login(client)).post(
            "/structures",
            data=form_for(activity="reactions", structure_type="tatara",
                          me_rig="none", te_rig="t2"),
        )
        assert response.status_code == 303, response.text


async def test_esi_failure_falls_back_to_local_system(app, client, db_session):
    """ESI unreachable at save time: the local universe_locations row
    names the system; the security class stays unset (hand-set applies
    on a retry)."""
    seed_system(db_session)
    await db_session.commit()
    with respx.mock:
        respx.get("https://esi.test/latest/universe/systems/30004482/").respond(
            status_code=500
        )
        response = await (await _login(client)).post(
            "/structures",
            data=form_for(system_id="30004482", security_class="low"),
        )
    assert response.status_code == 303, response.text
    structure = (
        await db_session.execute(select(Structure))
    ).scalar_one()
    assert structure.system_name == "Amamake"
    assert structure.security_class == "low"  # hand-set fallback


async def test_unknown_system_rejected(app, client):
    with respx.mock:
        respx.get("https://esi.test/latest/universe/systems/99999/").respond(
            status_code=404
        )
        response = await (await _login(client)).post(
            "/structures", data=form_for(system_id="99999")
        )
    assert response.status_code == 422
    assert "could not be resolved" in response.text


@respx.mock
async def test_system_typeahead_local_only(app, client, db_session):
    seed_system(db_session, 30004482, "Amamake")
    seed_system(db_session, 30002053, "Hek")
    await db_session.commit()
    response = await (await _login(client)).get(
        "/structures/systems/search", params={"q": "am"}
    )
    assert response.status_code == 200
    systems = response.json()["systems"]
    assert [s["name"] for s in systems] == ["Amamake"]


@respx.mock
async def test_registry_page_groups_and_import_card(app, client, db_session):
    """The page renders grouped by activity, and sync sightings that
    aren't registered become import candidates."""
    structure = await seed_structure(db_session)
    db_session.add(
        StructureRegistration(structure_id=structure.id,
                              activity="manufacturing", is_default=True)
    )
    db_session.add_all([
        UniverseLocation(
            location_id=10**12 + 1, kind="structure",
            name="Lirerim - Chlorohus", system_id=30004482,
        ),
        UniverseLocation(
            location_id=10**12 + 2, kind="structure", name=None,
            restricted=True,
        ),
        # Already registered: the seed structure's sighting is absent.
        UniverseLocation(location_id=10**12 + 3, kind="structure",
                         name="Registered One"),
    ])
    db_session.add(Structure(name="Registered One", structure_type="station",
                             location_id=10**12 + 3))
    await db_session.commit()

    response = await (await _login(client)).get("/structures")
    assert response.status_code == 200
    body = response.text
    assert "manufacturing" in body
    assert "1 registration" in body
    assert "Lirerim - Chlorohus" in body
    assert "Registered One" not in body  # registered sightings don't re-import
    assert "Structure #1000000000002" in body  # restricted stays listed


@respx.mock
async def test_import_prefills_form(app, client, db_session):
    db_session.add_all([
        UniverseLocation(
            location_id=10**12 + 1, kind="structure",
            name="Lirerim - Chlorohus", system_id=30004482,
        ),
        UniverseLocation(
            location_id=30004482, kind="solar_system", name="Amamake"
        ),
    ])
    await db_session.commit()
    response = await (await _login(client)).get(
        "/structures", params={"import": 10**12 + 1}
    )
    assert response.status_code == 200
    assert "Lirerim - Chlorohus" in response.text
    # The sighting's location id rides the form as the import tie.
    assert 'name="location_id" value="1000000000001"' in response.text


@respx.mock
async def test_delete_registration_keeps_structure(app, client, db_session):
    structure = await seed_structure(db_session)
    keep = StructureRegistration(structure_id=structure.id,
                                 activity="manufacturing")
    drop = StructureRegistration(structure_id=structure.id, activity="copying")
    db_session.add_all([keep, drop])
    await db_session.commit()

    response = await (await _login(client)).post(
        f"/structures/{structure.id}/{drop.id}/delete"
    )
    assert response.status_code == 303
    remaining = (
        await db_session.execute(select(StructureRegistration))
    ).scalars().all()
    assert [r.activity for r in remaining] == ["manufacturing"]
    assert (
        await db_session.execute(select(Structure))
    ).scalar_one() is not None


@respx.mock
async def test_last_registration_deletes_structure(app, client, db_session):
    structure = await seed_structure(db_session)
    registration = StructureRegistration(structure_id=structure.id,
                                         activity="reactions")
    db_session.add(registration)
    await db_session.commit()

    response = await (await _login(client)).post(
        f"/structures/{structure.id}/{registration.id}/delete"
    )
    assert response.status_code == 303
    assert (await db_session.execute(select(Structure))).scalars().all() == []


async def test_unauthenticated_redirects(client):
    response = await client.post("/structures", data=form_for())
    assert response.status_code in (302, 303)
    response = await client.get("/structures")
    assert response.status_code == 302


def test_effective_rig_percent_by_family():
    """Rig security scaling is per rig family (live ESI dogma 2355-2357):
    engineering-complex rigs ×1.0/×1.9/×2.1, refinery reactor rigs
    ×1.0 low / ×1.1 null with no highsec factor."""
    from app.facilities import effective_rig_percent

    # EC rigs (manufacturing, invention).
    assert effective_rig_percent(
        "manufacturing", "me", "t2", "null"
    ) == pytest.approx(2.4 * 2.1)
    assert effective_rig_percent(
        "invention", "te", "t1", "low"
    ) == pytest.approx(20.0 * 1.9)
    assert effective_rig_percent(
        "manufacturing", "me", "t1", "high"
    ) == pytest.approx(2.0)
    # Reactor rigs scale differently.
    assert effective_rig_percent(
        "reactions", "me", "t2", "null"
    ) == pytest.approx(2.4 * 1.1)
    assert effective_rig_percent(
        "reactions", "te", "t1", "low"
    ) == pytest.approx(20.0)
    # Copying has no rig effect; a class with no factor for the family
    # (hisec reactions — impossible in practice) defaults to unscaled.
    assert effective_rig_percent("copying", "te", "t1", "low") == 0.0
    assert effective_rig_percent(
        "reactions", "me", "t1", "high"
    ) == pytest.approx(2.0)
