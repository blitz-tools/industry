"""Plans section (M6): the plan of record's surfaces — the list, the
detail with live progress (the refresh tick materializes availability,
correlation, and delivery; renders stay DB-pure), the export POST, the
state-machine controls (Activate, Abandon), the Purchase⇄Build
markings (chips, phase-bulk, the fresh-gate lock), the multibuy export,
and the plan-shaping redirects. Conventions follow the structures
routes (one form, 303 redirects, the server validates everything)."""

import json

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import delete

from ..db import utc_now
from ..deps import DbDep, is_authenticated
from ..industry import owned_blueprints_for_types
from ..models import BuildPlan, BuildPlanJob
from ..planner import chain_plan
from ..plans import (
    apply_sourcing_math,
    assets_synced_at,
    gating_text,
    material_groups,
    multibuy_body,
    necessary_nodes,
    parse_material_sources,
    phase_views,
    plan_job_views,
    plan_read,
    planner_state,
    plans_overview,
    pool_badge,
    refresh_job_claims,
    refresh_plan,
    snapshot_plan,
    stage_text,
    state_qs,
    status_badge,
    stock_gap_meters,
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
    """The plan home: stat tiles over the snapshots and the plan table
    with per-plan progress meters (delivered / buildable nodes),
    newest first."""
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
    """The plan of record: snapshot tiles, the chain-flow strip, the
    phase tree with live stage states (materialized by the refresh
    tick) and the Purchase⇄Build chips (locked where the FRESH
    blueprint gate is missing — pool blueprint existence, the same read
    the refresh runs), the matched-jobs summaries, the draft-only
    blueprint and time sections, and the acquisition table (gaps-only
    by default, availability as last materialized). Every phase row
    renders expanded — the phases are the page's content, and the
    scripted marking swap remembers collapses within a visit."""
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
    job_views = await plan_job_views(db, plan_id)
    # The fresh-gate lock (pool blueprint existence, never the
    # export-time calc snapshot) and the stock-gap meters — both DB
    # reads, so page-render purity holds. The necessity set (what the
    # current markings still need) drives the greying and the counts.
    owned = await owned_blueprints_for_types(
        db, list({node.blueprint_type_id for node in nodes})
    )
    locked_nodes = {
        node.id for node in nodes if not owned.get(node.blueprint_type_id)
    }
    needed = necessary_nodes(nodes)
    build_nodes = [
        node
        for node in nodes
        if node.id in needed and node.sourcing != "purchase"
    ]
    delivered_nodes = sum(
        1 for node in build_nodes if node.qty and node.delivered_qty >= node.qty
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
            "needed": needed,
            "phase_views": phase_views(nodes, needed),
            "multibuy_text": multibuy_body(materials),
            "material_groups": groups,
            "covered_count": covered_count,
            "show_all": show_all,
            "toggle_href": toggle_href,
            "pool_badge": pool_badge(plan),
            "status_badge": status_badge(plan),
            "gating_text": gating_text,
            "stage_text": stage_text,
            "job_views": job_views,
            "locked_nodes": locked_nodes,
            "stock_meters": stock_gap_meters(nodes, materials),
            "correlated_jobs": sum(
                len(view["jobs"]) for view in job_views.values()
            ),
            "build_count": len(build_nodes),
            "delivered_nodes": delivered_nodes,
            "assets_synced": await assets_synced_at(db),
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
    """Render plan: re-resolve the chain from the form's planner state
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
    # One synchronous refresh so the redirect lands materialized —
    # availability re-measured, refreshed_at set (the claims pass stays
    # the tick's: a plan created this second can correlate nothing the
    # sync table doesn't already show, and the tick catches that).
    await refresh_plan(db, plan)
    await db.commit()
    return RedirectResponse(f"/plans/{plan.id}", status_code=303)


@router.post("/plans/{plan_id}/activate")
async def plan_activate(request: Request, db: DbDep, plan_id: int):
    """Activate: the owner forcing draft→active — the counterweight to
    correlation misses (a plan whose jobs the heuristic didn't catch
    still tracks). Runs one synchronous refresh so the redirect lands
    with the plan's correlated jobs materialized. Non-draft plans are
    a no-op redirect (the reverse is Deactivate; completion is
    computed)."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=303)
    if plan.status == "draft":
        plan.status = "active"
        plan.activated_at = utc_now()
        await refresh_job_claims(db)
        await refresh_plan(db, plan)
        await db.commit()
    # The DB row's id, never the raw path parameter — the url-redirection
    # hygiene every redirect follows (the param is int-coerced by FastAPI,
    # but the loaded row is provably server-side data).
    return RedirectResponse(f"/plans/{plan.id}", status_code=303)


@router.post("/plans/{plan_id}/deactivate")
async def plan_deactivate(request: Request, db: DbDep, plan_id: int):
    """Deactivate: the owner pulling active→draft — the escape hatch
    for a correlation false-positive that flipped a plan early (the
    handoff's open pin, resolved: owner activation control is
    reversible). The tick's auto-activate only fires for never-
    activated plans, so a deactivated plan stays draft while its jobs
    still correlate; activated_at keeps its historical value (it is
    the never-activated marker). Re-activation is the Activate button.
    Non-active plans are a no-op redirect."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=303)
    if plan.status == "active":
        plan.status = "draft"
        await db.commit()
    return RedirectResponse(f"/plans/{plan.id}", status_code=303)


@router.post("/plans/{plan_id}/abandon")
async def plan_abandon(request: Request, db: DbDep, plan_id: int):
    """Abandon: the owner closing a plan (terminal). Its claims drop
    immediately so the jobs free up for a sibling plan — the tick's
    correlation pass excludes terminal plans, so the rows would go on
    the next pass anyway; clearing here keeps the one-claim rule honest
    at once. Terminal plans are a no-op redirect."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=303)
    if plan.status in ("draft", "active"):
        plan.status = "abandoned"
        plan.abandoned_at = utc_now()
        await db.execute(
            delete(BuildPlanJob).where(BuildPlanJob.plan_id == plan_id)
        )
        await db.commit()
    return RedirectResponse(f"/plans/{plan.id}", status_code=303)


@router.post("/plans/bulk")
async def plans_bulk(request: Request, db: DbDep):
    """List-screen plan management: Activate, Deactivate, Abandon, or
    Delete the selected plans. Each action applies to the applicable
    subset of the selection — Activate: drafts; Deactivate: active
    plans (the false-positive escape hatch — the tick never re-activates
    a previously activated plan); Abandon: drafts and active plans;
    Delete: abandoned plans only, permanently (the snapshot rows
    cascade away; a superseded-by pointer to a deleted plan nulls out,
    never dangles). One claims pass plus a synchronous refresh per
    activation, matching the detail page's Activate; abandonment clears
    claims immediately. Terminal plans reject every action, and the
    server never trusts form construction."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    form = await request.form()
    action = (form.get("action") or "").strip()
    if action not in ("activate", "deactivate", "abandon", "delete"):
        return RedirectResponse("/plans", status_code=303)
    plan_ids = [
        int(value)
        for value in form.getlist("plan_id")
        if value.strip().isdigit()
    ]
    activated: list[BuildPlan] = []
    for plan_id in plan_ids:
        plan = await db.get(BuildPlan, plan_id)
        if plan is None:
            continue
        if action == "activate" and plan.status == "draft":
            plan.status = "active"
            plan.activated_at = utc_now()
            activated.append(plan)
        elif action == "deactivate" and plan.status == "active":
            plan.status = "draft"
        elif action == "abandon" and plan.status in ("draft", "active"):
            plan.status = "abandoned"
            plan.abandoned_at = utc_now()
            await db.execute(
                delete(BuildPlanJob).where(BuildPlanJob.plan_id == plan.id)
            )
        elif action == "delete" and plan.status == "abandoned":
            await db.delete(plan)
    if activated:
        await refresh_job_claims(db)
        for plan in activated:
            await refresh_plan(db, plan)
    await db.commit()
    return RedirectResponse("/plans", status_code=303)


@router.post("/plans/{plan_id}/sourcing")
async def plan_sourcing(request: Request, db: DbDep, plan_id: int):
    """The Purchase⇄Build marking (per-node chips and phase-bulk
    toggles): amends node rows in place — structural changes go through
    Re-plan. The acquisition math amends BY RECOMPUTE (snapshot total
    minus the purchase-marked demands — idempotent, symmetric on
    un-mark), a purchase line joins the acquisition table per marked
    type, and one synchronous refresh lands the redirect materialized
    at the phase that changed. The fresh-gate lock: a node whose
    blueprint the pool no longer holds cannot be marked Build (missing
    blueprint forces Purchase); Purchase markings always land. Terminal
    plans reject markings."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    plan = await db.get(BuildPlan, plan_id)
    if plan is None:
        return RedirectResponse("/plans", status_code=303)
    if plan.status not in ("draft", "active"):
        return RedirectResponse(f"/plans/{plan.id}", status_code=303)
    form = await request.form()
    target = (form.get("sourcing") or "").strip()
    if target not in ("build", "purchase"):
        return RedirectResponse(f"/plans/{plan.id}", status_code=303)
    read = await plan_read(db, plan.id)
    assert read is not None  # the row loaded above
    _plan, nodes, materials = read
    if "node" in form:
        node_id = _int_field(form, "node")
        selected = [node for node in nodes if node.id == node_id]
    else:
        phase = _int_field(form, "phase")
        selected = [node for node in nodes if node.phase == phase]
    if not selected:
        return RedirectResponse(f"/plans/{plan.id}", status_code=303)
    if target == "build":
        # The lock consults the FRESH gate — pool blueprint existence
        # as the refresh computes it — so a node whose blueprint left
        # the pool keeps its forced Purchase. Locked nodes drop out of
        # a Build-all bulk silently: they cannot be built.
        owned = await owned_blueprints_for_types(
            db, list({node.blueprint_type_id for node in selected})
        )
        selected = [
            node for node in selected if owned.get(node.blueprint_type_id)
        ]
        if not selected:
            return RedirectResponse(f"/plans/{plan.id}", status_code=303)
    for node in selected:
        node.sourcing = target
    await apply_sourcing_math(db, nodes, materials)
    await refresh_plan(db, plan)
    await db.commit()
    # The anchor lands the no-script path at the changed phase; every
    # row is open by default, so the page reads in place.
    phase = selected[0].phase
    return RedirectResponse(
        f"/plans/{plan.id}#phase-row-{phase}", status_code=303
    )


@router.get("/plans/{plan_id}/multibuy")
async def plan_multibuy(request: Request, db: DbDep, plan_id: int):
    """The multibuy export: the acquisition table as a shopping list —
    one `Item Name<TAB>Quantity` line per short row (raw gaps against
    the marking-amended requirement plus purchase lines), name-sorted,
    no header or footer — pastes straight into the in-game multibuy
    window."""
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    read = await plan_read(db, plan_id)
    if read is None:
        return RedirectResponse("/plans", status_code=302)
    plan, _nodes, materials = read
    return Response(
        multibuy_body(materials),
        media_type="text/plain",
        headers={
            "Content-Disposition": (
                f'attachment; filename="plan-{plan.id}-multibuy.txt"'
            )
        },
    )


@router.get("/plans/{plan_id}/rerun")
async def plan_rerun(request: Request, db: DbDep, plan_id: int):
    """The Re-run fork's front door: all the way back to the planner
    ENTRY with the plan's source query plus the fork context — the
    target is adjustable there (targets are a planning-phase input; the
    calculated chain is never edited in place, because spreading a
    build across jobs realigns material inputs — M9's waves own that
    math). Rendering from a re-run visit supersedes this plan."""
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
