"""Build-plan export tests (M6 PR 5): POST /plans snapshots the resolved
chain into build_plans / build_plan_nodes / build_plan_materials — the
plan of record. Snapshot fidelity asserts against the miniature golden
chain (the chain_db fixture's Typhoon slice), so every planner-page
golden carries onto the persisted rows; the fork rules pin the
Re-run semantics (auto-abandon only on the explicit from_plan path)."""

import json
from urllib.parse import parse_qs, urlparse

import pytest
import respx
from sqlalchemy import select

from app.models import (
    BuildPlan,
    BuildPlanMaterial,
    BuildPlanNode,
    Structure,
    StructureRegistration,
)
from tests.conftest import token_response
from tests.test_planner_chain import chain_db  # noqa: F401  (fixture)
from tests.test_planner_plan import MAIN, planner_db  # noqa: F401  (fixture)

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"

TYPHOON = 644
CPG = 20410
CARBIDE = 16672
FUEL = 4100
ICE = 4102
TRITANIUM = 34


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _export(client, **fields):
    """POST the export form (the planner page's hidden fields) and return
    the created plan's id via the redirect target."""
    response = await client.post("/plans", data=fields, follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/plans/")
    return int(location.rsplit("/", 1)[1])


async def _plan_row(db, plan_id) -> BuildPlan:
    plan = await db.get(BuildPlan, plan_id)
    assert plan is not None
    return plan


async def _nodes(db, plan_id) -> dict[int, BuildPlanNode]:
    rows = (
        (
            await db.execute(
                select(BuildPlanNode).where(BuildPlanNode.plan_id == plan_id)
            )
        )
        .scalars()
        .all()
    )
    return {row.type_id: row for row in rows}


async def _materials(db, plan_id) -> dict[int, BuildPlanMaterial]:
    rows = (
        (
            await db.execute(
                select(BuildPlanMaterial).where(BuildPlanMaterial.plan_id == plan_id)
            )
        )
        .scalars()
        .all()
    )
    return {row.type_id: row for row in rows}


@respx.mock
async def test_export_requires_auth(client, chain_db):  # noqa: F811
    response = await client.post(
        "/plans", data={"target": TYPHOON, "qty": 10}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


@respx.mock
async def test_export_snapshots_the_golden_chain(client, chain_db):  # noqa: F811
    """The plan of record: every planner-page golden carries onto the
    persisted rows — node identity and calc snapshot, materials, pinned
    facilities and participants, the copy readout, and the export-time
    stage states and availability."""
    await _login(client)
    plan_id = await _export(client, target=TYPHOON, qty=10)

    plan = await _plan_row(chain_db, plan_id)
    assert plan.status == "draft"
    assert plan.name == "Typhoon ×10"  # the default name
    assert plan.target_type_id == TYPHOON and plan.target_name == "Typhoon"
    assert plan.units == 10
    assert plan.corporation_id == 98000001  # the main's corp, the pool key
    assert plan.source_query == "?target=644&qty=10"
    assert plan.superseded_by_plan_id is None
    assert plan.activated_at is None and plan.abandoned_at is None

    # Participants pinned as the RESOLVED pool (ids + the time readouts).
    participants = json.loads(plan.participants_json)
    by_id = {row["character_id"]: row for row in participants}
    assert set(by_id) == {MAIN, 5678}
    assert by_id[MAIN]["name"] == "Test Pilot"
    assert by_id[MAIN]["holds_target_gate"] is True
    assert by_id[5678]["missing_target_skills"] == ["Advanced Industry"]

    # Facilities pinned per activity (registry defaults included); the
    # copy readout rides beside them.
    facilities = json.loads(plan.facilities_json)
    assert set(facilities) == {
        "manufacturing", "copying", "invention", "reactions"
    }
    assert facilities["manufacturing"]["structure_name"] == "Amamake - Test Azbel"
    assert facilities["manufacturing"]["me_rig"] == "t1"
    assert facilities["manufacturing"]["tax_rate"] == 0.005
    assert facilities["reactions"]["structure_name"] == "Amamake - Test Tatara"
    assert facilities["copying"] is None and facilities["invention"] is None
    assert plan.copy_facility_json is None
    assert plan.copy_seconds_per_run == 12_240
    assert plan.copy_total_seconds == 122_400
    assert json.loads(plan.cycles_json) == []

    # No src param: the default (corp-side) source set, snapshotted as
    # null — absence-means-default, same as the planner URL.
    assert plan.sources_json is None

    # The four buildable nodes of the miniature chain.
    nodes = await _nodes(chain_db, plan_id)
    assert set(nodes) == {TYPHOON, CPG, CARBIDE, FUEL}

    target = nodes[TYPHOON]
    assert target.is_target and target.phase == 4
    assert target.qty == 10 and target.runs == 10 and target.jobs == 1
    assert target.me == 10 and target.te == 20  # the corp BPO
    assert target.has_original and target.bpc_pool_runs is None
    assert target.blueprint_name == "Typhoon Blueprint"
    assert json.loads(target.install_json)["total"] == pytest.approx(
        958_869.3744, rel=1e-9
    )
    # The skills read orders level-descending.
    assert json.loads(target.skills_json) == [
        {"skill_id": 22242, "name": "Advanced Industry", "level": 3},
        {"skill_id": 3380, "name": "Industry", "level": 1},
    ]
    # The M4 golden demand, snapshotted as the node's material list.
    demands = {m["type_id"]: m for m in json.loads(target.materials_json)}
    assert demands[TRITANIUM]["required_qty"] == 68_571_360
    assert demands[TRITANIUM]["buildable"] is False
    assert demands[CPG]["required_qty"] == 471
    assert demands[CPG]["buildable"] is True

    cpg = nodes[CPG]
    assert cpg.phase == 3 and cpg.runs == 157
    assert not cpg.has_original and cpg.bpc_pool_runs == 11
    cpg_demands = {m["type_id"]: m for m in json.loads(cpg.materials_json)}
    assert cpg_demands[CARBIDE]["required_qty"] == 14_952

    # Export-time stage states and availability (the same values the
    # planner page showed; the refresh tick owns them from here on).
    assert nodes[FUEL].state == "ready" and nodes[FUEL].state_reason is None
    assert nodes[FUEL].available_qty == 40  # office stock measured at export
    assert nodes[CARBIDE].state == "missing"
    assert nodes[CARBIDE].state_reason == "skill-gated"
    assert not nodes[CARBIDE].holds_gate
    assert target.state == "missing"
    assert target.state_reason == "waiting-upstream"

    # The acquisition table: chain terminators summed across phases,
    # measured against the default source set.
    materials = await _materials(chain_db, plan_id)
    assert set(materials) == {TRITANIUM, ICE}
    assert materials[TRITANIUM].required_qty == 68_582_789
    assert materials[TRITANIUM].available_qty == 2_000_000
    assert materials[TRITANIUM].acquire_via == "Mining / reprocessing / market"
    assert materials[TRITANIUM].is_purchase_line is False
    assert materials[ICE].required_qty == 10
    assert materials[ICE].available_qty == 10


@respx.mock
async def test_export_honors_explicit_name(client, chain_db):  # noqa: F811
    await _login(client)
    plan_id = await _export(
        client, target=TYPHOON, qty=10, name="Jackdaw run — November"
    )
    plan = await _plan_row(chain_db, plan_id)
    assert plan.name == "Jackdaw run — November"


@respx.mock
async def test_export_blank_name_falls_back_to_default(client, chain_db):  # noqa: F811
    await _login(client)
    plan_id = await _export(client, target=TYPHOON, qty=10, name="   ")
    assert (await _plan_row(chain_db, plan_id)).name == "Typhoon ×10"


@respx.mock
async def test_export_invalid_target_redirects_to_planner(client, chain_db):  # noqa: F811
    await _login(client)
    response = await client.post(
        "/plans", data={"target": TRITANIUM}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/planner"


@respx.mock
async def test_export_pins_explicit_participants(client, chain_db):  # noqa: F811
    """An explicit `p` pool pins exactly those participants, and the
    source_query round-trips the param so Re-run re-resolves honestly."""
    await _login(client)
    plan_id = await _export(client, target=TYPHOON, qty=10, p=MAIN)
    plan = await _plan_row(chain_db, plan_id)
    participants = json.loads(plan.participants_json)
    assert [row["character_id"] for row in participants] == [MAIN]
    assert plan.source_query == "?target=644&qty=10&p=1234"


@respx.mock
async def test_export_pins_the_source_set(client, chain_db):  # noqa: F811
    """`src` refs snapshot verbatim (the present-even-empty sentinel
    included) and the export-time measurement follows the selection."""
    await _login(client)
    plan_id = await _export(
        client,
        target=TYPHOON,
        qty=10,
        src=["office:8000", f"hangar:{MAIN}:60003743"],
    )
    plan = await _plan_row(chain_db, plan_id)
    assert json.loads(plan.sources_json) == [
        "office:8000",
        f"hangar:{MAIN}:60003743",
    ]
    materials = await _materials(chain_db, plan_id)
    # Office 2M + the main's personal 1M.
    assert materials[TRITANIUM].available_qty == 3_000_000

    empty_id = await _export(client, target=TYPHOON, qty=10, src=[""])
    empty_plan = await _plan_row(chain_db, empty_id)
    assert json.loads(empty_plan.sources_json) == []
    empty_materials = await _materials(chain_db, empty_id)
    assert empty_materials[TRITANIUM].available_qty == 0


@respx.mock
async def test_fresh_export_never_touches_sibling_plans(client, chain_db):  # noqa: F811
    """The fork rule: a fresh same-target export leaves the sibling alone
    — concurrent plans stay possible (container bucketing's point)."""
    await _login(client)
    first = await _export(client, target=TYPHOON, qty=10)
    second = await _export(client, target=TYPHOON, qty=10)

    first_row = await _plan_row(chain_db, first)
    second_row = await _plan_row(chain_db, second)
    assert first_row.status == "draft"
    assert first_row.superseded_by_plan_id is None
    assert first_row.abandoned_at is None
    assert second_row.superseded_by_plan_id is None


@respx.mock
async def test_rerun_fork_abandons_the_source_plan(client, chain_db):  # noqa: F811
    """Auto-abandon applies only to the explicit Re-run path: exporting
    with from_plan marks that one plan abandoned and superseded."""
    await _login(client)
    source_id = await _export(client, target=TYPHOON, qty=10)
    forked_id = await _export(
        client, target=TYPHOON, qty=20, from_plan=source_id
    )

    source = await _plan_row(chain_db, source_id)
    forked = await _plan_row(chain_db, forked_id)
    assert source.status == "abandoned"
    assert source.superseded_by_plan_id == forked_id
    assert source.abandoned_at is not None
    # The fork never touches the source's snapshot — name, target, and
    # units stay the original values (the list must never show the new
    # target number on the abandoned plan).
    assert source.name == "Typhoon ×10"
    assert source.units == 10 and source.target_name == "Typhoon"
    assert forked.status == "draft"
    assert forked.superseded_by_plan_id is None
    assert forked.units == 20
    assert forked.name == "Typhoon ×20"

    # Forking an unknown plan id degrades to a fresh export.
    orphan_id = await _export(client, target=TYPHOON, qty=5, from_plan=9999)
    orphan = await _plan_row(chain_db, orphan_id)
    assert orphan.status == "draft"
    assert orphan.superseded_by_plan_id is None


@respx.mock
async def test_export_serializes_facility_overrides(client, chain_db):  # noqa: F811
    """A facility override (non-default registration id) round-trips
    through the form into both the pinned facilities and source_query."""
    from sqlalchemy import text

    await _login(client)
    # A second structure with a manufacturing registration to override
    # with (one registration per structure × activity).
    rig = Structure(
        name="Amamake - Test Raitaru",
        structure_type="raitaru",
        system_id=30002510,
        system_name="Amamake",
        security_class="low",
    )
    chain_db.add(rig)
    await chain_db.flush()
    chain_db.add(
        StructureRegistration(
            structure_id=rig.id, activity="manufacturing",
            me_rig="none", te_rig="none",
        )
    )
    await chain_db.commit()
    registration_id = (
        await chain_db.execute(
            text(
                "SELECT id FROM structure_registrations"
                " WHERE activity = 'manufacturing' AND is_default = 0"
            )
        )
    ).scalar_one()

    plan_id = await _export(
        client, target=TYPHOON, qty=10, manufacturing=registration_id
    )
    plan = await _plan_row(chain_db, plan_id)
    facilities = json.loads(plan.facilities_json)
    assert facilities["manufacturing"]["registration_id"] == registration_id
    assert facilities["manufacturing"]["me_rig"] == "none"
    assert plan.source_query == (
        f"?target=644&qty=10&manufacturing={registration_id}"
    )
