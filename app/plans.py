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

import json
from dataclasses import asdict
from urllib.parse import urlencode

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import utc_now
from .facilities import (
    ACTIVITIES,
    RegistrationRow,
    activity_registrations,
    default_facilities,
)
from .industry import activity_skills
from .models import BuildPlan, BuildPlanMaterial, BuildPlanNode, Character
from .planner import ChainPlan, fresh_node_state

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
    the largest node's own name), and the worst-child state rollup."""
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
                "state": (
                    "ready"
                    if all(node.state == "ready" for node in phase_nodes)
                    else "missing"
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
