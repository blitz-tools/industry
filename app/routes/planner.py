"""Planner section (M4/M5): the commodity-first planner entry and its
resolved-chain build plan.

Stateless by design — the whole planner input set (target, count,
participants, facilities, ME/TE overrides) lives in URL query params and
nothing writes to the DB until M6 persists build plans. Param
semantics, chosen once:

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
- `manufacturing` / `copying` / `invention` / `reactions` — facility
  registration ids; absent means the registry default (with copying
  falling back to invention's), so a registry edit re-resolves too.
- `all` (plan page) — the acquisition table's show-all toggle; absent
  means the gaps-only default.

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
    activity_registrations,
    default_facilities,
    effective_rig_percent,
)
from ..industry import (
    catalog_size,
    search_catalog,
)
from ..models import Character, UniverseCorporation
from ..planner import (
    ChainPlan,
    ChainResult,
    chain_plan,
    facility_time_multiplier,
    fresh_node_state,
    phase_state,
)
from ..templates import templates

router = APIRouter()

# Raw-material display labels: SDE category/group names pinned against
# the live mirror 2026-11-23, mapped to the mockup's tier-3 labels. The
# name-list fallback covers the SDE's known misfilings (Morphite — the
# top moon material, which the dump files under 'Mineral'; the
# reference model's lesson). Anything else falls back to its group or
# category name — honest to the SDE rather than guessed.
_RAW_LABELS: dict[tuple[str | None, str | None], str] = {
    ("Material", "Mineral"): "Minerals",
    ("Material", "Moon Materials"): "Moon materials",
    ("Material", "Ice Product"): "Ice products",
    ("Celestial", "Harvestable Cloud"): "Gas (harvestable clouds)",
}
_RAW_NAME_FALLBACK = {"Morphite": "Moon materials"}

# The acquisition-path text per raw label (a curated pin table — the
# milestone's "via which in-game mechanic"). Price figures stay out
# until M15's market data.
_RAW_ACQUIRE: dict[str, str] = {
    "Minerals": "Mining / reprocessing / market",
    "Moon materials": "Moon mining / market",
    "Ice products": "Ice mining / market",
    "Gas (harvestable clouds)": "Gas site harvesting",
    "PI commodities": "Planetary industry / market",
}

# Node activity → the mockup's activity-tag class and text.
_ACTIVITY_TAGS = {1: ("mfg", "manufacture"), 11: ("rxn", "reaction")}

# Stage-state reason → the static gating text (fixed template, computed
# slot values only — no scenario-composed sentences).
_REASON_TEXT = {
    "cycle": "SDE self-reference — cut",
    "blueprint-missing": "blueprint not owned",
    "skill-gated": "no skilled character in the pool",
    "waiting-upstream": "waiting on phase {phase}",
    "stock-gap": "input stock short",
}


def _raw_label(category: str | None, group: str | None, name: str) -> str:
    if name in _RAW_NAME_FALLBACK:
        return _RAW_NAME_FALLBACK[name]
    if (category, group) in _RAW_LABELS:
        return _RAW_LABELS[(category, group)]
    if category == "Planetary Commodities":
        return "PI commodities"
    return group or category or "Other"


def _format_duration(seconds: int) -> str:
    """Seconds → the mockup's compact duration form (h / d)."""
    if seconds <= 0:
        return "—"
    hours = seconds / 3600
    if hours < 1:
        return f"{seconds}s"
    if hours < 48:
        value = f"{hours:.1f}".rstrip("0").rstrip(".")
        return f"{value} h"
    days = hours / 24
    value = f"{days:.1f}".rstrip("0").rstrip(".")
    return f"{value} d"


def _format_isk(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f} Ƶ"


def _format_qty(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _parse_participants(request: Request) -> list[int] | None:
    """`p` semantics: absent = the default pool; present (even empty)
    = an explicit one. Non-numeric values drop — the server stays
    authoritative over link construction."""
    if "p" not in request.query_params:
        return None
    return [
        int(value)
        for value in request.query_params.getlist("p")
        if value.strip().isdigit()
    ]


async def _planner_state(
    request: Request, db: DbDep
) -> tuple[list[int] | None, dict[str, list], dict[str, object | None], dict]:
    """The facility and participant state both pages share: every
    activity's registration list, the chosen registration (URL override
    where valid, else the registry default), and the defaults
    themselves (for serializing only real overrides)."""
    participants = _parse_participants(request)
    registrations = {
        activity: await activity_registrations(db, activity)
        for activity in ACTIVITIES
    }
    defaults = await default_facilities(db)
    chosen: dict[str, object | None] = {}
    for activity in ACTIVITIES:
        raw = request.query_params.get(activity, "")
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
                gating = _REASON_TEXT[reason].format(phase=node.phase - 1)
            elif reason:
                gating = _REASON_TEXT.get(reason, reason)
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
        label = _raw_label(row.category_name, row.group_name, row.name)
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
                "acquire": _RAW_ACQUIRE.get(label, "Market"),
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


def _state_qs(
    target: int | None,
    qty: int,
    participants: list[int] | None,
    chosen: dict[str, object | None],
    defaults: dict | None = None,
    me: int | None = None,
    te: int | None = None,
    owned: bool = False,
) -> str:
    """The URL state both pages share, serialized once: target, count,
    an explicit participant pool, facility overrides (only when they
    differ from the registry default — absence-means-default keeps
    links honest when the default changes), and ME/TE overrides."""
    from urllib.parse import urlencode

    params: list[tuple[str, str]] = []
    if target is not None:
        params.append(("target", str(target)))
    if qty != 1:
        params.append(("qty", str(qty)))
    if owned:
        params.append(("owned", "1"))
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
    return ("?" + urlencode(params)) if params else ""


@router.get("/planner")
async def planner_page(
    request: Request,
    db: DbDep,
    target: int | None = None,
    qty: int = 1,
    owned: bool = False,
    me: int | None = None,
    te: int | None = None,
):
    """The planner entry: search + target + participants + facilities +
    the full-chain requirement tiers (blueprints, intermediates by
    phase, raw terminators by category) + the owned-copies overlay.
    The sell-side market selector is omitted until M15's market manager
    exists (settled scope)."""
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

    participants, registrations, chosen, defaults = await _planner_state(request, db)

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
        )
        if plan is None:
            return RedirectResponse("/planner", status_code=302)

    state_qs = _state_qs(
        target, qty, participants, chosen, defaults, me, te, owned
    )
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
            "me_override": me,
            "te_override": te,
            "plan": plan,
            "chain": plan.chain if plan else None,
            "phase_views": _phase_views(plan.chain) if plan else [],
            "raw_groups": _raw_groups(plan.chain) if plan else [],
            "blueprints": _blueprint_views(plan.chain) if plan else None,
            "multiplies": _multiplies_lines(plan, chosen) if plan else [],
            "calculate_href": "/planner/plan" + state_qs,
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
            "format_duration": _format_duration,
            "format_isk": _format_isk,
            "format_qty": _format_qty,
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
):
    """The calculated chain build plan (Calculate's destination): stat
    tiles, the chain-flow strip, the phase tree with stage states, the
    chain-wide blueprint overlay, the raw-material acquisition table
    with coverage meters (gaps-only by default), per-participant time,
    and the copy-time readout. Wave bar, copy plan, market panel, and
    job allocation are their own milestones' surfaces."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    if target is None:
        return RedirectResponse("/planner", status_code=302)
    qty = max(1, qty or 1)
    participants, _registrations, chosen, defaults = await _planner_state(request, db)

    plan = await chain_plan(
        db,
        target_type_id=target,
        units=qty,
        participants=participants,
        facilities=chosen,
        me_override=me,
        te_override=te,
    )
    if plan is None:
        return RedirectResponse("/planner", status_code=302)

    state_qs = _state_qs(target, qty, participants, chosen, defaults, me, te)
    base_href = "/planner/plan" + state_qs
    # The toggle flips `all`; dropping the param returns to the
    # gaps-only default (absence-means-default).
    toggle_href = (
        base_href if show_all else base_href + ("&all=1" if state_qs else "?all=1")
    )
    raw_groups = _raw_groups(plan.chain)
    covered_count = sum(
        1 for _label, rows in raw_groups for row in rows if row["meter"] == "full"
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
            "planner_href": "/planner" + state_qs,
            "qty": qty,
            "me_override": me,
            "te_override": te,
            "format_duration": _format_duration,
            "format_isk": _format_isk,
            "format_qty": _format_qty,
        },
    )
