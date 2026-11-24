"""Pure planner-engine tests (M4): run/job math, the material and time
multiplier chains, install cost, copy time, skill multipliers, and
blueprint selection — hermetic, no DB. Golden values hand-computed
against the pinned multiplier tables (app/facilities.py, live ESI
dogma 2026-11-23) and the reference model's max-skills scenario
(Industry 5 + Advanced Industry 5 = 0.68 — a scenario, not a constant)."""

import pytest

from app.facilities import RegistrationRow
from app.industry import BlueprintRow
from app.planner import (
    adjusted_material_quantity,
    bpc_pool_runs,
    copy_time_seconds,
    install_cost,
    job_count,
    job_time_seconds,
    rig_percent,
    round_half_up,
    runs_for_units,
    select_blueprint,
    skill_time_multiplier,
)

# Industry 3380 / Advanced Industry 3388 (the dogma-pinned skill ids).
INDUSTRY = 3380
ADVANCED_INDUSTRY = 3388


def _registration(
    *,
    activity="manufacturing",
    structure_type="azbel",
    security_class="low",
    me_rig="none",
    te_rig="none",
    registration_id=1,
) -> RegistrationRow:
    return RegistrationRow(
        registration_id=registration_id,
        structure_id=1,
        activity=activity,
        structure_name="Test Facility",
        structure_type=structure_type,
        system_id=30002510,
        system_name="Test System",
        security_class=security_class,
        me_rig=me_rig,
        te_rig=te_rig,
        tax_rate=0.005,
        is_default=True,
        supercapital_assembly=False,
    )


def _blueprint(
    item_id,
    *,
    me=0,
    te=0,
    runs=-1,
) -> BlueprintRow:
    return BlueprintRow(
        item_id=item_id,
        type_id=998,
        type_name="Typhoon Blueprint",
        icon_kind="bp" if runs == -1 else "bpc",
        material_efficiency=me,
        time_efficiency=te,
        runs=runs,
        location_name="Somewhere",
        location_flag="CorpSAG2",
        owner_name="Someone",
    )


# --- Run and job math -------------------------------------------------------


def test_runs_for_units_products_per_run():
    assert runs_for_units(10, 1) == 10  # ships: 1/run
    assert runs_for_units(750, 3) == 250  # components: 3/run
    assert runs_for_units(1000, 40) == 25  # fuel blocks: 40/run
    assert runs_for_units(1, 3) == 1
    assert runs_for_units(7, 3) == 3  # ceil, not round


def test_job_count_bounded_by_max_production_limit():
    assert job_count(10, 10) == 1
    assert job_count(11, 10) == 2  # the remainder is its own job
    assert job_count(500, 200) == 3
    assert job_count(25, None) == 1  # no limit row: a single job
    assert job_count(0, 10) == 0


def test_round_half_up_at_chain_end():
    assert round_half_up(2.5) == 3
    assert round_half_up(2.4999) == 2
    assert round_half_up(47.5) == 48
    assert round_half_up(0.4) == 0


# --- Skill multipliers (dogma-pinned) ----------------------------------------


def test_skill_multiplier_manufacturing_stacks_multiplicatively():
    # Industry 5 (−20%) × Advanced Industry 5 (−15%) = 0.68 — the
    # reference model's max-skills scenario, confirmed by dogma.
    assert skill_time_multiplier(
        "manufacturing", {INDUSTRY: 5, ADVANCED_INDUSTRY: 5}
    ) == pytest.approx(0.68)
    assert skill_time_multiplier(
        "manufacturing", {ADVANCED_INDUSTRY: 1}
    ) == pytest.approx(0.97)
    assert skill_time_multiplier("manufacturing", {}) == 1.0


def test_skill_multiplier_activity_scopes():
    # Industry is manufacturing-only; copying carries Advanced Industry
    # alone; nothing reduces reactions.
    assert skill_time_multiplier("copying", {INDUSTRY: 5}) == 1.0
    assert skill_time_multiplier("copying", {ADVANCED_INDUSTRY: 5}) == pytest.approx(0.85)
    assert (
        skill_time_multiplier("reactions", {INDUSTRY: 5, ADVANCED_INDUSTRY: 5}) == 1.0
    )


# --- Rig percent (security scaling through the registry row) -----------------


def test_rig_percent_security_scaling():
    row_high = _registration(me_rig="t1", te_rig="t1", security_class="high")
    assert rig_percent(row_high, "me") == pytest.approx(2.0)  # ×1.0
    row_low = _registration(me_rig="t1", te_rig="t1", security_class="low")
    assert rig_percent(row_low, "me") == pytest.approx(3.8)  # 2.0 × 1.9
    row_null = _registration(me_rig="t1", te_rig="t1", security_class="null")
    assert rig_percent(row_null, "me") == pytest.approx(4.2)  # 2.0 × 2.1
    assert rig_percent(_registration(me_rig="none"), "me") == 0.0
    assert rig_percent(None, "me") == 0.0


# --- Material chain -----------------------------------------------------------


def test_material_chain_me_hull_rig():
    # Typhoon tritanium at ME 10, an Azbel (×0.99), no rig: 8M × 10
    # runs × 0.90 × 0.99 = 71,280,000 exactly.
    assert (
        adjusted_material_quantity(
            8_000_000, 10, me_percent=10, hull_material=0.99, rig_me_percent=0.0
        )
        == 71_280_000
    )
    # With a T1 ME rig in lowsec (3.8%): × 0.962.
    assert (
        adjusted_material_quantity(
            8_000_000, 10, me_percent=10, hull_material=0.99, rig_me_percent=3.8
        )
        == 68_571_360
    )
    # A smaller input rounding mid-chain: 55 × 10 × 0.9 × 0.99 × 0.962
    # = 471.4281 → 471 (round once, at the end).
    assert (
        adjusted_material_quantity(
            55, 10, me_percent=10, hull_material=0.99, rig_me_percent=3.8
        )
        == 471
    )


def test_material_chain_rounds_half_up():
    # 50 × 0.95 (ME 5) at a station, no rig = 47.5 → 48.
    assert (
        adjusted_material_quantity(
            50, 1, me_percent=5, hull_material=1.0, rig_me_percent=0.0
        )
        == 48
    )


def test_material_floor_is_runs():
    # ME can never push a consumable below one per run.
    assert (
        adjusted_material_quantity(
            1, 10, me_percent=10, hull_material=1.0, rig_me_percent=0.0
        )
        == 10
    )


# --- Time chain ---------------------------------------------------------------


def test_time_chain_te_hull_rig_skills():
    # Typhoon (5 h/run) × 10 runs at TE 20, an Azbel (×0.80 hull), a T1
    # TE rig in lowsec (20 × 1.9 = 38%), max skills (0.68):
    # 180,000 × 0.8 × 0.8 × 0.62 × 0.68 = 48,568.32 → 48,568 s.
    assert (
        job_time_seconds(
            18_000,
            10,
            te_percent=20,
            structure_type="azbel",
            activity_key="manufacturing",
            rig_te_percent=38.0,
            skill_multiplier=0.68,
        )
        == 48_568
    )


def test_time_chain_tatara_reaction_time():
    # Reactions read the refinery's reaction_time (Tatara ×0.75); no
    # skill reduces them.
    assert (
        job_time_seconds(
            1000,
            1,
            te_percent=0,
            structure_type="tatara",
            activity_key="reactions",
            rig_te_percent=0.0,
        )
        == 750
    )
    # The Athanor carries no reaction-time bonus.
    assert (
        job_time_seconds(
            1000,
            1,
            te_percent=0,
            structure_type="athanor",
            activity_key="reactions",
            rig_te_percent=0.0,
        )
        == 1000
    )


def test_copy_time_hull_and_skills_only():
    # Copy time: activity-5 duration × runs × hull time × skill — no TE,
    # no rig. 4 h/run × 10 runs at an Azbel with AI 5 (0.85):
    # 144,000 × 0.80 × 0.85 = 97,920.
    assert (
        copy_time_seconds(14_400, 10, structure_type="azbel", skill_multiplier=0.85)
        == 97_920
    )


# --- Install cost --------------------------------------------------------------


def test_install_cost_full_chain():
    # Base value bills the UN-adjusted quantities: 8M tritanium × 10
    # runs × 2.7 Ƶ + 55 CPG × 10 × 100 Ƶ = 216,055,000; × index 0.0046
    # × Azbel cost 0.96 × (1 + 0.5% tax) = 958,869.3744.
    cost = install_cost(
        {34: 80_000_000, 20410: 550},
        {34: 2.7, 20410: 100.0},
        system_index=0.0046,
        structure_type="azbel",
        tax_rate=0.005,
    )
    assert cost.base_value == pytest.approx(216_055_000)
    assert cost.total == pytest.approx(958_869.3744)
    assert cost.priced_types == 2 and cost.missing_types == 0


def test_install_cost_degrades_on_missing_inputs():
    # An unpriced material forces total=None but reports the partial
    # base value and the missing count.
    cost = install_cost(
        {34: 100, 20410: 550},
        {34: 2.7},
        system_index=0.0046,
        structure_type="azbel",
        tax_rate=0.005,
    )
    assert cost.total is None
    assert cost.missing_types == 1 and cost.priced_types == 1
    assert cost.base_value == pytest.approx(270.0)

    # No synced index for the system: same degradation.
    cost = install_cost(
        {34: 100}, {34: 2.7}, system_index=None, structure_type="azbel", tax_rate=None
    )
    assert cost.total is None and cost.system_index is None

    # An NPC-set tax (None) multiplies as 1.0.
    cost = install_cost(
        {34: 100},
        {34: 2.0},
        system_index=0.01,
        structure_type="station",
        tax_rate=None,
    )
    assert cost.total == pytest.approx(2.0)


# --- Blueprint selection ---------------------------------------------------------


def test_select_blueprint_originals_first():
    bpo_me8 = _blueprint(1, me=8, te=20, runs=-1)
    bpc_me10 = _blueprint(2, me=10, te=20, runs=25)
    # An original wins over a higher-ME copy: unlimited runs.
    assert select_blueprint([bpc_me10, bpo_me8]) is bpo_me8
    # Among originals, best ME, ties → TE.
    assert select_blueprint([bpo_me8, _blueprint(3, me=10, te=0, runs=-1)]) .item_id == 3
    # Copies only: best ME, ties → TE, then item id.
    assert select_blueprint([bpc_me10, _blueprint(4, me=10, te=24, runs=9)]).item_id == 4


def test_bpc_pool_runs_sums_copies():
    owned = [
        _blueprint(1, runs=-1),  # originals never count
        _blueprint(2, runs=9),
        _blueprint(3, runs=15),
    ]
    assert bpc_pool_runs(owned) == 24
    assert bpc_pool_runs([]) == 0
