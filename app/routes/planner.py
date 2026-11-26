"""Planner section (M4/M5): the commodity-first planner entry and its
resolved-chain build plan.

Stateless by design — the whole planner input set (target, count,
participants, facilities, ME/TE overrides) lives in URL query params;
the one write is M6's export POST (app/routes/plans.py), whose form
serializes this same state. Param semantics, chosen once:

- `target` (type id) — invalid ids redirect to the bare planner.
- `qty` — target units, server-clamped to ≥ 1.
- `owned` — the Match From Inventory toggle on the search.
- `me` / `te` — ME/TE overrides; ABSENT means derived from the best
  owned blueprint (the flagged M4 decision; there is no mockup control
  for these — they exist for hand-checking the math). The overrides
  apply to the TARGET node only.
- `p` — participant character ids, repeatable. ABSENT means the
  default pool (the main's corporation's members); PRESENT — even
  empty (`?p=`) — is an explicit pool. Links never serialize the
  default set, so a roster change re-resolves honestly.
- `src` — material source refs, repeatable (the Material sources
  selector); absent means the corp-side default, present-even-empty an
  explicit set.
- `manufacturing` / `copying` / `invention` / `reactions` — facility
  registration ids; absent means the registry default (with copying
  falling back to invention's), so a registry edit re-resolves too.
- `all` (plan page) — the acquisition table's show-all toggle; absent
  means the gaps-only default.
- `from_plan` (plan page) — the Re-run fork context: the plan id a
  save from this page supersedes (transient, never serialized into
  snapshots).

Renders stay DB-pure; the one JSON endpoint is the search type-ahead.
Both pages swap `<main>` in place (static/planner.js, the structures
conventions).
"""

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select

from ..deps import DbDep, is_authenticated
from ..facilities import (
    ACTIVITIES,
    ACTIVITY_LABELS,
    STRUCTURE_TYPES,
    effective_rig_percent,
)
from ..industry import (
    catalog_size,
    search_catalog,
    type_names,
)
from ..models import Character, UniverseCorporation, UniverseLocation
from ..planner import (
    ChainPlan,
    ChainResult,
    chain_plan,
    facility_time_multiplier,
    fresh_node_state,
    phase_state,
)
from ..plans import (
    RAW_ACQUIRE,
    REASON_TEXT,
    lp_acquisition,
    lp_gate_text,
    parse_material_sources,
    planner_state,
    raw_label,
    state_pairs,
    state_qs,
)
from ..templates import templates

router = APIRouter()

# Node activity → the mockup's activity-tag class and text.
_ACTIVITY_TAGS = {1: ("mfg", "manufacture"), 11: ("rxn", "reaction")}


async def _labeled_sources(db: DbDep, plan: ChainPlan | None) -> list[dict]:
    """The chain's relevant material sources (only those holding
    measured types — a roster spans dozens of locations), labeled and
    carrying their per-type quantities and selection state. Both the
    planner's Material sources section and the plan page's acquisition
    breakdown read this one shape."""
    if plan is None or not plan.source_stock:
        return []
    location_ids = {
        source.location_id for source in plan.source_stock if source.location_id
    }
    location_names: dict[int, str | None] = {}
    if location_ids:
        location_names = dict(
            (
                await db.execute(
                    select(
                        UniverseLocation.location_id, UniverseLocation.name
                    ).where(UniverseLocation.location_id.in_(location_ids))
                )
            ).all()
        )
    container_type_ids = {
        source.container_type_id
        for source in plan.source_stock
        if source.container_type_id
    }
    container_names = (
        await type_names(db, list(container_type_ids))
        if container_type_ids
        else {}
    )
    participant_names = {
        row.character_id: row.name for row in plan.participants
    }
    all_mode = plan.material_source_refs is None
    selected = set(plan.material_source_refs or [])
    # Default mode: corp-side sources (offices, containers) count;
    # personal hangars render uncounted until chipped in.
    default_counts = {"office", "container"}

    labeled = []
    for source in plan.source_stock:
        location = location_names.get(source.location_id) or str(
            source.location_id
        )
        if source.kind == "office":
            label = location
        elif source.kind == "container":
            type_name = container_names.get(
                source.container_type_id, f"Type {source.container_type_id}"
            )
            label = f"{type_name} · {location}"
        else:
            who = participant_names.get(
                source.character_id, str(source.character_id)
            )
            label = f"{who} · {location}"
        labeled.append(
            {
                "ref": source.ref,
                "kind": source.kind,
                "label": label,
                "selected": (
                    source.kind in default_counts if all_mode
                    else source.ref in selected
                ),
                "quantities": source.quantities,
            }
        )
    return labeled


def _source_groups(labeled: list[dict]) -> list[dict]:
    """The Material sources section's chip groups: offices, containers,
    personal hangars."""
    groups: dict[str, list[dict]] = {}
    for source in labeled:
        groups.setdefault(source["kind"], []).append(source)
    order = [
        ("office", "Corp office hangars"),
        ("container", "Containers in corp hangars"),
        ("hangar", "Personal hangars"),
    ]
    return [
        {"label": group_label, "views": groups[kind]}
        for kind, group_label in order
        if groups.get(kind)
    ]


def _stock_lines(plan: ChainPlan, labeled: list[dict]) -> dict[int, list[dict]]:
    """Per-type stock breakdown for the acquisition table: where each
    measured type's on-hand stock sits (label + quantity + whether the
    selection counts it), so material moving is visible regardless of
    what the meters measure."""
    by_ref = {source["ref"]: source for source in labeled}
    lines: dict[int, list[dict]] = {}
    for source in plan.source_stock:
        view = by_ref.get(source.ref)
        if view is None:
            continue
        for type_id, quantity in source.quantities.items():
            lines.setdefault(type_id, []).append(
                {
                    "label": view["label"],
                    "qty": quantity,
                    "counted": view["selected"],
                }
            )
    for type_lines in lines.values():
        type_lines.sort(key=lambda line: -line["qty"])
    return lines


def _phase_views(chain: ChainResult) -> list[dict]:
    """The phase tree's view models: one entry per phase that holds
    buildable nodes (the all-raw level is the acquisition table's
    story), each node carrying its computed stage state and gating
    text. Phases count up in build order."""
    views = []
    for phase in chain.phases:
        buildables = [node for node in phase.nodes if node.buildable]
        if not buildables:
            continue
        nodes = []
        for node in sorted(buildables, key=lambda n: n.name):
            state, reason = fresh_node_state(node)
            gating = None
            if reason == "waiting-upstream":
                gating = REASON_TEXT[reason].format(phase=node.phase - 1)
            elif reason == "blueprint-missing" and lp_gate_text(
                node.blueprint_type_id
            ):
                gating = lp_gate_text(node.blueprint_type_id)
            elif reason:
                gating = REASON_TEXT.get(reason, reason)
            nodes.append(
                {
                    "node": node,
                    "state": state,
                    "reason": reason,
                    "gating": gating,
                    "tag": _ACTIVITY_TAGS.get(node.activity_id, ("mfg", "manufacture")),
                }
            )
        # The phase's display name: the modal invGroups name among its
        # buildables (the owner's call over a commodity name — groups
        # describe what a phase produces); ties break to the larger
        # requirement, then the name. Types the mirror leaves groupless
        # fall back to the largest node's own name.
        group_counts: dict[str, tuple[int, int, str]] = {}
        for node in buildables:
            label = node.group_name or node.name
            count, qty, _name = group_counts.get(label, (0, 0, label))
            group_counts[label] = (count + 1, max(qty, node.qty), label)
        name = max(
            group_counts,
            key=lambda label: (group_counts[label][0], group_counts[label][1]),
        )
        if not any(node.group_name for node in buildables):
            name = max(buildables, key=lambda n: n.qty).name
        views.append(
            {
                "phase": phase,
                "state": phase_state(phase),
                "nodes": nodes,
                "activity_tags": sorted(
                    {
                        _ACTIVITY_TAGS.get(node.activity_id, ("mfg", "manufacture"))
                        for node in buildables
                    }
                ),
                "name": name,
            }
        )
    return views


def _raw_groups(chain: ChainResult) -> list[tuple[str, list[dict]]]:
    """The acquisition table's grouping: chain terminators by display
    label, largest requirement first within each group, each row
    carrying its meter class and gap (the mockup's gaps-only default
    hides covered rows)."""
    groups: dict[str, list[dict]] = {}
    for row in chain.raw_totals:
        label = raw_label(row.category_name, row.group_name, row.name)
        on_hand = row.on_hand or 0
        if on_hand >= row.qty:
            meter = "full"
        elif on_hand * 2 >= row.qty:
            meter = "warn"
        else:
            meter = "low"
        groups.setdefault(label, []).append(
            {
                "row": row,
                "label": label,
                "on_hand": on_hand,
                "pct": min(100, int(100 * on_hand / row.qty)) if row.qty else 0,
                "meter": meter,
                "gap": max(0, row.qty - on_hand),
                "acquire": RAW_ACQUIRE.get(label, "Market"),
            }
        )
    return sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))


def _blueprint_views(chain: ChainResult) -> dict:
    """The chain-wide blueprint overlay: the owned summary plus the
    exceptions (no original — missing entirely or BPC-only with the
    run-coverage shortfall)."""
    nodes = sorted(chain.buildable_nodes, key=lambda n: n.name)
    owned = sum(1 for node in nodes if node.calc and node.calc.selected is not None)
    with_originals = sum(
        1 for node in nodes if node.calc and node.calc.has_original
    )
    exceptions = []
    for node in nodes:
        calc = node.calc
        if calc is None or calc.has_original:
            continue
        exceptions.append(
            {
                "node": node,
                "status": "missing" if calc.selected is None else "bpc",
                "shortfall": (
                    None
                    if calc.bpc_pool_runs is None
                    else max(0, (node.runs or 0) - calc.bpc_pool_runs)
                ),
            }
        )
    return {
        "total": len(nodes),
        "owned": owned,
        "with_originals": with_originals,
        "exceptions": exceptions,
    }


def _multiplies_lines(
    plan: ChainPlan, chosen: dict[str, object | None]
) -> list[dict]:
    """The 'This plan multiplies' readout's computed slots, per walk
    activity with a chosen facility: the rig and hull numbers behind
    the material, time, and install-cost math."""
    lines = []
    for activity in ("manufacturing", "reactions"):
        facility = chosen.get(activity)
        if facility is None:
            continue
        lines.append(
            {
                "activity": activity,
                "activity_label": ACTIVITY_LABELS[activity],
                "facility": facility,
                "rig_me": effective_rig_percent(
                    activity, "me", facility.me_rig, facility.security_class or ""
                ),
                "rig_te": effective_rig_percent(
                    activity, "te", facility.te_rig, facility.security_class or ""
                ),
                "hull_time": facility_time_multiplier(
                    facility.structure_type, activity
                ),
                "security": facility.security_class,
                "index": plan.chain.target_node.calc.install.system_index
                if activity == "manufacturing"
                else None,
            }
        )
    return lines


@router.get("/planner")
async def planner_page(
    request: Request,
    db: DbDep,
    target: int | None = None,
    qty: int = 1,
    owned: bool = False,
    me: int | None = None,
    te: int | None = None,
    from_plan: str = "",
):
    """The planner entry: search + target + participants + facilities +
    the full-chain requirement tiers (blueprints, intermediates by
    phase, raw terminators by category) + the owned-copies overlay.
    The sell-side market selector is omitted until M15's market manager
    exists (settled scope). `from_plan` is the Re-run fork context —
    carried into Calculate so a save from the visit supersedes that
    plan."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    qty = max(1, qty or 1)

    # Roster: the main's corporation scopes the member set (the
    # participants decision of record); other-corporation characters
    # are listed per plan.
    characters = (
        (await db.execute(select(Character).order_by(Character.name)))
        .scalars()
        .all()
    )
    main = next((c for c in characters if c.is_main), None)
    corp_id = main.corporation_id if main else None
    corp_name = None
    if corp_id is not None:
        corp_name = (
            await db.execute(
                select(UniverseCorporation.name).where(
                    UniverseCorporation.corporation_id == corp_id
                )
            )
        ).scalar_one_or_none()
    corp_members = [c for c in characters if c.corporation_id == corp_id]
    others = [c for c in characters if c.corporation_id != corp_id]

    participants, registrations, chosen, defaults = await planner_state(
        db, request.query_params
    )
    material_sources = parse_material_sources(request.query_params)

    # The target: an invalid id bounces to the bare planner (search
    # only offers catalog products, so this is a stale or hand-built
    # link, not a missing feature).
    plan: ChainPlan | None = None
    if target is not None:
        plan = await chain_plan(
            db,
            target_type_id=target,
            units=qty,
            participants=participants,
            facilities=chosen,
            me_override=me,
            te_override=te,
            material_sources=material_sources,
        )
        if plan is None:
            return RedirectResponse("/planner", status_code=302)

    state_query = state_qs(
        target, qty, participants, chosen, defaults, me, te, owned,
        material_sources,
    )
    labeled_sources = await _labeled_sources(db, plan)
    # Calculate carries the fork context so a save from a Re-run visit
    # supersedes the source plan.
    calculate_href = "/planner/plan" + state_query
    if from_plan.strip().isdigit():
        calculate_href += f"{'&' if state_query else '?'}from_plan={int(from_plan)}"
    return templates.TemplateResponse(
        request,
        "planner.html",
        {
            "authenticated": True,
            "active": "planner",
            "catalog_count": await catalog_size(db),
            "target": target,
            "qty": qty,
            "owned": owned,
            "material_sources": material_sources,
            "source_groups": _source_groups(labeled_sources),
            "me_override": me,
            "te_override": te,
            "plan": plan,
            "chain": plan.chain if plan else None,
            "phase_views": _phase_views(plan.chain) if plan else [],
            "raw_groups": _raw_groups(plan.chain) if plan else [],
            "blueprints": _blueprint_views(plan.chain) if plan else None,
            "multiplies": _multiplies_lines(plan, chosen) if plan else [],
            "calculate_href": calculate_href,
            "main": main,
            "corp_id": corp_id,
            "corp_name": corp_name,
            "corp_members": corp_members,
            "other_characters": others,
            "participants": participants,
            "registrations": registrations,
            "chosen": chosen,
            "defaults": defaults,
            "activities": ACTIVITIES,
            "activity_labels": ACTIVITY_LABELS,
            "structure_types": STRUCTURE_TYPES,
        },
    )


@router.get("/planner/search")
async def planner_search(
    request: Request, db: DbDep, q: str = "", owned: bool = False
):
    """The autocomplete's JSON feed: catalog entries with the owned
    overlay counts the rows badge against."""
    if not is_authenticated(request):
        return JSONResponse({"entries": []}, status_code=403)
    entries = await search_catalog(db, q, limit=10, owned_only=owned)
    return JSONResponse(
        {
            "entries": [
                {
                    "type_id": entry.type_id,
                    "type_name": entry.type_name,
                    "group_name": entry.group_name,
                    "blueprint_type_id": entry.blueprint_type_id,
                    "blueprint_name": entry.blueprint_name,
                    "activity_label": entry.activity_label,
                    "products_per_run": entry.products_per_run,
                    "max_production_limit": entry.max_production_limit,
                    "owned_originals": entry.owned_originals,
                    "owned_copies": entry.owned_copies,
                }
                for entry in entries
            ]
        }
    )


@router.get("/planner/plan")
async def planner_plan_page(
    request: Request,
    db: DbDep,
    target: int | None = None,
    qty: int = 1,
    me: int | None = None,
    te: int | None = None,
    show_all: bool = Query(False, alias="all"),
    from_plan: str = "",
):
    """The calculated chain build plan (Calculate's destination): stat
    tiles, the chain-flow strip, the phase tree with stage states, the
    chain-wide blueprint overlay, the raw-material acquisition table
    with coverage meters (gaps-only by default), per-participant time,
    and the copy-time readout, and the Save-plan export form (M6).
    Wave bar, copy plan, market panel, and job allocation are their own
    milestones' surfaces. `from_plan` is the Re-run fork context: the
    plan id a save from this page supersedes."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    if target is None:
        return RedirectResponse("/planner", status_code=302)
    qty = max(1, qty or 1)
    participants, _registrations, chosen, defaults = await planner_state(
        db, request.query_params
    )
    material_sources = parse_material_sources(request.query_params)

    plan = await chain_plan(
        db,
        target_type_id=target,
        units=qty,
        participants=participants,
        facilities=chosen,
        me_override=me,
        te_override=te,
        material_sources=material_sources,
    )
    if plan is None:
        return RedirectResponse("/planner", status_code=302)

    state_query = state_qs(
        target, qty, participants, chosen, defaults, me, te,
        material_sources=material_sources,
    )
    # The fork context rides every link (the acquisition toggle, the
    # back-to-planner link, Calculate's round trips) so a save from a
    # Re-run visit keeps its source plan; a fresh visit never carries
    # it and never touches siblings.
    fork_id = int(from_plan) if from_plan.strip().isdigit() else None
    fork_qs = f"{'&' if state_query else '?'}from_plan={fork_id}" if fork_id else ""
    base_href = "/planner/plan" + state_query + fork_qs
    toggle_href = (
        base_href if show_all else base_href + ("&all=1" if state_query else "?all=1")
    )
    labeled_sources = await _labeled_sources(db, plan)
    raw_groups = _raw_groups(plan.chain)
    covered_count = sum(
        1 for _label, rows in raw_groups for row in rows if row["meter"] == "full"
    )
    target_node = plan.chain.target_node
    # The LP acquisition front: when the target's blueprint is
    # LP-store-only and none is owned, the acquisition table reads the
    # pooled participants' loyalty balances against the pinned offers.
    lp_view = None
    if target_node.calc is not None and target_node.calc.selected is None:
        lp_view = await lp_acquisition(
            db,
            target_node.blueprint_type_id or 0,
            [row.character_id for row in plan.participants],
            target_node.runs or 0,
        )
    return templates.TemplateResponse(
        request,
        "plan.html",
        {
            "authenticated": True,
            "active": "planner",
            "plan": plan,
            "chain": plan.chain,
            "phase_views": _phase_views(plan.chain),
            "raw_groups": raw_groups,
            "covered_count": covered_count,
            "blueprints": _blueprint_views(plan.chain),
            "show_all": show_all,
            "toggle_href": toggle_href,
            "planner_href": "/planner" + state_query + fork_qs,
            "qty": qty,
            "material_sources": material_sources,
            "source_groups": _source_groups(labeled_sources),
            "stock_lines": _stock_lines(plan, labeled_sources),
            "me_override": me,
            "te_override": te,
            # The export form: the URL state as hidden fields, the
            # prefilled default name, and the fork context.
            "export_pairs": state_pairs(
                target, qty, participants, chosen, defaults, me, te,
                material_sources=material_sources,
            ),
            "default_plan_name": f"{target_node.name} ×{qty:,}",
            "from_plan": fork_id,
            "lp_view": lp_view,
        },
    )
