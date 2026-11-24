"""The planner calculation engine (M4): run math, material adjustment,
job time, install cost, and copy time for a single blueprint — the
substrate M5's chain resolver and M9's distribution engine multiply
against.

Layout: the section above the orchestrator is PURE (no DB, no
framework) so the golden-value tests run hermetic; the orchestrator
below composes the catalog reads (app/industry.py), the facility
registry (app/facilities.py), and the synced world data into one
depth-1 PlanResult both planner pages consume.

Multiplier provenance (pinned from live sources, the facilities.py
pattern — a CCP balance pass is a table edit, never a code change):

- Skill→time: live ESI dogma 2026-11-23. Industry (3380) carries dogma
  attribute 440 (manufacturingTimeBonus) −4%/level, manufacturing only;
  Advanced Industry (3388) carries attribute 1961
  (advancedIndustrySkillIndustryJobTimeBonus) −3%/level on ALL industry
  job times — its dogma effects name manufacturing, copying, invention,
  and TE/ME research; reactions are absent (no skill reduces them).
  Bonuses stack multiplicatively: Industry 5 + Advanced Industry 5 =
  0.80 × 0.85 = 0.68 (the reference model's max-skills scenario, now
  confirmed rather than assumed). The deliberate M4 pick: ACTIVE skill
  levels (implants/boosters included — what gameplay math sees).
- Facility hull/rig/security multipliers: app/facilities.py (live ESI
  dogma 2026-11-23).
- Install cost: base input value (Σ base quantity × adjusted price,
  the UN-ME-adjusted SDE quantities — what the game bills against,
  per community documentation) × system cost index × facility hull
  cost bonus × (1 + tax). The in-game Typhoon hand-check (M4's exit
  criterion) is the pin of record; if it disagrees, the fix is here.
- Rounding: materials round half-up ONCE, at the end of the multiplier
  chain (the SDE math rule), with a floor of one unit per run; job
  time rounds to the second at the end of its chain.
"""

import math
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .facilities import (
    HULL_BONUSES,
    RegistrationRow,
    effective_rig_percent,
)
from .industry import (
    BlueprintRow,
    CommodityRecipe,
    active_skill_levels,
    adjusted_prices,
    commodity_recipe,
    cost_index,
    material_categories,
)
from .models import Character

# --- Skill→time multipliers (the M4 data table) -------------------------------

SKILL_INDUSTRY = 3380
SKILL_ADVANCED_INDUSTRY = 3388

ACTIVITY_SKILL_MAPPING: dict[str, dict[int, float]] = {
    # per-level fractional reductions; see module docstring for provenance.
    "manufacturing": {SKILL_INDUSTRY: 0.04, SKILL_ADVANCED_INDUSTRY: 0.03},
    "copying": {SKILL_ADVANCED_INDUSTRY: 0.03},
    "invention": {SKILL_ADVANCED_INDUSTRY: 0.03},
    "reactions": {},
}

# SDE activity id → registry activity key (the catalog speaks SDE).
SDE_ACTIVITY_KEYS = {1: "manufacturing", 11: "reactions"}

# Hull bonus keys by effect (facilities.HULL_BONUSES): reactions read
# the refinery's reaction_time, everything else the EC time bonus.
_HULL_TIME_KEYS: dict[str, tuple[str, ...]] = {
    "reactions": ("reaction_time",),
    "manufacturing": ("time",),
    "copying": ("time",),
    "invention": ("time",),
}


# --- Pure engine (hermetic — no DB past this line until the orchestrator) -----


def runs_for_units(units: int, products_per_run: int) -> int:
    """Runs needed to build `units` of a commodity yielding
    `products_per_run` per run: ⌈units ÷ products-per-run⌉ (the
    commodity-first run math — computed, never asked)."""
    if products_per_run <= 0:
        return 0
    return math.ceil(units / products_per_run)


def job_count(runs: int, max_production_limit: int | None) -> int:
    """Jobs the runs split into, bounded by the blueprint's max
    production limit per job (the game's ~30-day ceiling). No limit row
    means a single job. M9's even deliver-together split is scheduling;
    M4 just counts the jobs."""
    if runs <= 0:
        return 0
    if max_production_limit is None or max_production_limit <= 0:
        return 1
    return math.ceil(runs / max_production_limit)


def round_half_up(value: Decimal | float) -> int:
    """Round half away from zero at the end of a multiplier chain (the
    SDE math rule — Decimal, so a chain landing exactly on .5 rounds up
    deterministically)."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def skill_time_multiplier(activity_key: str, levels: dict[int, int]) -> float:
    """One character's time multiplier for an activity from their active
    skill levels: every mapped skill's per-level reduction, stacking
    multiplicatively (Industry 5 + Advanced Industry 5 = 0.68)."""
    multiplier = Decimal("1")
    for skill_id, per_level in ACTIVITY_SKILL_MAPPING.get(activity_key, {}).items():
        level = levels.get(skill_id, 0)
        multiplier *= Decimal("1") - Decimal(str(per_level)) * level
    return float(multiplier)


def facility_material_multiplier(structure_type: str) -> float:
    """The hull's material-consumption multiplier (ECs ×0.99); stations
    and refineries without a material bonus read 1.0."""
    return HULL_BONUSES.get(structure_type, {}).get("material", 1.0)


def facility_time_multiplier(structure_type: str, activity_key: str) -> float:
    """The hull's job-time multiplier for an activity: refineries read
    their reaction_time (Tatara ×0.75), ECs and everything else the
    general time bonus (Azbel ×0.80)."""
    bonuses = HULL_BONUSES.get(structure_type, {})
    for key in _HULL_TIME_KEYS.get(activity_key, ("time",)):
        if key in bonuses:
            return bonuses[key]
    return 1.0


def facility_cost_multiplier(structure_type: str) -> float:
    """The hull's install-cost multiplier (ECs ×0.97/×0.96/×0.95)."""
    return HULL_BONUSES.get(structure_type, {}).get("cost", 1.0)


def rig_percent(registration: RegistrationRow | None, rig_field: str) -> float:
    """A registration's effective rig reduction for one field ("me" or
    "te"), security-scaled; no registration or no rig reads 0. The rig
    applies as registered — the registry's single-tier fields are the
    owner's declaration for that activity (per-material-category rig
    qualification is recorded future work)."""
    if registration is None:
        return 0.0
    tier = registration.me_rig if rig_field == "me" else registration.te_rig
    return effective_rig_percent(
        registration.activity, rig_field, tier, registration.security_class or ""
    )


def adjusted_material_quantity(
    base_qty: int,
    runs: int,
    *,
    me_percent: int,
    hull_material: float,
    rig_me_percent: float,
) -> int:
    """One material's required quantity: base × runs × (1−ME/100) ×
    hull material × (1−rig/100), rounded half-up once at the end of the
    chain, floored at one unit per run (ME never reduces a consumable
    below the run count)."""
    product = (
        Decimal(base_qty)
        * runs
        * (Decimal("1") - Decimal(me_percent) / 100)
        * Decimal(str(hull_material))
        * (Decimal("1") - Decimal(str(rig_me_percent)) / 100)
    )
    return max(runs, round_half_up(product))


def job_time_seconds(
    duration_seconds: int,
    runs: int,
    *,
    te_percent: int,
    structure_type: str,
    activity_key: str,
    rig_te_percent: float,
    skill_multiplier: float = 1.0,
) -> int:
    """One job's duration: per-run duration × runs × (1−TE/100) × hull
    time × (1−rig/100) × skill multiplier, rounded to the second at the
    end of the chain."""
    product = (
        Decimal(duration_seconds)
        * runs
        * (Decimal("1") - Decimal(te_percent) / 100)
        * Decimal(str(facility_time_multiplier(structure_type, activity_key)))
        * (Decimal("1") - Decimal(str(rig_te_percent)) / 100)
        * Decimal(str(skill_multiplier))
    )
    return max(1, round_half_up(product))


def copy_time_seconds(
    copy_duration_seconds: int,
    runs: int,
    *,
    structure_type: str,
    skill_multiplier: float = 1.0,
) -> int:
    """Copying `runs` runs of a blueprint: per-run copy duration (SDE
    activity 5) × runs × hull time × the copying skill multiplier
    (Advanced Industry's −3%/level; no rig affects copying, and
    blueprint TE does not apply to copy jobs)."""
    product = (
        Decimal(copy_duration_seconds)
        * runs
        * Decimal(str(facility_time_multiplier(structure_type, "copying")))
        * Decimal(str(skill_multiplier))
    )
    return max(1, round_half_up(product))


@dataclass
class InstallCost:
    """Install cost for the plan's jobs. `total` is None whenever the
    inputs it needs are missing (no synced cost index for the system, or
    unpriced materials) — the readout degrades, never crashes."""

    total: float | None
    base_value: float | None  # Σ base_qty × adjusted_price over priced inputs
    system_index: float | None
    priced_types: int
    missing_types: int


def install_cost(
    base_quantities: dict[int, int],
    prices: dict[int, float | None],
    *,
    system_index: float | None,
    structure_type: str,
    tax_rate: float | None,
) -> InstallCost:
    """Install cost = base input value × system cost index × hull cost
    bonus × (1 + facility tax), where the base value bills the
    UN-ME-adjusted SDE quantities (see module docstring). Materials
    without a synced adjusted price count as missing and force
    total=None; an NPC-set tax (None) multiplies as 1.0."""
    base_value = Decimal("0")
    priced = missing = 0
    for type_id, quantity in base_quantities.items():
        price = prices.get(type_id)
        if price is None:
            missing += 1
            continue
        priced += 1
        base_value += Decimal(quantity) * Decimal(str(price))
    total: float | None = None
    if system_index is not None and missing == 0 and priced:
        tax = Decimal("1") + (Decimal(str(tax_rate)) if tax_rate is not None else 0)
        total = float(
            base_value
            * Decimal(str(system_index))
            * Decimal(str(facility_cost_multiplier(structure_type)))
            * tax
        )
    return InstallCost(
        total=total,
        base_value=float(base_value) if priced else None,
        system_index=system_index,
        priced_types=priced,
        missing_types=missing,
    )


def select_blueprint(owned: list[BlueprintRow]) -> BlueprintRow | None:
    """The blueprint the calculation runs against: originals first
    (unlimited runs makes an original strictly more capable at equal
    ME/TE), then best ME, ties broken by TE, then item id. The full
    multi-copy selection policy stays parked for M5 (open question of
    record); this default matches the build-plan mockup's "best-ME"
    wording."""
    if not owned:
        return None
    return min(
        owned,
        key=lambda row: (
            0 if row.is_original else 1,
            -row.material_efficiency,
            -row.time_efficiency,
            row.item_id,
        ),
    )


def bpc_pool_runs(owned: list[BlueprintRow]) -> int:
    """Total remaining runs across every owned copy of the type — the
    run-coverage number that drives M5/M9 copy planning when no
    original exists."""
    return sum(row.runs or 0 for row in owned if not row.is_original)


# --- Depth-1 orchestrator (M4: direct inputs only; M5 deepens the tiers) ------


@dataclass
class PlanMaterial:
    """One direct input of the target: the target-adjusted required
    quantity, split by whether it is itself buildable (the depth-1
    tier boundary — M5's recursion signal)."""

    type_id: int
    name: str
    base_qty: int  # SDE quantity per run
    required_qty: int  # adjusted for ME/rig/hull at the target's runs
    buildable: bool
    category_name: str | None = None
    group_name: str | None = None


@dataclass
class PlanIntermediate:
    """One buildable direct input with its own producing blueprint:
    required quantity, its runs, and its owned-blueprint status (its
    own materials are the chain's next level — M5)."""

    type_id: int
    name: str
    required_qty: int
    runs: int
    products_per_run: int
    blueprint_type_id: int
    blueprint_name: str
    activity_id: int
    owned: bool
    best_owned: BlueprintRow | None
    bpc_runs: int


@dataclass
class PlanCharacterTime:
    """One participant's time on the target's jobs: active skill levels
    → multiplier → duration. The depth-1 consumer of the participants
    input (assignment itself is M9)."""

    character_id: int
    name: str
    skill_levels: dict[int, int]
    multiplier: float
    job_seconds: int
    total_seconds: int
    holds_gate: bool
    missing_skills: list[str] = field(default_factory=list)


@dataclass
class PlanResult:
    """Everything both planner pages render for one depth-1 plan."""

    recipe: CommodityRecipe
    units: int
    activity_key: str
    runs: int
    jobs: int
    max_production_limit: int | None
    selected: BlueprintRow | None
    me: int
    te: int
    bpc_pool_runs: int | None  # None: an original is owned (unlimited)
    materials: list[PlanMaterial]
    intermediates: list[PlanIntermediate]
    raw: list[PlanMaterial]  # the non-buildable direct inputs
    facility: RegistrationRow | None
    copy_facility: RegistrationRow | None
    base_job_seconds: int  # unskilled, no-facility reference
    job_seconds: int  # one full job at facility + best participant
    total_seconds: int  # every job, serial
    participant_times: list[PlanCharacterTime]
    install: InstallCost
    copy_seconds_per_run: int | None
    copy_total_seconds: int | None
    has_original: bool


async def depth1_plan(
    db: AsyncSession,
    *,
    target_type_id: int,
    units: int,
    participants: list[int] | None = None,
    facilities: dict[str, RegistrationRow | None] | None = None,
    me_override: int | None = None,
    te_override: int | None = None,
) -> PlanResult | None:
    """Resolve and calculate the depth-1 plan for one commodity:
    the selected blueprint (best owned, or ME/TE 0 when unowned), run
    and job math, the direct inputs split buildable/raw with the
    target-adjusted quantities, time at the facility with per-participant
    skill multipliers, install cost against the synced world data, and
    copy time for the target's blueprint. None when the type is not a
    catalog product. `facilities` maps registry activity keys to chosen
    registrations; the target's activity resolves its own entry (the
    route can't know manufacturing-vs-reactions before the recipe
    reads), and copying reads the "copying" entry."""
    recipe = await commodity_recipe(db, target_type_id)
    if recipe is None:
        return None
    facilities = facilities or {}
    activity_key = SDE_ACTIVITY_KEYS.get(recipe.activity_id, "manufacturing")
    facility = facilities.get(activity_key)
    copy_facility = facilities.get("copying")
    units = max(1, units)
    runs = runs_for_units(units, recipe.products_per_run)
    jobs = job_count(runs, recipe.max_production_limit)

    selected = select_blueprint(recipe.owned)
    has_original = selected is not None and selected.is_original
    me = selected.material_efficiency if selected is not None else 0
    te = selected.time_efficiency if selected is not None else 0
    if me_override is not None:
        me = me_override
    if te_override is not None:
        te = te_override

    # Materials at the target's facility and blueprint ME.
    hull_material = facility_material_multiplier(
        facility.structure_type if facility else "station"
    )
    rig_me = rig_percent(facility, "me")
    materials = [
        PlanMaterial(
            type_id=material.type_id,
            name=material.name,
            base_qty=material.quantity_per_run,
            required_qty=adjusted_material_quantity(
                material.quantity_per_run,
                runs,
                me_percent=me,
                hull_material=hull_material,
                rig_me_percent=rig_me,
            ),
            buildable=material.buildable,
        )
        for material in recipe.materials
    ]

    # Raw-input classification for the tier-3 grouping (M5-shared).
    raw_ids = [material.type_id for material in materials if not material.buildable]
    categories = await material_categories(db, raw_ids)
    for material in materials:
        if not material.buildable:
            category, group = categories.get(material.type_id, (None, None))
            material.category_name = category
            material.group_name = group

    # Buildable inputs become intermediates: their own producer recipe
    # (owned status + best owned) and their run count.
    intermediate_inputs = [material for material in materials if material.buildable]
    intermediates: list[PlanIntermediate] = []
    for material in intermediate_inputs:
        sub_recipe = await commodity_recipe(db, material.type_id)
        if sub_recipe is None:
            # Catalog-flagged but the read came back empty (SDE quirk):
            # keep the row, without producer detail.
            intermediates.append(
                PlanIntermediate(
                    type_id=material.type_id,
                    name=material.name,
                    required_qty=material.required_qty,
                    runs=0,
                    products_per_run=1,
                    blueprint_type_id=0,
                    blueprint_name="",
                    activity_id=recipe.activity_id,
                    owned=False,
                    best_owned=None,
                    bpc_runs=0,
                )
            )
            continue
        best = select_blueprint(sub_recipe.owned)
        intermediates.append(
            PlanIntermediate(
                type_id=material.type_id,
                name=material.name,
                required_qty=material.required_qty,
                runs=runs_for_units(material.required_qty, sub_recipe.products_per_run),
                products_per_run=sub_recipe.products_per_run,
                blueprint_type_id=sub_recipe.blueprint_type_id,
                blueprint_name=sub_recipe.blueprint_name,
                activity_id=sub_recipe.activity_id,
                owned=bool(sub_recipe.owned),
                best_owned=best,
                bpc_runs=bpc_pool_runs(sub_recipe.owned),
            )
        )

    # Time: the target's jobs at the facility, per participant.
    structure_type = facility.structure_type if facility else "station"
    rig_te = rig_percent(facility, "te")
    base_job_seconds = (
        recipe.duration_seconds or 0
    ) * runs if recipe.duration_seconds else 0

    async def _participant_rows() -> list[PlanCharacterTime]:
        if participants is None:
            # The default pool is the main character's corporation's
            # members (the participants decision of record); without a
            # main, nobody.
            main = (
                await db.execute(select(Character).where(Character.is_main))
            ).scalar_one_or_none()
            query = select(Character)
            if main is not None and main.corporation_id is not None:
                query = query.where(Character.corporation_id == main.corporation_id)
            roster = (
                (await db.execute(query.order_by(Character.name))).scalars().all()
            )
            ids = [character.character_id for character in roster]
        else:
            ids = list(participants)
        if not ids:
            return []
        levels = await active_skill_levels(db, ids)
        names = {
            character.character_id: character.name
            for character in (
                await db.execute(
                    select(Character).where(Character.character_id.in_(ids))
                )
            ).scalars()
        }
        rows_out: list[PlanCharacterTime] = []
        for character_id in ids:
            char_levels = levels.get(character_id, {})
            multiplier = skill_time_multiplier(activity_key, char_levels)
            missing = [
                skill.name
                for skill in recipe.skills
                if char_levels.get(skill.skill_id, 0) < skill.level
            ]
            per_job = (
                job_time_seconds(
                    recipe.duration_seconds,
                    min(runs, recipe.max_production_limit or runs),
                    te_percent=te,
                    structure_type=structure_type,
                    activity_key=activity_key,
                    rig_te_percent=rig_te,
                    skill_multiplier=multiplier,
                )
                if recipe.duration_seconds
                else 0
            )
            rows_out.append(
                PlanCharacterTime(
                    character_id=character_id,
                    name=names.get(character_id, f"Character #{character_id}"),
                    skill_levels=char_levels,
                    multiplier=multiplier,
                    job_seconds=per_job,
                    total_seconds=per_job * jobs,
                    holds_gate=not missing,
                    missing_skills=missing,
                )
            )
        return rows_out

    participant_times = await _participant_rows()

    # Install cost: base input value from the un-adjusted quantities ×
    # synced adjusted prices, against the facility's system index.
    base_quantities = {
        material.type_id: material.base_qty * runs for material in materials
    }
    prices = await adjusted_prices(db, list(base_quantities))
    install = install_cost(
        base_quantities,
        prices,
        system_index=await cost_index(
            db, facility.system_id if facility else None, activity_key
        ),
        structure_type=structure_type,
        tax_rate=facility.tax_rate if facility else None,
    )

    # Copy time for the target's blueprint at the copy facility.
    copy_seconds_per_run: int | None = None
    copy_total_seconds: int | None = None
    if recipe.copy_duration_seconds:
        best_multiplier = min(
            (row.multiplier for row in participant_times), default=1.0
        )
        copy_structure = copy_facility.structure_type if copy_facility else "station"
        copy_seconds_per_run = copy_time_seconds(
            recipe.copy_duration_seconds,
            1,
            structure_type=copy_structure,
            skill_multiplier=best_multiplier,
        )
        copy_total_seconds = copy_time_seconds(
            recipe.copy_duration_seconds,
            runs,
            structure_type=copy_structure,
            skill_multiplier=best_multiplier,
        )

    # The headline job time: facility + the best-skilled participant
    # (assignment is M9; the readout names whose multiplier it used).
    best_multiplier = min(
        (row.multiplier for row in participant_times if row.holds_gate),
        default=1.0,
    )
    per_full_job = (
        job_time_seconds(
            recipe.duration_seconds,
            min(runs, recipe.max_production_limit or runs),
            te_percent=te,
            structure_type=structure_type,
            activity_key=activity_key,
            rig_te_percent=rig_te,
            skill_multiplier=best_multiplier,
        )
        if recipe.duration_seconds
        else 0
    )

    return PlanResult(
        recipe=recipe,
        units=units,
        activity_key=activity_key,
        runs=runs,
        jobs=jobs,
        max_production_limit=recipe.max_production_limit,
        selected=selected,
        me=me,
        te=te,
        bpc_pool_runs=None if has_original else bpc_pool_runs(recipe.owned),
        materials=materials,
        intermediates=intermediates,
        raw=[material for material in materials if not material.buildable],
        facility=facility,
        copy_facility=copy_facility,
        base_job_seconds=base_job_seconds,
        job_seconds=per_full_job,
        total_seconds=per_full_job * jobs,
        participant_times=participant_times,
        install=install,
        copy_seconds_per_run=copy_seconds_per_run,
        copy_total_seconds=copy_total_seconds,
        has_original=has_original,
    )
