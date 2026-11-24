"""Pure chain-resolver tests (M5): the recursive BOM explosion's
structural rules against hand-built catalogs — no DB, the walk's inputs
are plain dicts. The golden arithmetic pins the per-phase
shared-quantity aggregation semantics from reference/chains/
TYPHOON-CHAIN.md (merged runs beat per-branch rounding), the
recurring-commodity level split from CHARON-CHAIN.md (one node per
(type, phase) occurrence), and the cycle cutting the whole-catalog
census mandates (reference/CENSUS.md). The enrichment orchestrator
suite extends this file below."""

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.esi.assets import OWNER_CHARACTER, OWNER_CORPORATION
from app.industry import ChainMaterial, RecipeHeader
from app.models import (
    Asset,
    Blueprint,
    CostIndex,
    MarketPrice,
    Structure,
    StructureRegistration,
)
from app.planner import (
    ChainAdjustments,
    ChainCatalog,
    chain_plan,
    fresh_node_state,
    phase_state,
    resolve_chain,
)
from tests.test_planner_plan import MAIN, planner_db  # noqa: F401 (fixture)


def header(type_id, bp, activity, per_run, mpl=None, duration=None):
    return RecipeHeader(
        type_id=type_id,
        blueprint_type_id=bp,
        blueprint_name=f"BP {bp}",
        activity_id=activity,
        products_per_run=per_run,
        max_production_limit=mpl,
        duration_seconds=duration,
        copy_duration_seconds=None,
    )


def mat(type_id, qty):
    return ChainMaterial(type_id=type_id, quantity_per_run=qty)


def nodes_by_type(result, type_id):
    return [node for phase in result.phases for node in phase.nodes
            if node.type_id == type_id]


def raw_by_type(result):
    return {row.type_id: row.qty for row in result.raw_totals}


# A four-level chain: target mfg → component mfg → reaction → raws.
CATALOG = ChainCatalog(
    headers={
        100: header(100, 190, 1, 1, mpl=10, duration=18000),
        110: header(110, 191, 1, 3, mpl=600, duration=1200),
        120: header(120, 192, 11, 200, mpl=1000, duration=3600),
    },
    materials={
        100: [mat(110, 2), mat(1, 50)],
        110: [mat(120, 1)],
        120: [mat(2, 5)],
    },
    names={100: "Target", 110: "Component", 120: "Intermediate",
           1: "Raw A", 2: "Raw B"},
)


def test_resolves_ascending_phases():
    """Phases count up in build order: the all-raw level is phase 0, the
    target is phases[-1]; a level's rows mix buildables and terminators
    (the Typhoon's direct minerals shape)."""
    result = resolve_chain(100, 4, CATALOG)
    assert [phase.phase for phase in result.phases] == [0, 1, 2, 3]

    (target,) = result.phases[3].nodes
    assert target.is_target and target.type_id == 100
    assert target.qty == 4 and target.runs == 4
    assert target.jobs == 1  # max production limit 10
    assert target.activity_id == 1 and target.blueprint_type_id == 190

    # The component (8 required at 3/run → 3 runs) beside the direct
    # raw input — terminators can sit above phase 0.
    by_type = {node.type_id: node for node in result.phases[2].nodes}
    assert by_type[110].qty == 8 and by_type[110].runs == 3
    assert by_type[110].activity_id == 1
    assert by_type[1].runs is None and by_type[1].qty == 200

    # The reaction intermediate: 1/run × 3 component runs = 3 required
    # → 1 run at 200/run.
    (intermediate,) = result.phases[1].nodes
    assert intermediate.type_id == 120
    assert intermediate.qty == 3 and intermediate.runs == 1
    assert intermediate.activity_id == 11

    # Phase 0: the reaction's raw input, 5/run × 1 run.
    (raw,) = result.phases[0].nodes
    assert raw.type_id == 2 and raw.qty == 5

    assert raw_by_type(result) == {1: 200, 2: 5}
    assert result.cycles == []


def test_merges_within_phase_rounds_runs_once():
    """The Typhoon chain's aggregation saving: same-type demands from
    several parents merge per phase, then round runs once — RCF's
    per-branch 3+2+3 = 8 runs become 7 aggregated; the 10/run commodity's
    3+2+3 = 8 units become a single run."""
    catalog = ChainCatalog(
        headers={
            100: header(100, 190, 1, 1),
            110: header(110, 191, 1, 1),
            111: header(111, 192, 1, 1),
            112: header(112, 193, 1, 1),
            120: header(120, 194, 1, 200),  # the RCF shape
            130: header(130, 195, 1, 10),  # the OOS shape
        },
        materials={
            100: [mat(110, 3), mat(111, 2), mat(112, 3)],
            110: [mat(120, 167), mat(130, 1)],
            111: [mat(120, 125), mat(130, 1)],
            112: [mat(120, 167), mat(130, 1)],
        },
        names={},
    )
    result = resolve_chain(100, 1, catalog)

    # The three consumers' runs: 3, 2, 3.
    level1 = {node.type_id: node for node in result.phases[1].nodes}
    assert [level1[t].runs for t in (110, 111, 112)] == [3, 2, 3]

    # 200/run commodity: merged demand 167·3 + 125·2 + 167·3 = 1252 →
    # ⌈1252/200⌉ = 7 runs (per-branch rounding would need 3+2+3 = 8).
    (merged,) = nodes_by_type(result, 120)
    assert merged.qty == 1252 and merged.runs == 7

    # 10/run commodity: merged demand 8 → 1 run (per-branch: 3).
    (small,) = nodes_by_type(result, 130)
    assert small.qty == 8 and small.runs == 1


def test_recurring_commodity_splits_phases():
    """The Charon chain's recurring shape: the same type demanded by
    consumers at different depths is one node per (type, phase)
    occurrence — runs round per occurrence (17,500 → 88 runs and 160 → 1
    run), never merged across phases into 89."""
    catalog = ChainCatalog(
        headers={
            100: header(100, 190, 1, 1),
            110: header(110, 191, 1, 1),
            111: header(111, 192, 1, 1),
            112: header(112, 193, 1, 1),
            120: header(120, 194, 11, 200),
        },
        materials={
            100: [mat(110, 1), mat(111, 1)],
            110: [mat(120, 17500)],
            111: [mat(112, 1)],
            112: [mat(120, 160)],
        },
        names={},
    )
    result = resolve_chain(100, 1, catalog)
    occurrences = nodes_by_type(result, 120)
    assert len(occurrences) == 2
    assert {node.phase for node in occurrences} == {0, 1}
    assert sorted(node.runs for node in occurrences) == [1, 88]
    # The recurrence is never a cycle.
    assert result.cycles == []


def test_mixed_activity_level():
    """A level can mix manufacturing and reaction rows — phase ≠
    activity (the Charon chain's phases 2–4)."""
    catalog = ChainCatalog(
        headers={
            100: header(100, 190, 1, 1),
            110: header(110, 191, 1, 1),
            120: header(120, 192, 11, 1),
        },
        materials={
            100: [mat(110, 2), mat(120, 2)],
            110: [mat(1, 5)],
            120: [mat(2, 5)],
        },
        names={},
    )
    result = resolve_chain(100, 1, catalog)
    by_type = {node.type_id: node for node in result.phases[1].nodes}
    assert by_type[110].activity_id == 1
    assert by_type[120].activity_id == 11


def test_self_referential_target_terminates():
    """The census's canonical cycle shape (the Component Assembly Array
    lists 1× itself): the back-edge renders as a flagged terminal row
    one phase below the consumer, is recorded in cycles, and never
    counts as a raw to acquire."""
    catalog = ChainCatalog(
        headers={100: header(100, 190, 1, 1)},
        materials={100: [mat(100, 1), mat(1, 5)]},
        names={100: "Structure Array", 1: "Raw"},
    )
    result = resolve_chain(100, 1, catalog)
    assert [phase.phase for phase in result.phases] == [0, 1]

    (target,) = result.phases[1].nodes
    assert target.is_target and target.runs == 1

    (raw, cut) = sorted(result.phases[0].nodes, key=lambda n: n.type_id)
    assert cut.type_id == 100 and cut.cycle is True and cut.runs is None
    assert cut.qty == 1
    assert raw.type_id == 1 and raw.cycle is False

    # The cut is surfaced with its consumer and phase, and the raw
    # totals exclude the self-reference.
    assert [(c.consumer_type_id, c.material_type_id, c.phase, c.qty)
            for c in result.cycles] == [(100, 100, 0, 1)]
    assert raw_by_type(result) == {1: 5}


def test_self_referential_intermediate_terminates():
    """A self-loop below the target: the intermediate builds normally,
    its self-demand cuts, its other materials still resolve."""
    catalog = ChainCatalog(
        headers={
            100: header(100, 190, 1, 1),
            110: header(110, 191, 1, 1),
        },
        materials={
            100: [mat(110, 1)],
            110: [mat(110, 1), mat(1, 7)],
        },
        names={},
    )
    result = resolve_chain(100, 1, catalog)
    (component,) = [node for node in nodes_by_type(result, 110)
                    if not node.cycle]
    assert component.runs == 1 and component.cycle is False
    (cut,) = [node for node in nodes_by_type(result, 110) if node.cycle]
    assert cut.phase == 0 and cut.qty == 1
    assert [(c.consumer_type_id, c.material_type_id) for c in result.cycles] == [
        (110, 110)
    ]
    assert raw_by_type(result) == {1: 7}


def test_two_node_cycle_cuts_second_demand():
    """A⇄B under an outside target: both expand once, B's demand of A
    cuts (A already expanded a level above), and B's non-cyclic material
    still resolves — the sibling demand is never lost to the cut."""
    catalog = ChainCatalog(
        headers={
            100: header(100, 190, 1, 1),
            110: header(110, 191, 1, 1),
            111: header(111, 192, 1, 1),
            112: header(112, 193, 1, 1),
        },
        materials={
            100: [mat(110, 1)],
            110: [mat(111, 1)],
            111: [mat(110, 1), mat(112, 1)],  # B → A (back-edge) + C
            112: [mat(1, 3)],
        },
        names={},
    )
    result = resolve_chain(100, 1, catalog)
    # The cut row sits one phase below B; C built and consumed its raw.
    (cut,) = [node for node in nodes_by_type(result, 110) if node.cycle]
    assert cut.runs is None and cut.qty == 1
    (c_node,) = nodes_by_type(result, 112)
    assert c_node.runs == 1 and c_node.cycle is False
    assert raw_by_type(result) == {1: 3}
    assert [(c.consumer_type_id, c.material_type_id) for c in result.cycles] == [
        (111, 110)
    ]


def test_adjusted_walk_applies_node_me_and_facility():
    """With ChainAdjustments, a node's material demands carry its own
    blueprint ME and its activity's facility material multiplier (the
    M4 chain: base × runs × (1−ME) × factor, rounded half-up once,
    floored at one unit per run); with no adjustments the walk is the
    unadjusted golden shape the chain documents pin."""
    result = resolve_chain(100, 10, CATALOG)
    (target,) = nodes_by_type(result, 100)
    demands = {d.type_id: d for d in target.demands}
    assert demands[1].required_qty == 500  # 50/run × 10 runs, unadjusted
    assert demands[110].required_qty == 20

    adjusted = resolve_chain(
        100,
        10,
        CATALOG,
        adjustments=ChainAdjustments(
            me_percent={100: 10}, material_factors={"manufacturing": (0.95, 0.0)}
        ),
    )
    (adj_target,) = nodes_by_type(adjusted, 100)
    adj_demands = {d.type_id: d for d in adj_target.demands}
    # 500 × 0.9 × 0.95 = 427.5 → 428; 20 × 0.9 × 0.95 = 17.1 → 17.
    assert adj_demands[1].required_qty == 428
    assert adj_demands[110].required_qty == 17
    # The child's requirement (and so its runs) follows the adjusted
    # demand: 17 at 3/run → 6 runs (unadjusted: 20 → 7).
    (adj_component,) = nodes_by_type(adjusted, 110)
    assert adj_component.qty == 17 and adj_component.runs == 6
    (component,) = nodes_by_type(result, 110)
    assert component.qty == 20 and component.runs == 7


def test_terminator_target_resolves_as_single_raw():
    """A non-catalog target (raw type) resolves to one phase-0 row —
    the orchestrator redirects earlier, but the walk stays total."""
    result = resolve_chain(1, 5, CATALOG)
    assert [phase.phase for phase in result.phases] == [0]
    (node,) = result.phases[0].nodes
    assert node.type_id == 1 and node.is_target
    assert node.runs is None and node.qty == 5
    assert raw_by_type(result) == {1: 5}


def test_units_scale_runs_and_jobs():
    """Run math recomputes per target count (⌈units ÷ per-run⌉), with
    over-delivery at small counts and job splits at the max production
    limit."""
    one = resolve_chain(100, 1, CATALOG)
    (target,) = nodes_by_type(one, 100)
    assert target.runs == 1  # 1 unit at 1/run — over-delivery is none
    five = resolve_chain(100, 5, CATALOG)
    (target5,) = nodes_by_type(five, 100)
    assert target5.qty == 5 and target5.runs == 5 and target5.jobs == 1

    tight = ChainCatalog(
        headers={100: header(100, 190, 1, 2, mpl=2)},
        materials={100: [mat(1, 1)]},
        names={},
    )
    result = resolve_chain(100, 5, tight)
    (node,) = nodes_by_type(result, 100)
    assert node.runs == 3  # ⌈5/2⌉ — one run over-delivers
    assert node.jobs == 2  # max 2 runs per job


# --- Orchestrator (chain_plan over the planner fixture) ------------------------
#
# The miniature golden chain, layered on planner_db's Typhoon slice:
#
#     Typhoon (mfg, BPO ME 10/TE 20)
#       → Tritanium (raw) + Capital Power Generator (mfg, BPC-only 5+6 runs)
#           → Tungsten Carbide (reaction via the published formula 46207,
#             gated on a level-5 skill nobody holds)
#               → Tritanium (raw) + Test Fuel Block (mfg, BPO owned)
#                   → Tritanium (raw) + Test Ice Product (raw)
#
# plus a self-referential structure array (the census's canonical cycle
# shape) and pool stock: ice and fuel blocks in the corp office,
# Tritanium partial in the main's hangar.

TYPHOON = 644
CPG = 20410
CARBIDE = 16672
FUEL = 4100
ICE = 4102
TRITANIUM = 34


@pytest_asyncio.fixture
async def chain_db(planner_db):  # noqa: F811 (layered fixture: the module-level import exposes it, this parameter consumes it)
    rows = {
        "sde_invTypes": [
            (4100, "Test Fuel Block", 5.0, 5.0, 104, 1),
            (4101, "Test Fuel Block Blueprint", 0.01, 0.01, 176, 1),
            (4102, "Test Ice Product", 0.01, 0.01, 19, 1),
            (4200, "Test Assembly Array", 1000.0, 1000.0, 4, 1),
            (4201, "Test Assembly Array Blueprint", 0.01, 0.01, 176, 1),
        ],
        "sde_invGroups": [(104, "Fuel Block", 4), (19, "Ice Product", 4)],
        "sde_industryBlueprints": [(4101, 40), (4201, 10)],
        "sde_industryActivity": [
            (20411, 1, 3000),
            (20411, 5, 2400),
            (46207, 11, 1800),
            (4101, 1, 1200),
            (4201, 1, 600),
        ],
        "sde_industryActivityMaterials": [
            (20411, 1, 16672, 100),
            (46207, 11, 34, 5000),
            (46207, 11, 4100, 2),
            (4101, 1, 34, 1500),
            (4101, 1, 4102, 10),
            (4201, 1, 4200, 1),
            (4201, 1, 34, 100),
        ],
        "sde_industryActivityProducts": [
            (4101, 1, 4100, 40),
            (4201, 1, 4200, 1),
        ],
        "sde_industryActivitySkills": [
            (20411, 1, 3380, 1),
            (4101, 1, 3380, 1),
            # Nobody in the pool holds level 5 — the reaction gate fails.
            (46207, 11, 22242, 5),
        ],
    }
    for table, table_rows in rows.items():
        columns = range(len(table_rows[0]))
        marks = ", ".join(f":c{i}" for i in columns)
        await planner_db.execute(
            text(f"INSERT INTO {table} VALUES ({marks})"),
            [{f"c{i}": value for i, value in enumerate(row)} for row in table_rows],
        )

    # The reaction facility: a Tatara in the same system, its index synced.
    tatara = Structure(
        name="Amamake - Test Tatara",
        structure_type="tatara",
        system_id=30002510,
        system_name="Amamake",
        security_class="low",
    )
    planner_db.add(tatara)
    await planner_db.flush()
    planner_db.add(
        StructureRegistration(
            structure_id=tatara.id,
            activity="reactions",
            me_rig="none",
            te_rig="none",
            tax_rate=0.01,
            is_default=True,
        )
    )
    planner_db.add(
        CostIndex(system_id=30002510, activity="reaction", cost_index=0.007)
    )

    # BPC-only CPG pool (5 + 6 runs, ME/TE 0); owned originals for the
    # fuel block and the reaction formula.
    planner_db.add_all(
        [
            Blueprint(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=3001,
                type_id=20411, location_id=60003743, location_flag="CorpSAG2",
                quantity=1, runs=5, material_efficiency=0, time_efficiency=0,
            ),
            Blueprint(
                owner_type=OWNER_CHARACTER, owner_id=MAIN, item_id=3002,
                type_id=20411, location_id=60003743, location_flag="Hangar",
                quantity=1, runs=6, material_efficiency=0, time_efficiency=0,
            ),
            Blueprint(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=3003,
                type_id=4101, location_id=60003743, location_flag="CorpSAG2",
                quantity=1, runs=-1, material_efficiency=0, time_efficiency=0,
            ),
            Blueprint(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=3004,
                type_id=46207, location_id=60003743, location_flag="CorpSAG2",
                quantity=1, runs=-1, material_efficiency=0, time_efficiency=0,
            ),
        ]
    )

    planner_db.add_all(
        [
            MarketPrice(type_id=16672, adjusted_price=20.0, average_price=19.0),
            MarketPrice(type_id=4100, adjusted_price=2.0, average_price=1.9),
            MarketPrice(type_id=4102, adjusted_price=0.5, average_price=0.4),
        ]
    )

    # Pool stock: the corp office holds the ice (exactly covered), fuel
    # blocks (over-stocked), and partial Tritanium; the main's personal
    # Tritanium stays OUT of the default measurement (participants may
    # be job-allocation positions, not material sources — the owner's
    # corp-hangars-only call).
    planner_db.add_all(
        [
            Asset(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=9100,
                type_id=27, quantity=1, location_id=8000,
                location_flag="OfficeFolder", location_type="item",
                parent_location_id=8000, is_blueprint_copy=False,
                is_singleton=True,
            ),
            Asset(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=9101,
                type_id=4102, quantity=10, location_id=8000,
                location_flag="CorpSAG1", location_type="item",
                parent_location_id=8000, is_blueprint_copy=False,
                is_singleton=False,
            ),
            Asset(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=9102,
                type_id=4100, quantity=40, location_id=8000,
                location_flag="CorpSAG1", location_type="item",
                parent_location_id=8000, is_blueprint_copy=False,
                is_singleton=False,
            ),
            Asset(
                owner_type=OWNER_CORPORATION, owner_id=98000001, item_id=9104,
                type_id=34, quantity=2_000_000, location_id=8000,
                location_flag="CorpSAG1", location_type="item",
                parent_location_id=8000, is_blueprint_copy=False,
                is_singleton=False,
            ),
            Asset(
                owner_type=OWNER_CHARACTER, owner_id=MAIN, item_id=9103,
                type_id=34, quantity=1_000_000, location_id=60003743,
                location_flag="Hangar", location_type="station",
                parent_location_id=60003743, is_blueprint_copy=False,
                is_singleton=False,
            ),
        ]
    )
    await planner_db.commit()
    return planner_db


async def _facilities(db):
    from app.facilities import registration_rows

    return {row.activity: row for row in await registration_rows(db)}


def _node(result, type_id, phase=None):
    matches = [node for phase_ in result.phases for node in phase_.nodes
               if node.type_id == type_id
               and (phase is None or node.phase == phase)]
    assert matches, f"no node for {type_id} at phase {phase}"
    return matches[0]


async def test_chain_plan_resolves_miniature_chain(chain_db):
    """The walk over the miniature chain at ×10, with the M4 goldens
    carrying over to the target node and per-node adjusted demands
    hand-checked down the phases."""
    plan = await chain_plan(
        chain_db, target_type_id=TYPHOON, units=10,
        facilities=await _facilities(chain_db),
    )
    assert plan is not None
    chain = plan.chain
    assert [phase.phase for phase in chain.phases] == [0, 1, 2, 3, 4]
    assert chain.cycles == []

    target = chain.target_node
    assert target.phase == 4 and target.runs == 10 and target.jobs == 1
    assert target.calc.me == 10 and target.calc.te == 20  # the corp BPO
    assert target.calc.has_original and target.calc.bpc_pool_runs is None
    demands = {m.type_id: m for m in target.calc.materials}
    # The M4 goldens: direct Tritanium and the CPG requirement.
    assert demands[TRITANIUM].required_qty == 68_571_360
    assert demands[CPG].required_qty == 471

    # Phase 3: the CPG at 471 required → 157 runs; its own demand for
    # the carbide is 100/run × 157 × Azbel factors (0.99 × 0.962) = 14,952.
    cpg = _node(chain, CPG, phase=3)
    assert cpg.runs == 157
    carbide_demand = {m.type_id: m for m in cpg.calc.materials}[CARBIDE]
    assert carbide_demand.required_qty == 14_952
    assert carbide_demand.base_qty == 100

    # Phase 2: the carbide reaction — 14,952 at 10,000/run → 2 runs; its
    # demands sit at the reaction facility (no material bonus, no rig).
    carbide = _node(chain, CARBIDE, phase=2)
    assert carbide.runs == 2
    reaction_demands = {m.type_id: m for m in carbide.calc.materials}
    assert reaction_demands[TRITANIUM].required_qty == 10_000
    assert reaction_demands[FUEL].required_qty == 4

    # Phase 1: the fuel block — 4 required at 40/run → 1 over-delivering
    # run; demands back at the Azbel: 1,500 × 0.99 × 0.962 = 1,429 and
    # 10 × 0.99 × 0.962 = 9.52 → 10.
    fuel = _node(chain, FUEL, phase=1)
    assert fuel.runs == 1 and fuel.jobs == 1
    fuel_demands = {m.type_id: m for m in fuel.calc.materials}
    assert fuel_demands[TRITANIUM].required_qty == 1_429
    assert fuel_demands[ICE].required_qty == 10

    # Terminators summed across every phase.
    totals = {row.type_id: row.qty for row in chain.raw_totals}
    assert totals[TRITANIUM] == 68_571_360 + 10_000 + 1_429
    assert totals[ICE] == 10


async def test_chain_plan_enriches_selection_gates_and_install(chain_db):
    """Per-node enrichment: BPC-only selection with run-coverage
    shortfall, the skill gate nobody holds, per-node install cost at
    each node's own facility, and time at the best gate-holder."""
    plan = await chain_plan(
        chain_db, target_type_id=TYPHOON, units=10,
        facilities=await _facilities(chain_db),
    )
    chain = plan.chain

    # CPG: BPC-only — the best copy drives the calc, coverage short.
    cpg = _node(chain, CPG, phase=3)
    assert cpg.calc.selected is not None and not cpg.calc.selected.is_original
    assert cpg.calc.bpc_pool_runs == 11  # 5 + 6 against a 157-run need
    # Time: 3,000 s/run × 157 runs × Azbel 0.80 × rig 0.62 × 0.68.
    assert cpg.calc.job_seconds == 158_859
    assert cpg.calc.total_seconds == 158_859  # one job (max 600 runs)

    # The carbide reaction: an original is owned, but the level-5 gate
    # fails for everybody → unskilled time at the Tatara's ×0.75.
    carbide = _node(chain, CARBIDE, phase=2)
    assert carbide.calc.has_original
    assert not carbide.calc.holds_gate
    assert carbide.calc.job_seconds == 2_700  # 1,800 × 2 runs × 0.75
    assert carbide.calc.install.total == pytest.approx(190.94656, rel=1e-9)

    # The fuel block: owned original, gate held, time at 0.68.
    fuel = _node(chain, FUEL, phase=1)
    assert fuel.calc.has_original and fuel.calc.holds_gate
    assert fuel.calc.job_seconds == 405  # 1,200 × 0.8 × 0.62 × 0.68
    assert fuel.calc.install.total == pytest.approx(17.9964144, rel=1e-9)

    # The target's install is M4's golden; the CPG node's bills the
    # un-adjusted carbide base (100 × 157) at the Azbel.
    target = chain.target_node
    assert target.calc.install.total == pytest.approx(958_869.3744, rel=1e-9)
    cpg_install = _node(chain, CPG, phase=3).calc.install.total
    assert cpg_install == pytest.approx(1_393.55712, rel=1e-9)

    # Chain totals roll up from the nodes.
    assert chain.total_runs == 10 + 157 + 2 + 1
    assert chain.total_jobs == 4
    assert chain.total_seconds == 48_568 + 158_859 + 2_700 + 405
    assert chain.install_total == pytest.approx(
        958_869.3744 + 1_393.55712 + 190.94656 + 17.9964144, rel=1e-9
    )
    assert chain.install_missing_nodes == 0


async def test_chain_plan_stage_states_and_coverage(chain_db):
    """The fresh-plan stage states (computed from ownership, skills,
    dependencies, and stock) and the pool-stock coverage of nodes and
    terminators."""
    plan = await chain_plan(
        chain_db, target_type_id=TYPHOON, units=10,
        facilities=await _facilities(chain_db),
    )
    chain = plan.chain

    # The target waits on its buildable input (the CPG, one phase below).
    assert fresh_node_state(chain.target_node) == ("missing", "waiting-upstream")
    # The CPG waits on the carbide; its BPC selection passes the
    # blueprint check and its gate is held.
    cpg = _node(chain, CPG, phase=3)
    assert fresh_node_state(cpg) == ("missing", "waiting-upstream")
    # The carbide: blueprint owned, gate unheld — skill-gated, not
    # blueprint-gated (the distinct marking of record).
    assert fresh_node_state(_node(chain, CARBIDE, phase=2)) == (
        "missing", "skill-gated")
    # The fuel block: owned, gated, raw inputs stock-covered → ready.
    assert fresh_node_state(_node(chain, FUEL, phase=1)) == ("ready", None)

    # Phase summaries roll up worst-child.
    states = {phase.phase: phase_state(phase) for phase in chain.phases}
    assert states[4] == "missing" and states[3] == "missing"
    assert states[2] == "missing" and states[1] == "ready"

    # Coverage: node-level (the fuel node's own stock vs its need) and
    # terminator-level (ice exactly covered, Tritanium partial — the
    # office stock only; the main's personal 1M stays out of the
    # default measurement).
    fuel = _node(chain, FUEL, phase=1)
    assert fuel.calc.on_hand == 40 and fuel.calc.coverage == pytest.approx(10.0)
    by_type = {row.type_id: row for row in chain.raw_totals}
    assert by_type[ICE].on_hand == 10  # exactly covered
    assert by_type[TRITANIUM].on_hand == 2_000_000  # office stock only


async def test_chain_plan_personal_stock_is_opt_in(chain_db):
    """The coverage measurement defaults to the corp office hangars;
    `include_personal_stock` widens it to the participants' own
    hangars (the false-positive guard for out-of-corp participants)."""
    facilities = await _facilities(chain_db)
    plan = await chain_plan(
        chain_db, target_type_id=TYPHOON, units=10, facilities=facilities,
        include_personal_stock=True,
    )
    by_type = {row.type_id: row for row in plan.chain.raw_totals}
    # The office's 2M plus the main's personal 1M.
    assert by_type[TRITANIUM].on_hand == 3_000_000


async def test_chain_plan_participants_and_copy_time(chain_db):
    """The chain-level participant readouts and the target's copy time.
    The copy multiplier is the COPYING skill map (Advanced Industry
    only — 0.85 at level 5), correcting M4's depth-1 readout which
    applied the manufacturing multiplier (0.68) against its own
    docstring."""
    plan = await chain_plan(
        chain_db, target_type_id=TYPHOON, units=10,
        facilities=await _facilities(chain_db),
    )
    by_name = {row.name: row for row in plan.participants}
    assert set(by_name) == {"Test Pilot", "Corp Mate"}  # default pool

    main = by_name["Test Pilot"]
    assert main.multipliers["manufacturing"] == pytest.approx(0.68)
    assert main.multipliers["reactions"] == pytest.approx(1.0)
    # Gated onto the Typhoon, the CPG, and the fuel block — not the
    # level-5 reaction gate.
    assert main.nodes_gated == 3
    assert main.gated_total_seconds == 48_568 + 158_859 + 405
    assert main.holds_target_gate  # the fixture's level-3 stand-in

    mate = by_name["Corp Mate"]
    assert mate.nodes_gated == 2  # the Typhoon gate excludes them
    assert not mate.holds_target_gate
    assert mate.missing_target_skills == ["Advanced Industry"]

    # Copy time: 4 h/run at a station with the best copying multiplier.
    assert plan.copy_seconds_per_run == 12_240  # 14,400 × 0.85
    assert plan.copy_total_seconds == 122_400


async def test_chain_plan_none_outside_catalog(chain_db):
    assert await chain_plan(chain_db, target_type_id=TRITANIUM, units=1) is None


async def test_chain_plan_surfaces_self_reference_cycle(chain_db):
    """A structure-array target: the walk terminates, the back-edge is
    flagged and recorded, and the array's real input still resolves."""
    plan = await chain_plan(
        chain_db, target_type_id=4200, units=1,
        facilities=await _facilities(chain_db),
    )
    assert plan is not None
    chain = plan.chain
    (target,) = [node for node in chain.buildable_nodes if node.is_target]
    assert target.calc is not None  # enrichment survived the cycle
    (cut,) = [node for node in chain.phases[0].nodes if node.cycle]
    assert cut.type_id == 4200 and cut.runs is None
    assert [(c.consumer_type_id, c.material_type_id) for c in chain.cycles] == [
        (4200, 4200)
    ]
    # The self-reference never counts as a raw to acquire; the array's
    # real input lands adjusted (100 × Azbel 0.99 × 0.962 = 95).
    totals = {row.type_id: row.qty for row in chain.raw_totals}
    assert totals == {TRITANIUM: 95}
