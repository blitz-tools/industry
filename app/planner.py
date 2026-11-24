"""The planner calculation engine (M4) and chain resolver (M5): run
math, material adjustment, job time, install cost, and copy time per
blueprint — and the recursive BOM explosion that turns one target into
the phased chain both planner pages render.

Layout: the sections above the orchestrators are PURE (no DB, no
framework) so the golden-value tests run hermetic; the orchestrators
below compose the bulk catalog reads (app/industry.py), the facility
registry (app/facilities.py), and the synced world data into one
ChainPlan — the resolved, enriched chain.

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
    ChainMaterial,
    CommodityRecipe,
    RecipeHeader,
    active_skill_levels,
    activity_materials,
    activity_skills,
    adjusted_prices,
    commodity_recipe,
    cost_index,
    material_categories,
    owned_blueprints_for_types,
    pool_on_hand,
    recipe_headers,
    type_names,
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
    if system_index is not None and missing == 0 and (priced or not base_quantities):
        # No materials at all bills zero (a recipe with an empty material
        # list is not missing price data).
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


@dataclass
class PlanMaterial:
    """One build input of a node: the SDE per-run quantity, the required
    quantity adjusted for the node's ME/rig/hull at its runs, split by
    whether it is itself buildable (the chain-continuation signal)."""

    type_id: int
    name: str
    base_qty: int  # SDE quantity per run
    required_qty: int  # adjusted for ME/rig/hull at the node's runs
    buildable: bool
    category_name: str | None = None
    group_name: str | None = None


# --- Chain resolver (M5: recursive BOM explosion → phases) ----------------------
#
# Pure like the engine above: the walk consumes an in-memory ChainCatalog
# (bulk-read by the orchestrators below) and produces the phase tree the
# chain-view surfaces render. Structural rules of record:
#
# - Level-by-level aggregation from the target (the executable spec,
#   reference/chain_expand.py's aggregated_phases): same-type demands
#   merge within a level, then round runs once — never per parent (the
#   Typhoon chain's RCF 8→7 runs saving), and never across levels (the
#   Charon chain's recurring commodities: one node per (type, phase)
#   occurrence, runs rounded per occurrence).
# - Phases count up in build order: the final all-terminal level is
#   phase 0, the target is phases[-1]. A level's rows mix buildables and
#   terminators whenever a recipe takes both (the Typhoon's direct
#   minerals sit well above phase 0).
# - Cycle detection is mandatory (reference/CENSUS.md: 51 cycles in the
#   mfg+reaction producer graph, mostly self-referential structure
#   arrays): a material that sits on a producer-graph cycle AND was
#   already expanded at or above the consumer's level is a back-edge —
#   rendered as a flagged terminal row one phase below the consumer,
#   recorded in ChainResult.cycles, never recursed, never counted as a
#   raw to acquire. Non-cyclic recurrence (the Charon's PO at two
#   phases) is never cut — cyclic status is what tells them apart.
# - Quantities adjust per node when ChainAdjustments carries the pool's
#   blueprint ME and the facility material multipliers; with no
#   adjustments the walk is exactly the unadjusted golden shape the
#   chain documents pin (the functional diff harness runs it that way).


@dataclass
class ChainCatalog:
    """The recipe closure for one walk, bulk-read upfront: producer
    headers and per-run material lists keyed by PRODUCT type id (the
    prefer-published producer choice is already applied by the read),
    plus the name map covering terminators (which have no header row).
    Types absent from `headers` are terminators."""

    headers: dict[int, RecipeHeader]
    materials: dict[int, list[ChainMaterial]]
    names: dict[int, str]


@dataclass
class ChainAdjustments:
    """Per-node multiplier inputs the walk applies when demanding
    inputs: the pool's blueprint ME per product type, and per activity
    the facility's (hull material multiplier, rig ME percent) — kept
    separate so the walk's arithmetic is identical to M4's material
    chain (one Decimal rounding at the end). Empty (the default) is the
    unadjusted golden walk — ME 0, no facility."""

    me_percent: dict[int, int] = field(default_factory=dict)
    material_factors: dict[str, tuple[float, float]] = field(default_factory=dict)


@dataclass
class NodeDemand:
    """One of a node's material demands at its runs: the SDE per-run
    quantity (un-adjusted — what install cost bills) and the required
    quantity after the node's ME and facility multipliers."""

    type_id: int
    base_qty: int
    required_qty: int


@dataclass
class NodeCalculation:
    """The enrichment layer over one buildable node (filled by
    chain_plan, None from the pure walk): blueprint selection and
    ME/TE, the adjusted material rows, un-skilled time at the facility,
    install cost, and the pool-stock coverage of the node's own type."""

    me: int
    te: int
    selected: BlueprintRow | None
    has_original: bool
    bpc_pool_runs: int | None  # None: an original is owned (unlimited)
    materials: list[PlanMaterial]  # adjusted quantities, names, categories
    base_quantities: dict[int, int]  # UN-adjusted (install cost)
    job_seconds: int  # one job at facility + best gate-holder
    total_seconds: int  # every job, serial
    install: InstallCost
    holds_gate: bool  # any participant holds the blueprint's skills
    on_hand: int | None  # pool stock for the node's type
    coverage: float | None  # on_hand ÷ qty, uncapped
    has_buildable_inputs: bool  # any demand is itself a chain node
    inputs_ready: bool  # every terminator demand covered by pool stock


@dataclass
class ChainNode:
    """One commodity occurrence in the chain: the unit is (type, phase)
    — a recurring commodity is several nodes. `runs` is None on
    terminal rows (raw materials and cycle cuts); `cycle` marks a row
    created by a broken back-edge."""

    type_id: int
    name: str
    phase: int
    qty: int  # required units, merged within the phase
    runs: int | None
    jobs: int
    activity_id: int | None
    blueprint_type_id: int | None
    products_per_run: int  # 0 on terminal rows
    max_production_limit: int | None
    is_target: bool
    cycle: bool
    blueprint_name: str | None = None
    group_name: str | None = None  # invGroups name (the phase display name)
    demands: list[NodeDemand] = field(default_factory=list)
    calc: NodeCalculation | None = None

    @property
    def buildable(self) -> bool:
        return self.runs is not None


@dataclass
class ChainPhase:
    """One dependency layer, counting up in build order (phase 0 = the
    final all-terminal level)."""

    phase: int
    nodes: list[ChainNode]

    @property
    def total_runs(self) -> int:
        return sum(node.runs or 0 for node in self.nodes)

    @property
    def total_jobs(self) -> int:
        return sum(node.jobs for node in self.nodes)

    @property
    def activity_ids(self) -> list[int]:
        """The distinct producing activities among the phase's buildable
        nodes (a phase can mix manufacturing and reactions)."""
        return sorted({node.activity_id for node in self.nodes if node.activity_id})


@dataclass
class CycleBreak:
    """One broken back-edge: the consumer whose expansion was cut, the
    cyclic material it demanded, the phase the flagged row landed on,
    and the demand quantity. Surfaced, never silently truncated; names
    filled by chain_plan."""

    consumer_type_id: int
    material_type_id: int
    phase: int
    qty: int
    consumer_name: str | None = None
    material_name: str | None = None


@dataclass
class RawTotal:
    """One chain terminator summed across every phase — the
    raw-material acquisition table's row. `on_hand` (the pool
    measurement) and the category/group classification are filled by
    chain_plan; None marks the pure walk."""

    type_id: int
    name: str
    qty: int
    on_hand: int | None = None
    category_name: str | None = None
    group_name: str | None = None


@dataclass
class ChainResult:
    """The resolved chain: ascending phases (target in phases[-1]),
    chain-wide terminator totals, and the cycle cuts. Node-level
    calculation, time, and coverage live on each node's calc (filled by
    chain_plan; the pure walk leaves them None)."""

    target_type_id: int
    units: int
    phases: list[ChainPhase]
    raw_totals: list[RawTotal]
    cycles: list[CycleBreak]

    @property
    def target_node(self) -> ChainNode:
        return next(node for phase in self.phases for node in phase.nodes
                    if node.is_target)

    @property
    def node_count(self) -> int:
        return sum(len(phase.nodes) for phase in self.phases)

    @property
    def buildable_nodes(self) -> list[ChainNode]:
        return [node for phase in self.phases for node in phase.nodes
                if node.buildable and not node.cycle]

    @property
    def total_runs(self) -> int:
        return sum(phase.total_runs for phase in self.phases)

    @property
    def total_jobs(self) -> int:
        return sum(phase.total_jobs for phase in self.phases)

    @property
    def total_seconds(self) -> int:
        return sum(node.calc.total_seconds for node in self.buildable_nodes
                   if node.calc is not None)

    @property
    def install_total(self) -> float:
        """Sum of the priced nodes' install costs — a partial sum
        whenever a node's materials lack synced prices (the readout
        carries install_missing_nodes beside it)."""
        return sum(node.calc.install.total for node in self.buildable_nodes
                   if node.calc is not None and node.calc.install.total is not None)

    @property
    def install_missing_nodes(self) -> int:
        return sum(1 for node in self.buildable_nodes
                   if node.calc is not None and node.calc.install.total is None)


def _cyclic_types(catalog: ChainCatalog) -> set[int]:
    """Types on a producer-graph cycle: members of a non-trivial
    strongly connected component of the material graph, plus self-loops
    (a one-node SCC with an edge to itself). Iterative Tarjan over the
    catalog closure — the walk's whole graph is in memory, so this is
    cheap and hermetic."""
    graph: dict[int, list[int]] = {t: [] for t in catalog.headers}
    for product, materials in catalog.materials.items():
        graph.setdefault(product, [])
        for material in materials:
            graph[product].append(material.type_id)
            graph.setdefault(material.type_id, [])

    index: dict[int, int] = {}
    low: dict[int, int] = {}
    on_stack: set[int] = set()
    stack: list[int] = []
    counter = 0
    cyclic: set[int] = set()
    for root in graph:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(graph[root]))]
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(graph[child])))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    cyclic.update(component)
                elif component[0] in graph[component[0]]:
                    cyclic.add(component[0])  # self-loop
    return cyclic


def resolve_chain(
    target_type_id: int,
    units: int,
    catalog: ChainCatalog,
    adjustments: ChainAdjustments | None = None,
    cyclic: set[int] | None = None,
) -> ChainResult:
    """Walk the target's manufacturing (1) and reaction (11) inputs to
    the full chain: level by level from the target, same-type demands
    merging within a level, runs rounding once per merged occurrence,
    back-edges cut and flagged. The level list is built target-first and
    reversed once at the end so phases ascend in build order. Every
    demand path is simple (a revisited type is a cycle, and cycles cut
    once expanded), so the walk always terminates; the SDE bounds phase
    depth at 7 for published targets but nothing here assumes a
    ceiling. `cyclic` (the catalog's on-cycle types, precomputed) lets a
    caller walking many targets over one catalog skip the per-walk SCC
    pass."""
    adjustments = adjustments or ChainAdjustments()
    cyclic = _cyclic_types(catalog) if cyclic is None else cyclic
    units = max(1, units)

    levels: list[list[ChainNode]] = []
    expanded_at: dict[int, int] = {}  # type id -> level it expanded at
    recorded_cuts: list[tuple[int, int, int, int]] = []  # consumer, material, level, qty
    raw_accum: dict[int, int] = {}
    reqs: dict[int, int] = {target_type_id: units}
    pending_cuts: dict[int, int] = {}  # cut rows to render at the next level
    level_idx = 0

    def _node(type_id: int, qty: int, *, runs: int | None, cycle: bool,
              is_target: bool = False) -> ChainNode:
        header = catalog.headers.get(type_id)
        return ChainNode(
            type_id=type_id,
            name=catalog.names.get(type_id, f"#{type_id}"),
            phase=0,  # assigned by the reversal below
            qty=qty,
            runs=runs,
            jobs=(job_count(runs, header.max_production_limit)
                  if header and runs is not None else 0),
            activity_id=header.activity_id if header else None,
            blueprint_type_id=header.blueprint_type_id if header else None,
            blueprint_name=header.blueprint_name if header else None,
            products_per_run=header.products_per_run if header else 0,
            max_production_limit=header.max_production_limit if header else None,
            is_target=is_target,
            cycle=cycle,
        )

    while reqs or pending_cuts:
        rows: list[ChainNode] = [
            _node(type_id, qty, runs=None, cycle=True)
            for type_id, qty in sorted(pending_cuts.items())
        ]
        pending_cuts = {}

        buildable: dict[int, tuple[int, RecipeHeader]] = {}
        for type_id, qty in sorted(reqs.items()):
            header = catalog.headers.get(type_id)
            if header is None:
                rows.append(_node(type_id, qty, runs=None, cycle=False,
                                  is_target=level_idx == 0))
                raw_accum[type_id] = raw_accum.get(type_id, 0) + qty
            else:
                buildable[type_id] = (qty, header)
        row_by_type: dict[int, ChainNode] = {}
        for type_id, (qty, header) in sorted(buildable.items()):
            runs = runs_for_units(qty, header.products_per_run)
            node = _node(type_id, qty, runs=runs, cycle=False,
                         is_target=level_idx == 0)
            rows.append(node)
            row_by_type[type_id] = node
            expanded_at[type_id] = level_idx
        levels.append(rows)

        # Expand this level's buildables into the next level's demands,
        # cutting back-edges (cyclic materials already expanded at or
        # above this level).
        nxt: dict[int, int] = {}
        cuts: dict[int, int] = {}
        for type_id, (qty, header) in sorted(buildable.items()):
            runs = runs_for_units(qty, header.products_per_run)
            me = adjustments.me_percent.get(type_id, 0)
            activity_key = SDE_ACTIVITY_KEYS.get(header.activity_id, "manufacturing")
            hull_material, rig_me = adjustments.material_factors.get(
                activity_key, (1.0, 0.0)
            )
            demands: list[NodeDemand] = []
            for material in catalog.materials.get(type_id, []):
                required = adjusted_material_quantity(
                    material.quantity_per_run,
                    runs,
                    me_percent=me,
                    hull_material=hull_material,
                    rig_me_percent=rig_me,
                )
                demands.append(NodeDemand(
                    type_id=material.type_id,
                    base_qty=material.quantity_per_run,
                    required_qty=required,
                ))
                if (material.type_id in cyclic
                        and expanded_at.get(material.type_id, level_idx + 1)
                        <= level_idx):
                    cuts[material.type_id] = cuts.get(material.type_id, 0) + required
                    recorded_cuts.append(
                        (type_id, material.type_id, level_idx + 1, required)
                    )
                else:
                    nxt[material.type_id] = nxt.get(material.type_id, 0) + required
            row_by_type[type_id].demands = demands
        reqs = nxt
        pending_cuts = cuts
        level_idx += 1

    # Reverse once: level 0 (the target) becomes the highest phase.
    depth = len(levels)
    phases: list[ChainPhase] = []
    for i, rows in enumerate(levels):
        for node in rows:
            node.phase = depth - 1 - i
        phases.append(ChainPhase(phase=depth - 1 - i, nodes=rows))
    phases.reverse()

    raw_totals = [
        RawTotal(type_id=type_id, name=catalog.names.get(type_id, f"#{type_id}"),
                 qty=qty)
        for type_id, qty in sorted(raw_accum.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    cycles = [
        CycleBreak(consumer_type_id=consumer, material_type_id=material,
                   phase=depth - 1 - cut_level, qty=qty)
        for consumer, material, cut_level, qty in recorded_cuts
    ]
    return ChainResult(
        target_type_id=target_type_id,
        units=units,
        phases=phases,
        raw_totals=raw_totals,
        cycles=cycles,
    )


# --- Chain orchestrators (M5: bulk reads + enrichment) -------------------------
#
# Everything from here down touches the DB. build_chain_catalog collects
# the recipe closure in level-sized batches; chain_plan enriches each
# buildable node with the M4 engine per node — selection, ME/TE, adjusted
# materials at the node's OWN activity facility, time at the best
# gate-holding participant, install cost, pool-stock coverage — and rolls
# the chain totals up from the nodes.


def fresh_node_state(node: ChainNode) -> tuple[str, str | None]:
    """(state, reason) for a buildable node on a fresh plan, per the
    stage-state model: computed from ownership, skills, dependencies,
    and stock — exactly the inputs M5 holds. The running/deliver/
    complete states are active-plan progress (M6) and never appear here.
    Reasons order by what the owner can act on: a missing blueprint or
    an unheld skill gate outranks waiting on an upstream phase, which
    resolves itself as the chain builds."""
    if node.cycle:
        return ("missing", "cycle")
    calc = node.calc
    if calc is None:
        return ("missing", None)
    if calc.selected is None:
        return ("missing", "blueprint-missing")
    if not calc.holds_gate:
        return ("missing", "skill-gated")
    if calc.has_buildable_inputs:
        return ("missing", "waiting-upstream")
    if not calc.inputs_ready:
        return ("missing", "stock-gap")
    return ("ready", None)


def phase_state(phase: ChainPhase) -> str:
    """A phase summary's state: worst buildable child wins (the
    stage-state rollup rule)."""
    buildables = [node for node in phase.nodes if node.buildable and not node.cycle]
    if any(fresh_node_state(node)[0] == "missing" for node in buildables):
        return "missing"
    return "ready" if buildables else "ready"


@dataclass
class ChainParticipantTime:
    """One participant's chain-level readout: their time multipliers per
    walk activity, how many chain nodes their skills gate them onto, and
    their solo serial time over those nodes (assignment itself is M9 —
    this is the eligibility picture)."""

    character_id: int
    name: str
    multipliers: dict[str, float]  # activity key -> multiplier
    nodes_gated: int
    gated_total_seconds: int
    holds_target_gate: bool
    missing_target_skills: list[str] = field(default_factory=list)


@dataclass
class ChainPlan:
    """chain_plan's output: the enriched chain plus the plan-level
    readouts both planner pages render — the participant rows, the
    target blueprint's owned-copies overlay, and its copy-time math
    (M4's readout, unchanged)."""

    chain: ChainResult
    participants: list[ChainParticipantTime]
    target_owned: list[BlueprintRow]
    copy_facility: RegistrationRow | None
    copy_seconds_per_run: int | None
    copy_total_seconds: int | None


async def build_chain_catalog(
    db: AsyncSession, target_type_ids: list[int]
) -> ChainCatalog | None:
    """The recipe closure for one or more seeds, read in level-sized
    batches: producer headers for the frontier, then the frontier's
    material lists, repeating on unseen material types. Each type is
    read once (the visited set also terminates cycles), so an
    eighty-buildable chain costs a handful of queries. None when no seed
    is a catalog product. Seed sets are read in chunks — the census
    passes every product id at once and SQLite's bind-parameter limit
    is not a contract."""
    _CHUNK = 900

    async def _headers_for(ids: list[int]) -> dict[int, RecipeHeader]:
        out: dict[int, RecipeHeader] = {}
        for start in range(0, len(ids), _CHUNK):
            for header in (
                await recipe_headers(db, ids[start : start + _CHUNK])
            ).values():
                out[header.type_id] = header
        return out

    seeds = list(dict.fromkeys(target_type_ids))
    headers = await _headers_for(seeds)
    if not headers:
        return None

    materials: dict[int, list[ChainMaterial]] = {}
    frontier = list(headers)
    while frontier:
        by_bp: dict[tuple[int, int], list[ChainMaterial]] = {}
        for start in range(0, len(frontier), _CHUNK):
            by_bp.update(
                await activity_materials(
                    db,
                    [headers[t].blueprint_type_id
                     for t in frontier[start : start + _CHUNK]],
                )
            )
        candidates: list[int] = []
        for type_id in frontier:
            header = headers[type_id]
            mats = by_bp.get((header.blueprint_type_id, header.activity_id), [])
            materials[type_id] = mats
            candidates.extend(m.type_id for m in mats if m.type_id not in headers)
        if candidates:
            for header in (
                await _headers_for(list(dict.fromkeys(candidates)))
            ).values():
                headers.setdefault(header.type_id, header)
        frontier = [
            type_id for type_id in dict.fromkeys(candidates) if type_id in headers
        ]

    touched = list(headers) + [
        m.type_id for mats in materials.values() for m in mats
    ]
    names = await type_names(db, list(dict.fromkeys(touched)))
    return ChainCatalog(headers=headers, materials=materials, names=names)


async def chain_plan(
    db: AsyncSession,
    *,
    target_type_id: int,
    units: int,
    participants: list[int] | None = None,
    facilities: dict[str, RegistrationRow | None] | None = None,
    me_override: int | None = None,
    te_override: int | None = None,
    include_personal_stock: bool = False,
) -> ChainPlan | None:
    """Resolve and calculate the full chain for one commodity: the pure
    walk over the bulk-read catalog, then per-node enrichment (selection
    and ME/TE per node — overrides apply to the target node only,
    preserving M4's hand-check semantics; materials at each node's own
    activity facility; time at the best gate-holding participant; install
    cost against the synced world data; pool-stock coverage). None when
    the type is not a catalog product. `facilities` maps registry
    activity keys to chosen registrations; each node resolves its own
    entry, copying reads the "copying" entry. `include_personal_stock`
    widens the coverage measurement from the corp office hangars (the
    default — participants may be job-allocation positions, not
    material sources) to the participants' personal assets."""
    catalog = await build_chain_catalog(db, [target_type_id])
    if catalog is None or target_type_id not in catalog.headers:
        return None
    facilities = facilities or {}
    units = max(1, units)

    # The participant pool: the main's corporation's members by default
    # (the participants decision of record), else the explicit list. The
    # main's corporation is the office pool regardless — the shared
    # inventory corporate plans draw from.
    main = (
        await db.execute(select(Character).where(Character.is_main))
    ).scalar_one_or_none()
    if participants is None:
        query = select(Character)
        if main is not None and main.corporation_id is not None:
            query = query.where(Character.corporation_id == main.corporation_id)
        roster = (
            (await db.execute(query.order_by(Character.name))).scalars().all()
        )
    else:
        pool_ids = list(participants)
        roster = (
            (
                await db.execute(
                    select(Character).where(Character.character_id.in_(pool_ids))
                )
            ).scalars().all()
            if pool_ids
            else []
        )
    pool_ids = [character.character_id for character in roster]
    corporation_id = main.corporation_id if main is not None else None
    levels = await active_skill_levels(db, pool_ids) if pool_ids else {}
    roster_names = {character.character_id: character.name for character in roster}

    # Blueprint selection and ME/TE per product type (best owned, else 0).
    owned_map = await owned_blueprints_for_types(
        db,
        list({header.blueprint_type_id for header in catalog.headers.values()}),
    )
    selected_by_type = {
        type_id: select_blueprint(owned_map.get(header.blueprint_type_id, []))
        for type_id, header in catalog.headers.items()
    }
    me_percent = {
        type_id: selected.material_efficiency if selected is not None else 0
        for type_id, selected in selected_by_type.items()
    }
    te_percent = {
        type_id: selected.time_efficiency if selected is not None else 0
        for type_id, selected in selected_by_type.items()
    }
    if me_override is not None:
        me_percent[target_type_id] = me_override
    if te_override is not None:
        te_percent[target_type_id] = te_override

    # Per-activity facility material factors for the walk.
    material_factors: dict[str, tuple[float, float]] = {}
    for activity_key in ("manufacturing", "reactions"):
        facility = facilities.get(activity_key)
        material_factors[activity_key] = (
            facility_material_multiplier(
                facility.structure_type if facility else "station"
            ),
            rig_percent(facility, "me"),
        )

    result = resolve_chain(
        target_type_id,
        units,
        catalog,
        adjustments=ChainAdjustments(
            me_percent=me_percent, material_factors=material_factors
        ),
    )

    # Shared enrichment reads: skills, prices, cost indices, raw
    # categories, and the pool's on-hand stock — one batch each.
    skills_by_bp = await activity_skills(
        db,
        list({header.blueprint_type_id for header in catalog.headers.values()}),
    )
    price_ids = list(
        {
            demand.type_id
            for node in result.buildable_nodes
            for demand in node.demands
        }
    )
    prices = await adjusted_prices(db, price_ids)
    index_cache: dict[str, float | None] = {}
    for activity_key in ("manufacturing", "reactions"):
        facility = facilities.get(activity_key)
        index_cache[activity_key] = await cost_index(
            db, facility.system_id if facility else None, activity_key
        )
    terminator_ids = [
        demand.type_id
        for node in result.buildable_nodes
        for demand in node.demands
        if demand.type_id not in catalog.headers
    ]
    # invGroups classification for both the terminators (the
    # acquisition table's categories) and the buildable nodes (the
    # phase display names) — one read.
    classified = await material_categories(
        db,
        list(
            dict.fromkeys(
                terminator_ids + [node.type_id for node in result.buildable_nodes]
            )
        ),
    )
    measured_ids = list(
        dict.fromkeys(
            [node.type_id for node in result.buildable_nodes]
            + [row.type_id for row in result.raw_totals]
        )
    )
    on_hand = await pool_on_hand(
        db,
        measured_ids,
        participant_ids=pool_ids,
        corporation_id=corporation_id,
        include_personal=include_personal_stock,
    )
    for row in result.raw_totals:
        row.on_hand = on_hand.get(row.type_id, 0)
        category, group = classified.get(row.type_id, (None, None))
        row.category_name = category
        row.group_name = group

    def _gate_holders(required: list) -> list[int]:
        return [
            character_id
            for character_id in pool_ids
            if all(
                levels.get(character_id, {}).get(skill.skill_id, 0) >= skill.level
                for skill in required
            )
        ]

    for node in result.buildable_nodes:
        header = catalog.headers[node.type_id]
        node.group_name = classified.get(node.type_id, (None, None))[1]
        owned = owned_map.get(header.blueprint_type_id, [])
        selected = selected_by_type[node.type_id]
        has_original = selected is not None and selected.is_original
        activity_key = SDE_ACTIVITY_KEYS.get(header.activity_id, "manufacturing")
        facility = facilities.get(activity_key)
        structure_type = facility.structure_type if facility else "station"
        rig_te = rig_percent(facility, "te")
        required = skills_by_bp.get((header.blueprint_type_id, header.activity_id), [])
        holders = _gate_holders(required)
        best_multiplier = min(
            (
                skill_time_multiplier(activity_key, levels.get(character_id, {}))
                for character_id in holders
            ),
            default=1.0,
        )

        materials: list[PlanMaterial] = []
        base_quantities: dict[int, int] = {}
        has_buildable_inputs = False
        inputs_ready = True
        for demand in node.demands:
            buildable = demand.type_id in catalog.headers
            category = group = None
            if buildable:
                has_buildable_inputs = True
            else:
                category, group = classified.get(demand.type_id, (None, None))
                if on_hand.get(demand.type_id, 0) < demand.required_qty:
                    inputs_ready = False
            materials.append(
                PlanMaterial(
                    type_id=demand.type_id,
                    name=catalog.names.get(demand.type_id, f"#{demand.type_id}"),
                    base_qty=demand.base_qty,
                    required_qty=demand.required_qty,
                    buildable=buildable,
                    category_name=category,
                    group_name=group,
                )
            )
            base_quantities[demand.type_id] = demand.base_qty * node.runs

        per_job = (
            job_time_seconds(
                header.duration_seconds,
                min(node.runs, header.max_production_limit or node.runs),
                te_percent=te_percent.get(node.type_id, 0),
                structure_type=structure_type,
                activity_key=activity_key,
                rig_te_percent=rig_te,
                skill_multiplier=best_multiplier,
            )
            if header.duration_seconds
            else 0
        )
        node.calc = NodeCalculation(
            me=me_percent.get(node.type_id, 0),
            te=te_percent.get(node.type_id, 0),
            selected=selected,
            has_original=has_original,
            bpc_pool_runs=None if has_original else bpc_pool_runs(owned),
            materials=materials,
            base_quantities=base_quantities,
            job_seconds=per_job,
            total_seconds=per_job * node.jobs,
            install=install_cost(
                base_quantities,
                prices,
                system_index=index_cache.get(activity_key),
                structure_type=structure_type,
                tax_rate=facility.tax_rate if facility else None,
            ),
            holds_gate=bool(holders),
            on_hand=on_hand.get(node.type_id),
            coverage=(on_hand.get(node.type_id, 0) / node.qty) if node.qty else None,
            has_buildable_inputs=has_buildable_inputs,
            inputs_ready=inputs_ready,
        )

    # Per-participant chain readouts: multipliers, gate coverage, and
    # the solo serial time over the nodes their skills allow.
    participant_rows: list[ChainParticipantTime] = []
    for character_id in pool_ids:
        char_levels = levels.get(character_id, {})
        gated = 0
        gated_seconds = 0
        for node in result.buildable_nodes:
            header = catalog.headers[node.type_id]
            required = skills_by_bp.get(
                (header.blueprint_type_id, header.activity_id), []
            )
            if not all(
                char_levels.get(skill.skill_id, 0) >= skill.level
                for skill in required
            ):
                continue
            gated += 1
            activity_key = SDE_ACTIVITY_KEYS.get(header.activity_id, "manufacturing")
            facility = facilities.get(activity_key)
            per_job = (
                job_time_seconds(
                    header.duration_seconds,
                    min(node.runs, header.max_production_limit or node.runs),
                    te_percent=te_percent.get(node.type_id, 0),
                    structure_type=(
                        facility.structure_type if facility else "station"
                    ),
                    activity_key=activity_key,
                    rig_te_percent=rig_percent(facility, "te"),
                    skill_multiplier=skill_time_multiplier(activity_key, char_levels),
                )
                if header.duration_seconds
                else 0
            )
            gated_seconds += per_job * node.jobs
        target_header = catalog.headers[target_type_id]
        target_required = skills_by_bp.get(
            (target_header.blueprint_type_id, target_header.activity_id), []
        )
        missing = [
            skill.name
            for skill in target_required
            if char_levels.get(skill.skill_id, 0) < skill.level
        ]
        participant_rows.append(
            ChainParticipantTime(
                character_id=character_id,
                name=roster_names.get(character_id, f"Character #{character_id}"),
                multipliers={
                    activity_key: skill_time_multiplier(activity_key, char_levels)
                    for activity_key in ("manufacturing", "reactions")
                },
                nodes_gated=gated,
                gated_total_seconds=gated_seconds,
                holds_target_gate=not missing,
                missing_target_skills=missing,
            )
        )

    # Copy time for the target's blueprint at the copy facility (M4's
    # readout, unchanged: best pool multiplier, hull time only).
    target_header = catalog.headers[target_type_id]
    target_node = result.target_node
    copy_facility = facilities.get("copying")
    copy_seconds_per_run: int | None = None
    copy_total_seconds: int | None = None
    if target_header.copy_duration_seconds:
        best_multiplier = min(
            (
                skill_time_multiplier("copying", levels.get(character_id, {}))
                for character_id in pool_ids
            ),
            default=1.0,
        )
        copy_structure = (
            copy_facility.structure_type if copy_facility else "station"
        )
        copy_seconds_per_run = copy_time_seconds(
            target_header.copy_duration_seconds,
            1,
            structure_type=copy_structure,
            skill_multiplier=best_multiplier,
        )
        copy_total_seconds = copy_time_seconds(
            target_header.copy_duration_seconds,
            target_node.runs or 1,
            structure_type=copy_structure,
            skill_multiplier=best_multiplier,
        )

    for cut in result.cycles:
        cut.consumer_name = catalog.names.get(cut.consumer_type_id)
        cut.material_name = catalog.names.get(cut.material_type_id)

    return ChainPlan(
        chain=result,
        participants=participant_rows,
        target_owned=owned_map.get(target_header.blueprint_type_id, []),
        copy_facility=copy_facility,
        copy_seconds_per_run=copy_seconds_per_run,
        copy_total_seconds=copy_total_seconds,
    )
