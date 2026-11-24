"""Planner orchestrator tests (M4→M5): chain_plan over the catalog
fixture extended with a registered facility, synced skills, and the
world-data tables — the M4 depth-1 goldens carried onto the target node
of the resolved chain — plus the planner read helpers and the
facility-default resolution."""

from datetime import timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.db import utc_now
from app.esi.assets import OWNER_CHARACTER, OWNER_CORPORATION
from app.facilities import activity_registrations, default_facilities
from app.industry import (
    active_skill_levels,
    adjusted_prices,
    cost_index,
    material_categories,
)
from app.models import (
    Blueprint,
    Character,
    CostIndex,
    MarketPrice,
    Skill,
    Structure,
    StructureRegistration,
)
from app.planner import chain_plan
from tests.test_catalog import SDE_DDL, SDE_ROWS

# The fixture's Advanced Industry stand-in (the real skill id is 3388 —
# see app/planner.py; the SDE slice's fictional 22242 only feeds the
# required-skills read).
INDUSTRY = 3380
ADVANCED_INDUSTRY = 3388

MAIN = 1234
CORP_MEMBER = 5678
OUT_OF_CORP = 9999


@pytest_asyncio.fixture
async def planner_db(db_session):
    """The catalog slice plus the M4 planner's read surfaces: a
    registered Azbel (T1 rigs, lowsec, taxed), a main character with
    corp-mates and an out-of-corp character, synced skill sheets, and
    the world-data snapshots (cost index + market prices)."""
    for ddl in SDE_DDL:
        await db_session.execute(text(ddl))
    for table, rows in SDE_ROWS.items():
        columns = range(len(rows[0]))
        marks = ", ".join(f":c{i}" for i in columns)
        await db_session.execute(
            text(f"INSERT INTO {table} VALUES ({marks})"),
            [{f"c{i}": value for i, value in enumerate(row)} for row in rows],
        )
    # Copy duration for the Typhoon Blueprint (activity 5).
    await db_session.execute(
        text("INSERT INTO sde_industryActivity VALUES (998, 5, 14400)")
    )

    tokens = dict(
        owner_hash="owner-1",
        scopes="publicData",
        access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R",
    )
    db_session.add_all(
        [
            Character(
                character_id=MAIN,
                name="Test Pilot",
                corporation_id=98000001,
                is_main=True,
                **tokens,
            ),
            Character(
                character_id=CORP_MEMBER,
                name="Corp Mate",
                corporation_id=98000001,
                **tokens,
            ),
            Character(
                character_id=OUT_OF_CORP,
                name="Outsider",
                corporation_id=99000002,
                **tokens,
            ),
        ]
    )

    # Skill sheets: the main holds Industry 5 + Advanced Industry 5
    # (multiplier 0.68) plus the fixture's level-3 required stand-in;
    # the corp-mate holds Industry 5 only (fails the level-3 required
    # skill); the outsider holds AI 1.
    def sheet(owner_id, levels):
        return [
            Skill(
                owner_type=OWNER_CHARACTER,
                owner_id=owner_id,
                skill_id=skill_id,
                trained_skill_level=level,
                active_skill_level=level,
                skillpoints_in_skill=1000 * level,
            )
            for skill_id, level in levels.items()
        ]

    db_session.add_all(sheet(MAIN, {INDUSTRY: 5, ADVANCED_INDUSTRY: 5, 22242: 3}))
    db_session.add_all(sheet(CORP_MEMBER, {INDUSTRY: 5}))
    db_session.add_all(sheet(OUT_OF_CORP, {ADVANCED_INDUSTRY: 1}))

    azbel = Structure(
        name="Amamake - Test Azbel",
        structure_type="azbel",
        system_id=30002510,
        system_name="Amamake",
        security_class="low",
    )
    db_session.add(azbel)
    await db_session.flush()
    db_session.add(
        StructureRegistration(
            structure_id=azbel.id,
            activity="manufacturing",
            me_rig="t1",
            te_rig="t1",
            tax_rate=0.005,
            is_default=True,
        )
    )

    # The Typhoon BPO (ME 10 / TE 20) in the corp pool.
    db_session.add(
        Blueprint(
            owner_type=OWNER_CORPORATION,
            owner_id=98000001,
            item_id=1001,
            type_id=998,
            location_id=60003743,
            location_flag="CorpSAG2",
            quantity=1,
            runs=-1,
            material_efficiency=10,
            time_efficiency=20,
        )
    )

    # World data: Amamake's manufacturing index and the input prices.
    db_session.add(
        CostIndex(system_id=30002510, activity="manufacturing", cost_index=0.0046)
    )
    db_session.add(MarketPrice(type_id=34, adjusted_price=2.7, average_price=2.6))
    db_session.add(
        MarketPrice(type_id=20410, adjusted_price=100.0, average_price=99.0)
    )

    await db_session.commit()
    return db_session


async def _facility(db) -> StructureRegistration:
    """The seeded manufacturing registration as the planner sees it (a
    RegistrationRow with the structure facts denormalized)."""
    from app.facilities import registration_rows

    rows = [row for row in await registration_rows(db) if row.activity == "manufacturing"]
    assert rows, "manufacturing registration not seeded"
    return rows[0]


async def test_chain_plan_calculates_typhoon(planner_db):
    """The resolved chain for Typhoon ×10 at the registered Azbel: the
    M4 depth-1 goldens on the target node — runs/jobs, ME-adjusted
    materials with the rig/hull chain, the input node's runs, install
    cost, time at the best participant's skills, and copy time. (The
    fixture's CPG slice carries no materials, so the chain bottoms out
    one level down.)"""
    facility = await _facility(planner_db)
    plan = await chain_plan(
        planner_db,
        target_type_id=644,
        units=10,
        facilities={"manufacturing": facility},
    )
    assert plan is not None
    chain = plan.chain
    target = chain.target_node
    assert target.runs == 10 and target.jobs == 1  # max production limit 10
    assert target.calc.me == 10 and target.calc.te == 20  # the corp BPO
    assert target.calc.has_original and target.calc.bpc_pool_runs is None

    # Materials: Tritanium (raw) and Capital Power Generator
    # (buildable), quantities per the engine suite's golden chains.
    by_name = {material.name: material for material in target.calc.materials}
    assert by_name["Tritanium"].required_qty == 68_571_360
    assert by_name["Tritanium"].buildable is False
    assert by_name["Capital Power Generator"].required_qty == 471
    assert by_name["Capital Power Generator"].buildable is True

    # The input node one phase below: 471 required at 3/run → 157 runs.
    (cpg,) = [node for node in chain.buildable_nodes if node.type_id == 20410]
    assert cpg.runs == 157
    assert cpg.blueprint_type_id == 20411
    assert cpg.calc.selected is None  # no CPG blueprint seeded
    assert cpg.calc.bpc_pool_runs == 0

    # Install cost bills the un-adjusted quantities (the engine's
    # golden chain: 958,869.3744 Ƶ); the empty-material CPG node bills
    # zero, not missing data.
    assert target.calc.install.total == pytest.approx(958_869.3744, rel=1e-9)
    assert cpg.calc.install.total == 0.0
    assert chain.install_total == pytest.approx(958_869.3744, rel=1e-9)
    assert chain.install_missing_nodes == 0

    # Time: the default pool's best multiplier is the main's 0.68 →
    # 48,568 s for the single 10-run job (the CPG slice has no duration
    # row, so it contributes nothing).
    assert target.calc.job_seconds == 48_568
    assert chain.total_seconds == 48_568

    # Copy time: 4 h/run at a station with the best COPYING multiplier
    # (Advanced Industry only — 0.85 at level 5; the M4 depth-1 readout
    # applied the manufacturing multiplier against its own docstring).
    assert plan.copy_seconds_per_run == 12_240
    assert plan.copy_total_seconds == 122_400


async def test_chain_plan_default_pool_is_corp_members(planner_db):
    """Participants=None resolves the main's corporation's members —
    the outsider stays out (the participants decision of record)."""
    facility = await _facility(planner_db)
    plan = await chain_plan(
        planner_db, target_type_id=644, units=10, facilities={"manufacturing": facility}
    )
    names = {row.name for row in plan.participants}
    assert names == {"Test Pilot", "Corp Mate"}

    by_name = {row.name: row for row in plan.participants}
    # The main: Industry 5 + AI 5 → 0.68, gate held.
    assert by_name["Test Pilot"].multipliers["manufacturing"] == pytest.approx(0.68)
    assert by_name["Test Pilot"].holds_target_gate
    # The corp-mate: Industry 5 only → 0.80, and fails the level-3
    # required skill the fixture carries.
    assert by_name["Corp Mate"].multipliers["manufacturing"] == pytest.approx(0.80)
    assert not by_name["Corp Mate"].holds_target_gate
    assert by_name["Corp Mate"].missing_target_skills == ["Advanced Industry"]


async def test_chain_plan_explicit_participants(planner_db):
    """An explicit participant list replaces the default pool, and the
    target's time uses the best gate-holding multiplier among them."""
    facility = await _facility(planner_db)
    plan = await chain_plan(
        planner_db,
        target_type_id=644,
        units=10,
        participants=[CORP_MEMBER, OUT_OF_CORP],
        facilities={"manufacturing": facility},
    )
    assert {row.name for row in plan.participants} == {"Corp Mate", "Outsider"}
    # Corp Mate 0.80 (gate held? no — missing Advanced Industry);
    # Outsider AI 1 → 0.97, but the fixture's required skills (Industry
    # 1) are unmet too. Neither holds the gate, so the target's time
    # falls back to the unskilled 1.0 baseline.
    by_name = {row.name: row for row in plan.participants}
    assert by_name["Corp Mate"].multipliers["manufacturing"] == pytest.approx(0.80)
    assert by_name["Outsider"].multipliers["manufacturing"] == pytest.approx(0.97)
    assert not any(row.holds_target_gate for row in plan.participants)
    # Unskilled: 180,000 × 0.8 (TE) × 0.8 (hull) × 0.62 (rig) = 71,424.
    assert plan.chain.target_node.calc.job_seconds == 71_424


async def test_chain_plan_unowned_target_defaults_me_te_zero(planner_db):
    """A target whose blueprint nobody owns calculates at ME/TE 0 with
    no selection and no run coverage."""
    await planner_db.execute(text("DELETE FROM blueprints"))
    await planner_db.commit()
    facility = await _facility(planner_db)
    plan = await chain_plan(
        planner_db, target_type_id=644, units=10, facilities={"manufacturing": facility}
    )
    target = plan.chain.target_node
    assert target.calc.selected is None
    assert target.calc.me == 0 and target.calc.te == 0
    assert target.calc.has_original is False and target.calc.bpc_pool_runs == 0
    # No ME: Tritanium 8M × 10 × 0.99 × 0.962 = 76,190,400.
    by_name = {material.name: material for material in target.calc.materials}
    assert by_name["Tritanium"].required_qty == 76_190_400


async def test_chain_plan_bpc_only_selection_and_coverage(planner_db):
    """BPC-only pool: the best-ME copy drives the calculation and the
    run-coverage shortfall surfaces (Σ BPC runs vs required)."""
    await planner_db.execute(text("DELETE FROM blueprints"))
    planner_db.add_all(
        [
            Blueprint(
                owner_type=OWNER_CORPORATION,
                owner_id=98000001,
                item_id=2001,
                type_id=998,
                location_id=60003743,
                location_flag="CorpSAG2",
                quantity=1,
                runs=9,
                material_efficiency=10,
                time_efficiency=18,
            ),
            Blueprint(
                owner_type=OWNER_CHARACTER,
                owner_id=MAIN,
                item_id=2002,
                type_id=998,
                location_id=60003743,
                location_flag="Hangar",
                quantity=1,
                runs=8,
                material_efficiency=10,
                time_efficiency=18,
            ),
        ]
    )
    await planner_db.commit()
    facility = await _facility(planner_db)
    plan = await chain_plan(
        planner_db, target_type_id=644, units=10, facilities={"manufacturing": facility}
    )
    target = plan.chain.target_node
    assert target.calc.selected is not None
    assert target.calc.selected.is_original is False
    assert target.calc.me == 10 and target.calc.te == 18
    assert target.calc.has_original is False
    assert target.calc.bpc_pool_runs == 17  # 9 + 8 — short of the 10-run need


async def test_chain_plan_none_outside_catalog(planner_db):
    facility = await _facility(planner_db)
    assert (
        await chain_plan(
            planner_db, target_type_id=34, units=1, facilities={"manufacturing": facility}
        )
        is None
    )


async def test_chain_plan_no_facility_degrades(planner_db):
    """No registration: station baselines (no hull, no rig, no tax) and
    the install cost still reads the (systemless) index as missing."""
    plan = await chain_plan(planner_db, target_type_id=644, units=10, facilities={})
    assert plan is not None
    target = plan.chain.target_node
    assert target.calc.install.total is None  # no system → no index
    # Station + no rig: 8M × 10 × 0.9 = 72,000,000.
    by_name = {material.name: material for material in target.calc.materials}
    assert by_name["Tritanium"].required_qty == 72_000_000


# --- Read helpers -------------------------------------------------------------


async def test_active_skill_levels_keyed_by_character(planner_db):
    levels = await active_skill_levels(planner_db, [MAIN, CORP_MEMBER, OUT_OF_CORP])
    assert levels[MAIN] == {INDUSTRY: 5, ADVANCED_INDUSTRY: 5, 22242: 3}
    assert levels[CORP_MEMBER] == {INDUSTRY: 5}
    assert levels[OUT_OF_CORP] == {ADVANCED_INDUSTRY: 1}


async def test_adjusted_prices_missing_types_key_none(planner_db):
    prices = await adjusted_prices(planner_db, [34, 20410, 644])
    assert prices[34] == pytest.approx(2.7)
    assert prices[20410] == pytest.approx(100.0)
    assert prices[644] is None  # no synced row


async def test_cost_index_maps_activity_keys(planner_db):
    assert await cost_index(planner_db, 30002510, "manufacturing") == pytest.approx(
        0.0046
    )
    # ESI stores "reaction" for the registry's "reactions" key; no row
    # was seeded for it here.
    assert await cost_index(planner_db, 30002510, "reactions") is None
    assert await cost_index(planner_db, None, "manufacturing") is None
    assert await cost_index(planner_db, 42, "manufacturing") is None


async def test_material_categories_from_sde_groups(planner_db):
    categories = await material_categories(planner_db, [34, 644, 20410])
    assert categories[34] == ("Material", "Mineral")
    assert categories[644] == ("Ship", "Battleship")
    assert categories[20410] == ("Ship", "Capital Component")


# --- Facility defaults ----------------------------------------------------------


async def test_default_facilities_and_copying_fallback(planner_db):
    """Defaults resolve per activity (is_default, else lowest id, else
    None); copying falls back to the invention default — here there is
    none, so everything but manufacturing reads None."""
    defaults = await default_facilities(planner_db)
    assert defaults["manufacturing"] is not None
    assert defaults["manufacturing"].structure_name == "Amamake - Test Azbel"
    assert defaults["copying"] is None
    assert defaults["invention"] is None
    assert defaults["reactions"] is None

    # An invention registration becomes the copying default.
    azbel_id = defaults["manufacturing"].structure_id
    planner_db.add(
        StructureRegistration(
            structure_id=azbel_id, activity="invention", me_rig="none", te_rig="t1"
        )
    )
    await planner_db.commit()
    defaults = await default_facilities(planner_db)
    assert defaults["invention"] is not None
    assert defaults["copying"] is not None
    assert defaults["copying"].registration_id == defaults["invention"].registration_id

    # A dedicated copying registration wins over the fallback.
    planner_db.add(
        StructureRegistration(
            structure_id=azbel_id, activity="copying", me_rig="none", te_rig="none"
        )
    )
    await planner_db.commit()
    defaults = await default_facilities(planner_db)
    assert defaults["copying"].activity == "copying"


async def test_activity_registrations_lists_one_activity(planner_db):
    rows = await activity_registrations(planner_db, "manufacturing")
    assert [row.structure_name for row in rows] == ["Amamake - Test Azbel"]
    assert rows[0].me_rig == "t1" and rows[0].security_class == "low"
