"""Build-plan domain layer (M6): the snapshot writer that persists a
resolved chain as the plan of record, and the reads the Plans section
renders. Mirrors the industry-reads / planner-calc split — this module
owns plan semantics, not chain math:

- The planner-state helpers (participant/source parsing, facility
  resolution, URL serialization) live here because both the planner
  pages and the export POST consume them, and `source_query` — the
  Re-run button's target — is itself a plan fact.
- Raw-material display labels and the acquire-via pins are plan
  acquisition semantics (the curated "via which in-game mechanic"
  table); the planner pages import them.
- The snapshot is one transaction: columns for anything measured or
  mutated, JSON for pure display. Re-running the planner makes a NEW
  plan; only status, timestamps, and materialized columns ever move.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from urllib.parse import urlencode

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db import utc_now
from .facilities import (
    ACTIVITIES,
    RegistrationRow,
    activity_registrations,
    default_facilities,
)
from .industry import (
    active_skill_levels,
    activity_skills,
    material_source_stock,
    owned_blueprints_for_types,
)
from .models import (
    AssetSync,
    BuildPlan,
    BuildPlanJob,
    BuildPlanMaterial,
    BuildPlanNode,
    Character,
    IndustryJob,
    Structure,
)
from .planner import SDE_ACTIVITY_KEYS, ChainPlan, active_node_state, fresh_node_state

logger = logging.getLogger(__name__)

# Raw-material display labels: SDE category/group names pinned against
# the live mirror 2026-11-23, mapped to the mockup's tier-3 labels. The
# name-list fallback covers the SDE's known misfilings (Morphite — the
# top moon material, which the dump files under 'Mineral'; the
# reference model's lesson). Anything else falls back to its group or
# category name — honest to the SDE rather than guessed.
RAW_LABELS: dict[tuple[str | None, str | None], str] = {
    ("Material", "Mineral"): "Minerals",
    ("Material", "Moon Materials"): "Moon materials",
    ("Material", "Ice Product"): "Ice products",
    ("Celestial", "Harvestable Cloud"): "Gas (harvestable clouds)",
}
RAW_NAME_FALLBACK = {"Morphite": "Moon materials"}

# The acquisition-path text per raw label (a curated pin table — the
# milestone's "via which in-game mechanic"). Price figures stay out
# until M15's market data.
RAW_ACQUIRE: dict[str, str] = {
    "Minerals": "Mining / reprocessing / market",
    "Moon materials": "Moon mining / market",
    "Ice products": "Ice mining / market",
    "Gas (harvestable clouds)": "Gas site harvesting",
    "PI commodities": "Planetary industry / market",
}

# Stage-state reason → the static gating text (fixed template, computed
# slot values only — no scenario-composed sentences).
REASON_TEXT: dict[str, str] = {
    "cycle": "SDE self-reference — cut",
    "blueprint-missing": "blueprint not owned",
    "skill-gated": "no skilled character in the pool",
    "waiting-upstream": "waiting on phase {phase}",
    "stock-gap": "input stock short",
}

# The stage-state model's chip labels (static scaffolding — computed
# slots only, never scenario-composed sentences) and the worst-child
# rollup order for phase summaries: least advanced wins.
STAGE_TEXT: dict[str, str] = {
    "missing": "Missing inputs",
    "ready": "Ready to build",
    "running": "In progress",
    "deliver": "Ready to deliver",
    "complete": "Stage complete",
}
STAGE_ORDER: tuple[str, ...] = (
    "missing", "ready", "running", "deliver", "complete",
)


def stage_text(state: str) -> str:
    """A stage state's chip label."""
    return STAGE_TEXT.get(state, state)


def raw_label(category: str | None, group: str | None, name: str) -> str:
    """An acquisition row's tier-3 display label from its SDE
    classification."""
    if name in RAW_NAME_FALLBACK:
        return RAW_NAME_FALLBACK[name]
    if (category, group) in RAW_LABELS:
        return RAW_LABELS[(category, group)]
    if category == "Planetary Commodities":
        return "PI commodities"
    return group or category or "Other"


# --- Planner state (shared by the planner pages and the export POST) -------------


def parse_participants(params) -> list[int] | None:
    """`p` semantics: absent = the default pool; present (even empty)
    = an explicit one. Non-numeric values drop — the server stays
    authoritative over link construction."""
    if "p" not in params:
        return None
    return [
        int(value)
        for value in params.getlist("p")
        if value.strip().isdigit()
    ]


def parse_material_sources(params) -> list[str] | None:
    """`src` semantics (the Material sources selector): the source refs
    the coverage measurement counts from. Absent = all sources (the
    source-from-all default); present (even empty) = an explicit set —
    the same absent/empty sentinel `p` uses, because an explicitly
    empty selection (nothing counts) is a real state."""
    if "src" not in params:
        return None
    return [
        value for value in params.getlist("src") if value.strip()
    ]


async def planner_state(
    db: AsyncSession, params
) -> tuple[list[int] | None, dict[str, list], dict[str, object | None], dict]:
    """The facility and participant state both planner pages and the
    export POST share: every activity's registration list, the chosen
    registration (override where valid, else the registry default), and
    the defaults themselves (for serializing only real overrides).
    `params` is the request's query params or the export form's fields —
    the same names either way."""
    participants = parse_participants(params)
    registrations = {
        activity: await activity_registrations(db, activity)
        for activity in ACTIVITIES
    }
    defaults = await default_facilities(db)
    chosen: dict[str, object | None] = {}
    for activity in ACTIVITIES:
        raw = params.get(activity, "")
        chosen[activity] = None
        if raw.strip().isdigit():
            wanted = int(raw)
            chosen[activity] = next(
                (
                    row
                    for row in registrations[activity]
                    if row.registration_id == wanted
                ),
                None,
            )
        if chosen[activity] is None:
            chosen[activity] = defaults.get(activity)
    return participants, registrations, chosen, defaults


def state_pairs(
    target: int | None,
    qty: int,
    participants: list[int] | None,
    chosen: dict[str, object | None],
    defaults: dict | None = None,
    me: int | None = None,
    te: int | None = None,
    owned: bool = False,
    material_sources: list[str] | None = None,
) -> list[tuple[str, str]]:
    """The URL state both planner pages share, as param pairs (the
    export form serializes the same pairs as hidden fields): target,
    count, an explicit participant pool, the material-source selection,
    and facility overrides (only when they differ from the registry
    default — absence-means-default keeps links honest when the default
    changes), and ME/TE overrides."""
    params: list[tuple[str, str]] = []
    if target is not None:
        params.append(("target", str(target)))
    if qty != 1:
        params.append(("qty", str(qty)))
    if owned:
        params.append(("owned", "1"))
    if material_sources is not None:
        # The present-even-empty sentinel: an explicit empty selection
        # serializes as a bare src=.
        if material_sources:
            params.extend(("src", ref) for ref in material_sources)
        else:
            params.append(("src", ""))
    if participants is not None:
        params.extend(("p", str(pid)) for pid in participants)
    for activity in ACTIVITIES:
        row = chosen.get(activity)
        default_row = defaults.get(activity) if defaults else None
        if row is not None and (
            default_row is None or row.registration_id != default_row.registration_id
        ):
            params.append((activity, str(row.registration_id)))
    if me is not None:
        params.append(("me", str(me)))
    if te is not None:
        params.append(("te", str(te)))
    return params


def state_qs(
    target: int | None,
    qty: int,
    participants: list[int] | None,
    chosen: dict[str, object | None],
    defaults: dict | None = None,
    me: int | None = None,
    te: int | None = None,
    owned: bool = False,
    material_sources: list[str] | None = None,
) -> str:
    """state_pairs as a query string (empty string when stateless)."""
    params = state_pairs(
        target, qty, participants, chosen, defaults, me, te, owned,
        material_sources,
    )
    return ("?" + urlencode(params)) if params else ""


# --- The snapshot writer ---------------------------------------------------------


def _facility_pin(row: RegistrationRow | None) -> dict | None:
    """One activity's pinned registration facts: everything the plan
    detail renders and the job matcher correlates on, frozen at export —
    registry edits never move an existing plan."""
    if row is None:
        return None
    return {
        "registration_id": row.registration_id,
        "activity": row.activity,
        "structure_id": row.structure_id,
        "structure_name": row.structure_name,
        "structure_type": row.structure_type,
        "system_id": row.system_id,
        "system_name": row.system_name,
        "security_class": row.security_class,
        "me_rig": row.me_rig,
        "te_rig": row.te_rig,
        "tax_rate": row.tax_rate,
        "is_default": row.is_default,
        "supercapital_assembly": row.supercapital_assembly,
    }


async def snapshot_plan(
    db: AsyncSession,
    *,
    resolved: ChainPlan,
    facilities: dict[str, RegistrationRow | None],
    name: str,
    source_query: str,
    sources: list[str] | None,
    me_override: int | None = None,
    te_override: int | None = None,
    from_plan_id: int | None = None,
) -> BuildPlan:
    """Persist a resolved chain as the plan of record (one transaction;
    the caller commits). Snapshots the resolved participants and pinned
    facilities, every buildable node's identity/calc/materials/skills,
    the acquisition rows from the chain terminators, the copy readout,
    and the cycle cuts — and initializes the materialized columns from
    the export-time measurement (the same values the planner page
    showed; the refresh tick owns them from here on). `from_plan_id` is
    the one auto-abandon path: the Re-run fork marks that plan abandoned
    and superseded. Fresh exports never touch sibling plans."""
    chain = resolved.chain
    target = chain.target_node
    assert target.calc is not None  # chain_plan enriches every buildable

    main = (
        await db.execute(select(Character).where(Character.is_main))
    ).scalar_one_or_none()
    skills_by_bp = await activity_skills(
        db,
        list({node.blueprint_type_id for node in chain.buildable_nodes}),
    )
    now = utc_now()

    plan = BuildPlan(
        name=name[:200],
        target_type_id=target.type_id,
        target_name=target.name,
        units=chain.units,
        status="draft",
        corporation_id=main.corporation_id if main is not None else None,
        participants_json=json.dumps([asdict(row) for row in resolved.participants]),
        sources_json=(
            json.dumps(sources) if sources is not None else None
        ),
        facilities_json=json.dumps(
            {activity: _facility_pin(facilities.get(activity))
             for activity in ACTIVITIES}
        ),
        me_override=me_override,
        te_override=te_override,
        source_query=source_query,
        copy_seconds_per_run=resolved.copy_seconds_per_run,
        copy_total_seconds=resolved.copy_total_seconds,
        copy_facility_json=(
            json.dumps(_facility_pin(resolved.copy_facility))
            if resolved.copy_facility is not None
            else None
        ),
        cycles_json=json.dumps([asdict(cut) for cut in chain.cycles]),
    )
    db.add(plan)
    await db.flush()  # plan.id for the node rows and the fork pointer

    for node in chain.buildable_nodes:
        calc = node.calc
        assert calc is not None
        state, reason = fresh_node_state(node)
        skills = [
            {"skill_id": skill.skill_id, "name": skill.name, "level": skill.level}
            for skill in skills_by_bp.get(
                (node.blueprint_type_id, node.activity_id), []
            )
        ]
        db.add(
            BuildPlanNode(
                plan_id=plan.id,
                phase=node.phase,
                type_id=node.type_id,
                name=node.name,
                group_name=node.group_name,
                qty=node.qty,
                runs=node.runs or 0,
                jobs=node.jobs,
                activity_id=node.activity_id or 0,
                blueprint_type_id=node.blueprint_type_id or 0,
                blueprint_name=node.blueprint_name,
                products_per_run=node.products_per_run,
                max_production_limit=node.max_production_limit,
                is_target=node.is_target,
                me=calc.me,
                te=calc.te,
                has_original=calc.has_original,
                bpc_pool_runs=calc.bpc_pool_runs,
                blueprint_owner_name=(
                    calc.selected.owner_name if calc.selected else None
                ),
                blueprint_location_name=(
                    calc.selected.location_name if calc.selected else None
                ),
                job_seconds=calc.job_seconds,
                total_seconds=calc.total_seconds,
                install_json=json.dumps(asdict(calc.install)),
                holds_gate=calc.holds_gate,
                skills_json=json.dumps(skills),
                materials_json=json.dumps([asdict(m) for m in calc.materials]),
                sourcing="build",
                available_qty=calc.on_hand or 0,
                delivered_qty=0,
                running_qty=0,
                state=state,
                state_reason=reason,
            )
        )

    for row in chain.raw_totals:
        label = raw_label(row.category_name, row.group_name, row.name)
        db.add(
            BuildPlanMaterial(
                plan_id=plan.id,
                type_id=row.type_id,
                name=row.name,
                category_name=row.category_name,
                group_name=row.group_name,
                is_purchase_line=False,
                required_qty=row.qty,
                acquire_via=RAW_ACQUIRE.get(label, "Market"),
                available_qty=row.on_hand or 0,
            )
        )

    # The Re-run fork: the one auto-abandon path. An unknown or terminal
    # source plan degrades to a fresh export.
    if from_plan_id is not None:
        source = await db.get(BuildPlan, from_plan_id)
        if source is not None and source.status in ("draft", "active"):
            source.superseded_by_plan_id = plan.id
            source.status = "abandoned"
            source.abandoned_at = now
    return plan


# --- Reads (DB-pure; pages never re-run the resolver) ----------------------------


async def plans_overview(db: AsyncSession) -> list[dict]:
    """The list page's rows: plans newest first with their snapshot
    counts (nodes, phases, acquisition types)."""
    plans = (
        (
            await db.execute(
                select(BuildPlan).order_by(
                    BuildPlan.created_at.desc(), BuildPlan.id.desc()
                )
            )
        )
        .scalars()
        .all()
    )
    node_counts: dict[int, tuple[int, int]] = {
        plan_id: (nodes, phases)
        for plan_id, nodes, phases in (
            await db.execute(
                select(
                    BuildPlanNode.plan_id,
                    func.count(),
                    func.count(func.distinct(BuildPlanNode.phase)),
                ).group_by(BuildPlanNode.plan_id)
            )
        ).all()
    }
    delivered_counts: dict[int, int] = {
        plan_id: count
        for plan_id, count in (
            await db.execute(
                select(
                    BuildPlanNode.plan_id, func.count()
                ).where(BuildPlanNode.delivered_qty >= BuildPlanNode.qty)
                .group_by(BuildPlanNode.plan_id)
            )
        ).all()
    }
    material_counts: dict[int, int] = {
        plan_id: count
        for plan_id, count in (
            await db.execute(
                select(
                    BuildPlanMaterial.plan_id, func.count()
                ).group_by(BuildPlanMaterial.plan_id)
            )
        ).all()
    }
    return [
        {
            "plan": plan,
            "nodes": node_counts.get(plan.id, (0, 0))[0],
            "phases": node_counts.get(plan.id, (0, 0))[1],
            "materials": material_counts.get(plan.id, 0),
            "delivered": delivered_counts.get(plan.id, 0),
        }
        for plan in plans
    ]


async def plan_read(
    db: AsyncSession, plan_id: int
) -> tuple[BuildPlan, list[BuildPlanNode], list[BuildPlanMaterial]] | None:
    """The detail page's rows: the plan, its nodes (phase, then name),
    and its acquisition lines."""
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return None
    nodes = (
        (
            await db.execute(
                select(BuildPlanNode)
                .where(BuildPlanNode.plan_id == plan_id)
                .order_by(BuildPlanNode.phase, BuildPlanNode.name)
            )
        )
        .scalars()
        .all()
    )
    materials = (
        (
            await db.execute(
                select(BuildPlanMaterial)
                .where(BuildPlanMaterial.plan_id == plan_id)
                .order_by(BuildPlanMaterial.name)
            )
        )
        .scalars()
        .all()
    )
    return plan, nodes, materials


def phase_views(nodes: list[BuildPlanNode]) -> list[dict]:
    """The detail page's phase tree: one entry per phase holding nodes,
    the modal invGroups display name (the planner's rule — ties break to
    the larger requirement, then the name; groupless phases fall back to
    the largest node's own name), and the worst-child state rollup over
    the full stage-state ladder (least advanced wins)."""
    by_phase: dict[int, list[BuildPlanNode]] = {}
    for node in nodes:
        by_phase.setdefault(node.phase, []).append(node)
    views = []
    for phase in sorted(by_phase):
        phase_nodes = sorted(by_phase[phase], key=lambda n: n.name)
        group_counts: dict[str, tuple[int, int, str]] = {}
        for node in phase_nodes:
            label = node.group_name or node.name
            count, qty, _name = group_counts.get(label, (0, 0, label))
            group_counts[label] = (count + 1, max(qty, node.qty), label)
        name = max(
            group_counts,
            key=lambda label: (group_counts[label][0], group_counts[label][1]),
        )
        if not any(node.group_name for node in phase_nodes):
            name = max(phase_nodes, key=lambda n: n.qty).name
        activity_ids = sorted({node.activity_id for node in phase_nodes})
        views.append(
            {
                "phase": phase,
                "nodes": phase_nodes,
                "name": name,
                "state": min(
                    (node.state for node in phase_nodes),
                    key=lambda state: (
                        STAGE_ORDER.index(state)
                        if state in STAGE_ORDER
                        else 0
                    ),
                ),
                "activity_ids": activity_ids,
            }
        )
    return views


def material_groups(
    materials: list[BuildPlanMaterial],
) -> list[tuple[str, list[dict]]]:
    """The acquisition table's grouping: rows by display label, largest
    requirement first within each group, each row carrying its meter
    class and gap (the gaps-only default hides covered rows)."""
    groups: dict[str, list[dict]] = {}
    for row in materials:
        label = raw_label(row.category_name, row.group_name, row.name)
        if row.available_qty >= row.required_qty:
            meter = "full"
        elif row.available_qty * 2 >= row.required_qty:
            meter = "warn"
        else:
            meter = "low"
        groups.setdefault(label, []).append(
            {
                "row": row,
                "on_hand": row.available_qty,
                "pct": (
                    min(100, int(100 * row.available_qty / row.required_qty))
                    if row.required_qty
                    else 0
                ),
                "meter": meter,
                "gap": max(0, row.required_qty - row.available_qty),
            }
        )
    return sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))


def gating_text(node: BuildPlanNode) -> str | None:
    """A node's gating reason as the static template text."""
    if node.state_reason is None:
        return None
    if node.state_reason == "waiting-upstream":
        return REASON_TEXT["waiting-upstream"].format(phase=node.phase - 1)
    return REASON_TEXT.get(node.state_reason, node.state_reason)


def pool_badge(plan: BuildPlan) -> str:
    """The read-only pool label: the snapshot's source set in badge form
    (the pool is structural — changing it goes through Re-run)."""
    if plan.sources_json is None:
        return "Corp offices"
    refs = json.loads(plan.sources_json)
    if any(ref.startswith("hangar:") for ref in refs):
        return "Corp + personal"
    return f"{len(refs)} source{'s' if len(refs) != 1 else ''}"


def status_badge(plan: BuildPlan) -> str:
    """The plan-state badge's class."""
    return {
        "draft": "plan-state",
        "active": "plan-state active",
        "complete": "owned",
        "abandoned": "missing",
    }.get(plan.status, "plan-state")


# --- Job correlation (M6 PR 6: the pure matcher + build_plan_jobs writes) --------

# ESI industry-job activity ids → the SDE recipe activity ids plan
# nodes carry. ESI reports reaction jobs under 9 (the ramActivities
# label) while the SDE dump files reaction recipes under 11 — this is
# the reconcile map the matcher joins across, verified against live
# corp jobs on the dev deployment 2026-11-25. Any other activity
# (copying, research, invention) matches nothing: build-plan nodes
# only ever carry 1 or 11.
ACTIVITY_RECONCILE: dict[int, int] = {1: 1, 9: 11, 11: 11}

# The job statuses that can carry a claim. cancelled/reverted are
# terminal failures; delivered still counts (delivery is the point).
CLAIMABLE_STATUSES = frozenset({"active", "paused", "ready", "delivered"})


@dataclass(frozen=True)
class PlanNodeRef:
    """One build_plan_nodes row as the matcher sees it: the identity
    keys plus the pinned facility's resolved sighting location — None
    when the structure is hand-entered (no location) or no facility is
    registered for the activity, in which case jobs at any location
    match (loosely — the documented failure mode)."""

    node_id: int
    phase: int
    blueprint_type_id: int
    activity_id: int
    facility_location_id: int | None


@dataclass(frozen=True)
class PlanRef:
    """One non-terminal plan as the matcher sees it."""

    plan_id: int
    created_at: datetime
    nodes: tuple[PlanNodeRef, ...]


@dataclass(frozen=True)
class JobClaim:
    """One job→node claim: the industry_jobs key plus the plan node it
    belongs to (the build_plan_jobs row's shape)."""

    plan_id: int
    node_id: int
    owner_type: str
    owner_id: int
    job_id: int


def correlate_jobs(plans: list[PlanRef], jobs: list[IndustryJob]) -> list[JobClaim]:
    """The heuristic matcher (PURE): which synced industry jobs belong
    to which plan nodes. The jobs endpoint carries no plan reference,
    so a job claims a node when its blueprint type and its ESI activity
    (reconciled to the SDE id) equal the node's, it started at or after
    the plan was exported (pre-export installs belong to a previous
    effort), and — only when the node's pinned facility resolved to a
    sighting location — it runs at that location. One claim per job
    GLOBALLY: plans walk oldest-first and nodes phase-ascending (build
    order), so a job matching several nodes lands on the oldest plan's
    earliest phase. False positives are accepted by design; there is no
    un-match UI in v1."""
    candidates = {
        blueprint_id: []
        for blueprint_id in (job.blueprint_type_id for job in jobs)
    }
    for job in jobs:
        if job.status in CLAIMABLE_STATUSES and job.start_date is not None:
            candidates[job.blueprint_type_id].append(job)

    claims: list[JobClaim] = []
    claimed: set[tuple[str, int, int]] = set()
    for plan in sorted(plans, key=lambda p: (p.created_at, p.plan_id)):
        for node in sorted(plan.nodes, key=lambda n: (n.phase, n.node_id)):
            for job in candidates.get(node.blueprint_type_id, ()):
                key = (job.owner_type, job.owner_id, job.job_id)
                if key in claimed:
                    continue
                if ACTIVITY_RECONCILE.get(job.activity_id) != node.activity_id:
                    continue
                if job.start_date < plan.created_at:
                    continue
                if (
                    node.facility_location_id is not None
                    and job.station_id != node.facility_location_id
                ):
                    continue
                claimed.add(key)
                claims.append(
                    JobClaim(
                        plan_id=plan.plan_id,
                        node_id=node.node_id,
                        owner_type=job.owner_type,
                        owner_id=job.owner_id,
                        job_id=job.job_id,
                    )
                )
    return claims


# The claims rewrite is serialized process-wide (the _sync_lock
# pattern): the tick's pass and a request-path refresh must never
# interleave their delete/insert cycles against the same unique key.
_claims_lock = asyncio.Lock()


async def refresh_job_claims(db: AsyncSession) -> list[JobClaim]:
    """One global correlation pass: load every non-terminal plan's
    nodes (their pinned facilities resolved to sighting locations) and
    every synced industry job, run the pure matcher, and rewrite
    build_plan_jobs wholesale. The pass is global so the one-claim rule
    holds across concurrent plans. The refresh tick (M6 PR 7) owns the
    cadence; nothing here mutates plans or nodes. The caller commits."""
    async with _claims_lock:
        return await _rewrite_job_claims(db)


async def _rewrite_job_claims(db: AsyncSession) -> list[JobClaim]:
    plans = (
        (
            await db.execute(
                select(BuildPlan)
                .where(BuildPlan.status.in_(("draft", "active")))
                .order_by(BuildPlan.created_at, BuildPlan.id)
            )
        )
        .scalars()
        .all()
    )
    nodes: list[BuildPlanNode] = []
    if plans:
        nodes = (
            (
                await db.execute(
                    select(BuildPlanNode)
                    .where(
                        BuildPlanNode.plan_id.in_([plan.id for plan in plans])
                    )
                    .order_by(BuildPlanNode.phase, BuildPlanNode.id)
                )
            )
            .scalars()
            .all()
        )

    # The pinned facilities' structure ids → sighting locations. A
    # structure without one (hand-entered, or since deleted) leaves its
    # nodes matching loosely.
    facilities_by_plan = {
        plan.id: json.loads(plan.facilities_json) for plan in plans
    }
    structure_ids = {
        pin["structure_id"]
        for pins in facilities_by_plan.values()
        for pin in pins.values()
        if pin
    }
    locations: dict[int, int | None] = {}
    if structure_ids:
        locations = dict(
            (
                await db.execute(
                    select(Structure.id, Structure.location_id).where(
                        Structure.id.in_(structure_ids)
                    )
                )
            ).all()
        )

    nodes_by_plan: dict[int, list[BuildPlanNode]] = {}
    for node in nodes:
        nodes_by_plan.setdefault(node.plan_id, []).append(node)
    refs = []
    for plan in plans:
        pins = facilities_by_plan[plan.id]
        plan_nodes = []
        for node in nodes_by_plan.get(plan.id, []):
            pin = pins.get(SDE_ACTIVITY_KEYS.get(node.activity_id, ""))
            plan_nodes.append(
                PlanNodeRef(
                    node_id=node.id,
                    phase=node.phase,
                    blueprint_type_id=node.blueprint_type_id,
                    activity_id=node.activity_id,
                    facility_location_id=(
                        locations.get(pin["structure_id"]) if pin else None
                    ),
                )
            )
        refs.append(
            PlanRef(
                plan_id=plan.id,
                created_at=plan.created_at,
                nodes=tuple(plan_nodes),
            )
        )

    jobs = (await db.execute(select(IndustryJob))).scalars().all()
    claims = correlate_jobs(refs, jobs)

    await db.execute(delete(BuildPlanJob))
    for claim in claims:
        db.add(
            BuildPlanJob(
                plan_id=claim.plan_id,
                node_id=claim.node_id,
                owner_type=claim.owner_type,
                owner_id=claim.owner_id,
                job_id=claim.job_id,
            )
        )
    return claims


# --- Progress refresh (M6 PR 7: the materialization tick + state machine) --------


async def plan_pool_on_hand(
    db: AsyncSession,
    plan: BuildPlan,
    nodes: list[BuildPlanNode],
    materials: list[BuildPlanMaterial],
) -> dict[int, int]:
    """Availability over the plan's pinned source set — the same
    measurement the planner page ran at export (material_source_stock
    plus the sources_json selection), re-run by the refresh tick
    against live assets. Reuses the M6 read rather than forking it;
    unheld types key zero, not absence."""
    participant_ids = [
        row["character_id"] for row in json.loads(plan.participants_json)
    ]
    measured = list(
        {node.type_id for node in nodes} | {row.type_id for row in materials}
    )
    sources = await material_source_stock(
        db,
        measured,
        corporation_id=plan.corporation_id,
        participant_ids=participant_ids,
    )
    if plan.sources_json is None:
        # The default: corp-side sources only (offices + containers);
        # personal hangars stayed out at export and stay out.
        counted = [source for source in sources if source.kind != "hangar"]
    else:
        selected = set(json.loads(plan.sources_json))
        counted = [source for source in sources if source.ref in selected]
    on_hand = {type_id: 0 for type_id in measured}
    for source in counted:
        for type_id, quantity in source.quantities.items():
            on_hand[type_id] += quantity
    return on_hand


async def refresh_plan(db: AsyncSession, plan: BuildPlan) -> BuildPlan:
    """Materialize one plan's progress (the tick's five steps): fresh
    availability over the pinned source set, delivery and running
    counts from the correlated jobs, node states through the
    active-state ladder, then the plan rollups and state machine.
    Assumes the correlation pass has already run — delivery reads the
    claims it wrote. Delivery is STICKY (recomputed, never lowered): a
    complete plan's claims drop out of the correlation pool, so its
    delivered ledger must not decay underneath it. The caller commits.
    """
    nodes = (
        (
            await db.execute(
                select(BuildPlanNode)
                .where(BuildPlanNode.plan_id == plan.id)
                .order_by(BuildPlanNode.phase, BuildPlanNode.id)
            )
        )
        .scalars()
        .all()
    )
    materials = (
        (
            await db.execute(
                select(BuildPlanMaterial).where(
                    BuildPlanMaterial.plan_id == plan.id
                )
            )
        )
        .scalars()
        .all()
    )

    # 1. Availability over the pinned source set, node and material
    # types together (delivered intermediates sit in the pool, so an
    # arrived input stops gating its consumer).
    on_hand = await plan_pool_on_hand(db, plan, nodes, materials)
    for row in nodes:
        row.available_qty = on_hand.get(row.type_id, 0)
    for row in materials:
        row.available_qty = on_hand.get(row.type_id, 0)

    # 2-4. Delivery, running, and the active-state ladder per node,
    # from the correlated jobs. delivered = min(qty, Σ successful_runs
    # × products_per_run over delivered jobs), never lowered (sticky);
    # running = Σ runs over active/paused jobs. The ladder's gating
    # rungs re-derive from fresh world state (the owner's 2026-11-25
    # call): pool blueprint existence for the node's blueprint type —
    # binary in v1, run-pool coverage arithmetic is the M8/M9 invention
    # layer — and the pinned participants' current skill levels against
    # the snapshotted requirements. The calc stays pinned: a mid-flight
    # acquisition with different ME/TE doesn't re-derive planned math.
    claims = (
        (
            await db.execute(
                select(BuildPlanJob).where(BuildPlanJob.plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )
    jobs_by_node: dict[int, list[IndustryJob]] = {}
    for claim in claims:
        job = await db.get(
            IndustryJob, (claim.owner_type, claim.owner_id, claim.job_id)
        )
        if job is not None:
            jobs_by_node.setdefault(claim.node_id, []).append(job)
    participant_ids = [
        row["character_id"] for row in json.loads(plan.participants_json)
    ]
    owned = await owned_blueprints_for_types(
        db, list({node.blueprint_type_id for node in nodes})
    )
    skill_levels = await active_skill_levels(db, participant_ids)
    for node in nodes:
        node_jobs = jobs_by_node.get(node.id, [])
        delivered = sum(
            (job.successful_runs or 0)
            for job in node_jobs
            if job.status == "delivered"
        )
        node.delivered_qty = max(
            node.delivered_qty, min(node.qty, delivered * node.products_per_run)
        )
        node.running_qty = sum(
            job.runs
            for job in node_jobs
            if job.status in ("active", "paused")
        )
        requirements = json.loads(node.skills_json)
        state, reason = active_node_state(
            node,
            on_hand,
            any(job.status == "ready" for job in node_jobs),
            has_blueprint=bool(owned.get(node.blueprint_type_id)),
            holds_gate=any(
                all(
                    levels.get(skill["skill_id"], 0) >= skill["level"]
                    for skill in requirements
                )
                for levels in skill_levels.values()
            ),
        )
        node.state = state
        node.state_reason = reason

    # 5. Plan rollups + the state machine. draft→active flips the first
    # time a job correlates (the export tooltip of record); active→
    # complete when every node is delivered (purchased nodes measure
    # availability instead — PR 8's markings). No transition touches
    # snapshot columns; abandoned is an owner action or the Re-plan
    # fork, never computed here.
    now = utc_now()
    if plan.status == "draft" and claims:
        plan.status = "active"
        plan.activated_at = now
    if plan.status == "active" and nodes and all(
        node.delivered_qty >= node.qty for node in nodes
    ):
        plan.status = "complete"
        plan.completed_at = now
    plan.refreshed_at = now
    plan.refresh_error = None
    return plan


async def refresh_plans_tick(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """One progress pass over every non-abandoned plan. Never raises:
    a plan the pass cannot refresh records refresh_error on its own
    session and the pass moves on (the world_sync_tick guarantee).
    Each plan refreshes in its OWN session — a mid-plan failure rolls
    back cleanly without poisoning the others."""
    try:
        async with session_factory() as db:
            await refresh_job_claims(db)
            await db.commit()
            plan_ids = [
                plan_id
                for (plan_id,) in (
                    await db.execute(
                        select(BuildPlan.id).where(
                            BuildPlan.status != "abandoned"
                        )
                    )
                ).all()
            ]
        for plan_id in plan_ids:
            try:
                async with session_factory() as db:
                    plan = await db.get(BuildPlan, plan_id)
                    if plan is None or plan.status == "abandoned":
                        continue
                    await refresh_plan(db, plan)
                    await db.commit()
            except Exception as exc:
                logger.warning(
                    "plan %s refresh failed: %s", plan_id, exc
                )
                try:
                    async with session_factory() as db:
                        plan = await db.get(BuildPlan, plan_id)
                        if plan is not None:
                            plan.refresh_error = str(exc)[:500]
                            await db.commit()
                except Exception:
                    logger.exception(
                        "plan %s refresh-error write failed", plan_id
                    )
    except Exception:
        logger.exception("plans refresh tick failed")


async def plans_refresh_loop(
    session_factory: async_sessionmaker[AsyncSession],
    settings,
) -> None:
    """The background progress refresh (world_sync_loop pattern): tick
    once shortly after startup — a restarted server converges without
    waiting out the interval — then every interval. DB-only reads, so
    a shorter cadence than the asset sync is cheap."""
    interval = settings.plans_refresh_interval_minutes * 60
    while True:
        await refresh_plans_tick(session_factory)
        await asyncio.sleep(interval)


# --- Progress reads (DB-pure surfaces) -------------------------------------------


async def assets_synced_at(db: AsyncSession) -> datetime | None:
    """The most recent asset-sync completion, any owner — the freshness
    stamp on the plan detail's availability figures."""
    return (
        await db.execute(select(func.max(AssetSync.synced_at)))
    ).scalar_one_or_none()


async def plan_job_views(
    db: AsyncSession, plan_id: int
) -> dict[int, dict]:
    """The detail page's per-node matched-jobs summaries — the eyeball
    surface for the correlation heuristic: installer names, run counts,
    statuses, and time-to-delivery (the latest end date among the
    node's in-flight jobs). Claims whose job left the sync window drop
    out (the next tick rewrites them away)."""
    rows = (
        await db.execute(
            select(BuildPlanJob, IndustryJob)
            .where(BuildPlanJob.plan_id == plan_id)
            .join(
                IndustryJob,
                (IndustryJob.owner_type == BuildPlanJob.owner_type)
                & (IndustryJob.owner_id == BuildPlanJob.owner_id)
                & (IndustryJob.job_id == BuildPlanJob.job_id),
            )
        )
    ).all()
    installer_ids = {job.installer_id for _claim, job in rows}
    names: dict[int, str] = {}
    if installer_ids:
        names = {
            character.character_id: character.name
            for character in (
                await db.execute(
                    select(Character).where(
                        Character.character_id.in_(installer_ids)
                    )
                )
            ).scalars()
        }
    views: dict[int, dict] = {}
    now = utc_now()
    for claim, job in rows:
        view = views.setdefault(
            claim.node_id,
            {"jobs": [], "installers": [], "deliver_in": None},
        )
        view["jobs"].append(job)
        installer = names.get(job.installer_id, f"#{job.installer_id}")
        if installer not in view["installers"]:
            view["installers"].append(installer)
        if job.status in ("active", "paused") and job.end_date is not None:
            remaining = (job.end_date - now).total_seconds()
            if view["deliver_in"] is None or remaining > view["deliver_in"]:
                view["deliver_in"] = remaining
    return views
