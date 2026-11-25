"""Build-plan progress tests (M6 PR 7): the refresh tick's
materialization — availability re-measured against the pinned source
set, delivery from correlated jobs' successful runs, the running/
deliver/complete stage states, the gating and stock-gap rungs
recomputed against fresh world state, the draft→active→complete state
machine, and the never-raises guarantee — plus the Activate/Abandon
routes and the surfaces they light up (stage chips, matched-jobs
summary, progress meters)."""

from datetime import timedelta

import respx
from sqlalchemy import select

from app.db import utc_now
from app.models import (
    Asset,
    Blueprint,
    BuildPlan,
    BuildPlanMaterial,
    BuildPlanNode,
    IndustryJob,
    Skill,
)
from app.plans import refresh_job_claims, refresh_plan, refresh_plans_tick
from tests.conftest import token_response
from tests.test_planner_chain import (  # noqa: F401  (fixture)
    CARBIDE,
    CPG,
    FUEL,
    TYPHOON,
    chain_db,
)
from tests.test_planner_plan import MAIN, planner_db  # noqa: F401  (fixture)
from tests.test_plans_correlation import (  # noqa: F401  (helpers)
    CORP,
    FUEL_BP,
    REACTION_BP,
    _export,
    _job,
)

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
TRITANIUM = 34

# The golden chain's node blueprints at ×10: type → (blueprint, ESI
# activity, products per run) — one generous delivered job per node
# completes the plan.
NODE_BLUEPRINTS = {
    TYPHOON: (998, 1, 1),
    CPG: (20411, 1, 3),
    CARBIDE: (46207, 9, 200),
    FUEL: (4101, 1, 40),
}


async def _refresh(db, plan):
    """One synchronous materialization pass — the tick's body for a
    single plan (claims, then the plan)."""
    await refresh_job_claims(db)
    await refresh_plan(db, plan)
    await db.commit()


async def _reload(db, plan_id) -> BuildPlan:
    # populate_existing, not expire_all + get: an expired identity-map
    # instance refreshes through a sync path on async sessions
    # (MissingGreenlet) — a fresh select with populate_existing
    # refreshes the cached row properly.
    return (
        await db.execute(
            select(BuildPlan)
            .where(BuildPlan.id == plan_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()


async def _node(db, plan_id, type_id) -> BuildPlanNode:
    return (
        await db.execute(
            select(BuildPlanNode).where(
                BuildPlanNode.plan_id == plan_id,
                BuildPlanNode.type_id == type_id,
            )
        )
    ).scalar_one()


async def _material(db, plan_id, type_id) -> BuildPlanMaterial:
    return (
        await db.execute(
            select(BuildPlanMaterial).where(
                BuildPlanMaterial.plan_id == plan_id,
                BuildPlanMaterial.type_id == type_id,
            )
        )
    ).scalar_one()


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    from urllib.parse import parse_qs, urlparse

    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def test_availability_measures_the_pinned_source_set(chain_db):  # noqa: F811
    """Both source modes re-measure on refresh: the default counts
    corp-side stock only (personal hangars out); pinned refs count
    exactly the selected sources — the same selection semantics the
    planner page ran at export."""
    default_plan = await _export(chain_db)
    scoped_plan = await _export(
        chain_db, sources=["office:8000", f"hangar:{MAIN}:60003743"]
    )

    await _refresh(chain_db, default_plan)
    await _refresh(chain_db, scoped_plan)

    # Office 2M Tritanium only under the default; the pinned set adds
    # the main's personal 1M.
    assert (await _material(chain_db, default_plan.id, TRITANIUM)).available_qty \
        == 2_000_000
    assert (await _material(chain_db, scoped_plan.id, TRITANIUM)).available_qty \
        == 3_000_000


async def test_delivered_sums_successful_runs_and_caps_at_qty(chain_db):  # noqa: F811
    """Delivery is Σ successful_runs × products_per_run over correlated
    delivered jobs, capped at the node's requirement — over-delivery
    banks as inventory, never as node progress. The CPG node carries
    the headroom for the uncapped sum (471 required at 3/run)."""
    plan = await _export(chain_db)
    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.qty > 3 * 8  # the sums below stay under the requirement
    chain_db.add_all(
        [
            _job(
                blueprint_type_id=20411, status="delivered",
                runs=5, successful_runs=5,
            ),
            _job(
                blueprint_type_id=20411, status="delivered",
                runs=3, successful_runs=3,
            ),
        ]
    )
    await _refresh(chain_db, plan)

    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.delivered_qty == 8 * cpg.products_per_run
    assert cpg.state != "complete"

    # A generous job caps at the requirement and completes the node.
    chain_db.add(
        _job(
            blueprint_type_id=20411, status="delivered",
            runs=1, successful_runs=100_000,
        )
    )
    await _refresh(chain_db, plan)
    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.delivered_qty == cpg.qty
    assert cpg.state == "complete" and cpg.state_reason is None


async def test_running_and_deliver_states(chain_db):  # noqa: F811
    """Correlated active jobs put the node In progress (running_qty =
    their runs); a ready job puts it Ready to deliver."""
    plan = await _export(chain_db)
    chain_db.add_all(
        [
            _job(runs=4, end_date=utc_now() + timedelta(hours=2)),
            _job(
                blueprint_type_id=20411, runs=157, status="ready",
                end_date=utc_now() - timedelta(hours=1),
            ),
        ]
    )
    await _refresh(chain_db, plan)

    fuel = await _node(chain_db, plan.id, FUEL)
    assert fuel.state == "running" and fuel.running_qty == 4
    assert fuel.delivered_qty == 0
    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.state == "deliver"
    # The plan left draft: its first job correlated.
    assert (await _reload(chain_db, plan.id)).status == "active"


async def test_stock_gap_recomputed_against_fresh_availability(chain_db):  # noqa: F811
    """The fallback ladder re-derives from live stock: removing the
    office's ice flips the fuel node to stock-gap; restoring it flips
    the node back to ready — no re-export needed."""
    plan = await _export(chain_db)
    fuel = await _node(chain_db, plan.id, FUEL)
    assert fuel.state == "ready" and fuel.state_reason is None

    ice = (
        await chain_db.execute(select(Asset).where(Asset.item_id == 9101))
    ).scalar_one()
    await chain_db.delete(ice)
    await chain_db.commit()

    await _refresh(chain_db, plan)
    fuel = await _node(chain_db, plan.id, FUEL)
    assert fuel.state == "missing" and fuel.state_reason == "stock-gap"
    assert (await _material(chain_db, plan.id, 4102)).available_qty == 0

    chain_db.add(
        Asset(
            owner_type="corporation", owner_id=CORP, item_id=9101,
            type_id=4102, quantity=10, location_id=8000,
            location_flag="CorpSAG1", location_type="item",
            parent_location_id=8000, is_blueprint_copy=False,
            is_singleton=False,
        )
    )
    await chain_db.commit()
    await _refresh(chain_db, plan)
    fuel = await _node(chain_db, plan.id, FUEL)
    assert fuel.state == "ready" and fuel.state_reason is None


async def test_skill_gate_refreshes_from_fresh_levels(chain_db):  # noqa: F811
    """Gating is a measured readiness fact, not a planning input (the
    owner's 2026-11-25 call): the reaction node's level-5 gate clears
    when a pinned participant trains it — no re-plan needed, and the
    node falls through the ladder to ready (its inputs are stocked)."""
    plan = await _export(chain_db)
    carbide = await _node(chain_db, plan.id, CARBIDE)
    assert carbide.state == "missing" and carbide.state_reason == "skill-gated"

    # Still gated on refresh — nobody in the pool holds level 5.
    await _refresh(chain_db, plan)
    carbide = await _node(chain_db, plan.id, CARBIDE)
    assert carbide.state_reason == "skill-gated"

    chain_db.add(
        Skill(
            owner_type="character",
            owner_id=5678,  # CORP_MEMBER, a pinned participant
            skill_id=22242,
            trained_skill_level=5,
            active_skill_level=5,
            skillpoints_in_skill=500_000,
        )
    )
    await chain_db.commit()
    await _refresh(chain_db, plan)
    carbide = await _node(chain_db, plan.id, CARBIDE)
    assert carbide.state == "ready" and carbide.state_reason is None


async def test_blueprint_gate_refreshes_from_fresh_pool(chain_db):  # noqa: F811
    """Same rule for blueprints: the gate re-derives from the pool's
    current contents — the BPCs leaving flips the node to
    blueprint-missing, one returning un-gates it and the ladder falls
    through to the next rung (its carbide input is not in stock). The
    calc snapshot never moves."""
    plan = await _export(chain_db)
    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.state_reason != "blueprint-missing"  # BPCs owned at export

    # The pool's CPG BPCs leave (both copies, by exact item id).
    for item_id in (3001, 3002):
        bp = (
            await chain_db.execute(
                select(Blueprint).where(Blueprint.item_id == item_id)
            )
        ).scalar_one()
        await chain_db.delete(bp)
    await chain_db.commit()
    await _refresh(chain_db, plan)
    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.state == "missing" and cpg.state_reason == "blueprint-missing"

    # One copy returns: the gate clears, the ladder falls through.
    chain_db.add(
        Blueprint(
            owner_type="corporation", owner_id=CORP, item_id=3001,
            type_id=20411, location_id=60003743, location_flag="CorpSAG2",
            quantity=1, runs=5, material_efficiency=0, time_efficiency=0,
        )
    )
    await chain_db.commit()
    await _refresh(chain_db, plan)
    cpg = await _node(chain_db, plan.id, CPG)
    assert cpg.state == "missing" and cpg.state_reason == "waiting-upstream"


async def test_state_machine_completes_and_delivery_is_sticky(chain_db):  # noqa: F811
    """Every node delivered → the plan completes (completed_at set).
    Delivery is sticky: jobs going terminal afterwards never lower a
    node's delivered_qty, so a complete plan stays complete even though
    the wholesale claim rewrite drops its rows (the PR 6 discovery)."""
    plan = await _export(chain_db)
    for _type_id, (blueprint, activity, _ppr) in NODE_BLUEPRINTS.items():
        chain_db.add(
            _job(
                blueprint_type_id=blueprint, activity_id=activity,
                status="delivered", runs=1, successful_runs=100_000,
            )
        )
    await _refresh(chain_db, plan)

    plan = await _reload(chain_db, plan.id)
    assert plan.status == "complete" and plan.completed_at is not None
    for type_id in NODE_BLUEPRINTS:
        node = await _node(chain_db, plan.id, type_id)
        assert node.state == "complete"

    # Every job reverts to cancelled: claims wipe, delivery holds.
    jobs = (await chain_db.execute(select(IndustryJob))).scalars().all()
    for job in jobs:
        job.status = "cancelled"
    await chain_db.commit()
    await _refresh(chain_db, plan)

    plan = await _reload(chain_db, plan.id)
    assert plan.status == "complete"
    fuel = await _node(chain_db, plan.id, FUEL)
    assert fuel.state == "complete" and fuel.delivered_qty == fuel.qty


async def test_refresh_tick_never_raises(app, chain_db):  # noqa: F811
    """The tick survives a plan it cannot refresh: the failing plan
    records refresh_error, the healthy plan still materializes, and
    nothing raises (the world_sync_tick guarantee)."""
    healthy = await _export(chain_db)
    corrupt = await _export(chain_db)
    corrupt.sources_json = "not json"
    await chain_db.commit()

    await refresh_plans_tick(app.state.session_factory)

    corrupt = await _reload(chain_db, corrupt.id)
    healthy = await _reload(chain_db, healthy.id)
    assert corrupt.refresh_error is not None
    assert healthy.refresh_error is None
    assert healthy.refreshed_at is not None


@respx.mock
async def test_activate_and_abandon_routes(client, chain_db):  # noqa: F811
    """Activate forces draft→active (the counterweight to heuristic
    misses); Abandon is terminal. Neither re-activates a terminal plan,
    and both are auth-gated."""
    plan = await _export(chain_db)
    plan_id = plan.id

    response = await client.post(
        f"/plans/{plan_id}/activate", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    await _login(client)
    response = await client.post(
        f"/plans/{plan_id}/activate", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/plans/{plan_id}"
    plan = await _reload(chain_db, plan_id)
    assert plan.status == "active" and plan.activated_at is not None

    # Re-activating an active plan changes nothing.
    await client.post(f"/plans/{plan_id}/activate", follow_redirects=False)
    assert (await _reload(chain_db, plan_id)).status == "active"

    html = (await client.get(f"/plans/{plan_id}")).text
    assert "plan-state active" in html and ">Active<" in html

    response = await client.post(
        f"/plans/{plan_id}/abandon", follow_redirects=False
    )
    assert response.status_code == 303
    plan = await _reload(chain_db, plan_id)
    assert plan.status == "abandoned" and plan.abandoned_at is not None

    # Terminal: Activate no longer applies.
    await client.post(f"/plans/{plan_id}/activate", follow_redirects=False)
    assert (await _reload(chain_db, plan_id)).status == "abandoned"
    html = (await client.get(f"/plans/{plan_id}")).text
    assert ">Abandoned<" in html


@respx.mock
async def test_export_lands_materialized(client, chain_db):  # noqa: F811
    """The export POST runs one synchronous refresh: the redirect lands
    on a materialized plan (refreshed_at set, states recomputed)."""
    await _login(client)
    response = await client.post(
        "/plans", data={"target": TYPHOON, "qty": 10}, follow_redirects=False
    )
    assert response.status_code == 303
    plan_id = int(response.headers["location"].rsplit("/", 1)[1])
    plan = await _reload(chain_db, plan_id)
    assert plan.refreshed_at is not None
    assert plan.refresh_error is None


@respx.mock
async def test_detail_renders_progress_surfaces(client, chain_db):  # noqa: F811
    """The active surface: In-progress chips with time-to-delivery, the
    matched-jobs summary (installer, runs), the refreshed/assets-synced/
    jobs-correlated meta line, and the list page's Progress column."""
    await _login(client)
    plan = await _export(chain_db)
    chain_db.add(
        _job(runs=4, end_date=utc_now() + timedelta(hours=2))
    )
    await _refresh(chain_db, plan)

    html = (await client.get(f"/plans/{plan.id}")).text
    assert "In progress" in html
    assert "Test Pilot" in html  # the installer, in the gating slot
    assert "delivers in 2 h" in html  # time-to-delivery from end_date
    assert "1 job correlated" in html  # the meta line
    assert "Nodes delivered" in html  # the active stat tile

    list_html = (await client.get("/plans")).text
    assert "Progress" in list_html
