"""Planner section (M4): the commodity-first planner entry and its
depth-1 build plan.

Stateless by design — the whole planner input set (target, count,
participants, facilities, ME/TE overrides) lives in URL query params and
nothing writes to the DB until M6 persists build plans. Param
semantics, chosen once:

- `target` (type id) — invalid ids redirect to the bare planner.
- `qty` — target units, server-clamped to ≥ 1.
- `owned` — the Match From Inventory toggle on the search.
- `me` / `te` — ME/TE overrides; ABSENT means derived from the best
  owned blueprint (the flagged M4 decision; there is no mockup control
  for these — they exist for hand-checking the math).
- `p` — participant character ids, repeatable. ABSENT means the
  default pool (the main's corporation's members); PRESENT — even
  empty (`?p=`) — is an explicit pool. Links never serialize the
  default set, so a roster change re-resolves honestly.
- `manufacturing` / `copying` / `invention` / `reactions` — facility
  registration ids; absent means the registry default (with copying
  falling back to invention's), so a registry edit re-resolves too.

Renders stay DB-pure; the one JSON endpoint is the search type-ahead.
Both pages swap `<main>` in place (static/planner.js, the structures
conventions).
"""

from fastapi import APIRouter, Request
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
from ..planner import PlanResult, depth1_plan
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


def _raw_groups(plan: PlanResult) -> list[tuple[str, list]]:
    """The tier-3 grouping: raw inputs by display label, largest
    requirement first within each group."""
    groups: dict[str, list] = {}
    for material in plan.raw:
        label = _raw_label(
            material.category_name, material.group_name, material.name
        )
        groups.setdefault(label, []).append(material)
    return sorted(
        groups.items(), key=lambda item: (-len(item[1]), item[0])
    )


def _multiplies_line(
    plan: PlanResult, chosen: dict[str, object | None]
) -> dict:
    """The 'This plan multiplies' readout's computed slots: the rig and
    hull numbers behind the material, time, and install-cost math."""
    from ..planner import facility_time_multiplier

    facility = plan.facility
    activity = plan.activity_key
    rig_me = (
        effective_rig_percent(
            activity, "me", facility.me_rig, facility.security_class or ""
        )
        if facility
        else 0.0
    )
    rig_te = (
        effective_rig_percent(
            activity, "te", facility.te_rig, facility.security_class or ""
        )
        if facility
        else 0.0
    )
    hull_time = (
        facility_time_multiplier(facility.structure_type, activity)
        if facility
        else 1.0
    )
    return {
        "facility": facility,
        "rig_me": rig_me,
        "rig_te": rig_te,
        "hull_time": hull_time,
        "security": facility.security_class if facility else None,
        "index": plan.install.system_index,
    }


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
    the depth-1 requirement tiers + the owned-copies overlay. The
    sell-side market selector is omitted until M15's market manager
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
    plan: PlanResult | None = None
    if target is not None:
        plan = await depth1_plan(
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
            "raw_groups": _raw_groups(plan) if plan else [],
            "multiplies": _multiplies_line(plan, chosen) if plan else None,
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
):
    """The calculated depth-1 build plan (Calculate's destination):
    stat tiles, the phase-row tree, required blueprints, the adjusted
    materials, per-participant time, and the copy-time readout. Wave
    bar, copy plan, market panel, and job allocation are their own
    milestones' surfaces."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    if target is None:
        return RedirectResponse("/planner", status_code=302)
    qty = max(1, qty or 1)
    participants, _registrations, chosen, defaults = await _planner_state(request, db)

    plan = await depth1_plan(
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
    return templates.TemplateResponse(
        request,
        "plan.html",
        {
            "authenticated": True,
            "active": "planner",
            "plan": plan,
            "raw_groups": _raw_groups(plan),
            "multiplies": _multiplies_line(plan, chosen),
            "planner_href": "/planner" + state_qs,
            "qty": qty,
            "me_override": me,
            "te_override": te,
            "format_duration": _format_duration,
            "format_isk": _format_isk,
        },
    )
