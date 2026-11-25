"""Plans section (M6): the plan of record's surfaces — the list, the
read-only draft detail, the export POST, and the Re-run fork redirect.
Conventions follow the structures routes (one form, 303 redirects, the
server validates everything); renders stay DB-pure — the detail reads
snapshot rows, never re-runs the resolver. Activation, progress
materialization, and Purchase⇄Build marking are the milestone's next
slices; this PR ships the snapshot and its read-only surfaces."""

import json

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from ..deps import DbDep, is_authenticated
from ..models import BuildPlan
from ..planner import chain_plan
from ..plans import (
    gating_text,
    material_groups,
    parse_material_sources,
    phase_views,
    plan_read,
    planner_state,
    plans_overview,
    pool_badge,
    snapshot_plan,
    state_qs,
    status_badge,
)
from ..templates import templates

router = APIRouter()


def _int_field(form, key: str) -> int | None:
    """A form field as a non-negative int, None when absent or not a
    number (the server never trusts form construction)."""
    raw = (form.get(key) or "").strip()
    return int(raw) if raw.isdigit() else None


@router.get("/plans")
async def plans_page(request: Request, db: DbDep):
    """The plan home: stat tiles over the snapshots and the plan table,
    newest first. The active-surface tiles (correlated jobs, delivered
    nodes) land with the progress refresh."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    rows = await plans_overview(db)
    return templates.TemplateResponse(
        request,
        "plans.html",
        {
            "authenticated": True,
            "active": "plans",
            "rows": rows,
            "drafts": sum(1 for row in rows if row["plan"].status == "draft"),
            "node_total": sum(row["nodes"] for row in rows),
            "material_total": sum(row["materials"] for row in rows),
            "pool_badge": pool_badge,
            "status_badge": status_badge,
        },
    )


@router.get("/plans/{plan_id}")
async def plan_detail_page(
    request: Request,
    db: DbDep,
    plan_id: int,
    show_all: bool = Query(False, alias="all"),
):
    """The plan of record, read-only while draft: snapshot tiles, the
    chain-flow strip, the phase tree with export-time stage states, the
    draft-only blueprint and time sections, and the acquisition table
    (gaps-only by default, availability as measured at export)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    read = await plan_read(db, plan_id)
    if read is None:
        return RedirectResponse("/plans", status_code=302)
    plan, nodes, materials = read
    target_node = next((node for node in nodes if node.is_target), None)
    groups = material_groups(materials)
    covered_count = sum(
        1 for _label, rows in groups for row in rows if row["meter"] == "full"
    )
    base_href = f"/plans/{plan_id}"
    toggle_href = base_href + ("?all=1" if not show_all else "")
    # Snapshot rollups (display-only JSON blobs parsed once per render).
    install_totals = [json.loads(node.install_json).get("total") for node in nodes]
    copy_facility = (
        json.loads(plan.copy_facility_json)
        if plan.copy_facility_json is not None
        else None
    )
    facilities = json.loads(plan.facilities_json)
    facilities_line = " · ".join(
        f"{activity} — {facility['structure_name']}"
        for activity, facility in facilities.items()
        if facility
    )
    return templates.TemplateResponse(
        request,
        "plan_detail.html",
        {
            "authenticated": True,
            "active": "plans",
            "plan": plan,
            "target_node": target_node,
            "nodes": nodes,
            "materials": materials,
            "phase_views": phase_views(nodes),
            "material_groups": groups,
            "covered_count": covered_count,
            "show_all": show_all,
            "toggle_href": toggle_href,
            "pool_badge": pool_badge(plan),
            "status_badge": status_badge(plan),
            "gating_text": gating_text,
            "totals": {
                "runs": sum(node.runs for node in nodes),
                "jobs": sum(node.jobs for node in nodes),
                "seconds": sum(node.total_seconds for node in nodes),
                "install_total": sum(
                    value for value in install_totals if value is not None
                ),
                "install_missing": sum(
                    1 for value in install_totals if value is None
                ),
                "phases": len({node.phase for node in nodes}),
            },
            "participants": json.loads(plan.participants_json),
            "facilities_line": facilities_line,
            "cycles": json.loads(plan.cycles_json),
            "copy_facility": copy_facility,
        },
    )


@router.post("/plans")
async def plans_export(request: Request, db: DbDep):
    """Save plan: re-resolve the chain from the form's planner state
    (DB-pure, no ESI), snapshot it as a new draft, and land on its
    detail page. A `from_plan` id is the Re-run fork — the one path
    that abandons another plan; fresh exports never touch siblings."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    form = await request.form()

    target = _int_field(form, "target")
    if target is None:
        return RedirectResponse("/planner", status_code=303)
    qty_field = _int_field(form, "qty")
    qty = max(1, qty_field or 1)
    me = _int_field(form, "me")
    te = _int_field(form, "te")

    participants, _registrations, chosen, defaults = await planner_state(db, form)
    material_sources = parse_material_sources(form)

    resolved = await chain_plan(
        db,
        target_type_id=target,
        units=qty,
        participants=participants,
        facilities=chosen,
        me_override=me,
        te_override=te,
        material_sources=material_sources,
    )
    if resolved is None:
        return RedirectResponse("/planner", status_code=303)

    name = (form.get("name", "") or "").strip()
    if not name:
        name = f"{resolved.chain.target_node.name} ×{qty:,}"
    plan = await snapshot_plan(
        db,
        resolved=resolved,
        facilities=chosen,
        name=name,
        source_query=state_qs(
            target, qty, participants, chosen, defaults, me, te,
            material_sources=material_sources,
        ),
        sources=material_sources,
        me_override=me,
        te_override=te,
        from_plan_id=_int_field(form, "from_plan"),
    )
    await db.commit()
    return RedirectResponse(f"/plans/{plan.id}", status_code=303)


@router.get("/plans/{plan_id}/rerun")
async def plan_rerun(request: Request, db: DbDep, plan_id: int):
    """The Re-run fork's front door: all the way back to the planner
    ENTRY with the plan's source query plus the fork context — the
    target is adjustable there (targets are a planning-phase input; the
    calculated chain is never edited in place, because spreading a
    build across jobs realigns material inputs — M9's waves own that
    math). Saving from a re-run visit supersedes this plan."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=302)
    source_query = plan.source_query or ""
    separator = "&" if source_query.startswith("?") else "?"
    return RedirectResponse(
        f"/planner{source_query}{separator}from_plan={plan.id}",
        status_code=303,
    )


@router.get("/plans/{plan_id}/copy")
async def plan_copy(request: Request, db: DbDep, plan_id: int):
    """Copy plan: back to the CALCULATED page with the plan's source
    query, no fork context — the same build saved as a new, concurrent
    plan (the container-bucketing workflow: same chain, different
    material-source locations). The source plan is never touched."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=302)
    return RedirectResponse(
        f"/planner/plan{plan.source_query or ''}", status_code=303
    )


@router.get("/plans/{plan_id}/branch")
async def plan_branch(request: Request, db: DbDep, plan_id: int):
    """Branch plan: the planner ENTRY with the plan's setup loaded and
    NO fork context — the same planning setup (target, count,
    participants, facilities, sources) adjustable in full, saved as a
    new sibling plan. Git semantics, deliberately: a branch diverges
    and keeps its origin; superseding is Re-plan's job (from_plan)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=302)
    return RedirectResponse(f"/planner{plan.source_query or ''}", status_code=303)
