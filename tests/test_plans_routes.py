"""Plans route tests (M6 PR 5 + PR 8): the Plans section's list and
detail — auth gates, the nav link, the export form on the planner plan
page, the detail render (snapshot-faithful: phase tree with export-time
stage states, acquisition table with the gaps-only default), the
Re-run redirect, the Purchase⇄Build markings (chips, phase-bulk, the
fresh-gate lock), and the multibuy export."""

import json
from urllib.parse import parse_qs, urlparse

import respx
from sqlalchemy import select

from app.models import (
    Asset,
    Blueprint,
    BuildPlan,
    BuildPlanMaterial,
    BuildPlanNode,
)
from tests.conftest import token_response
from tests.test_planner_chain import (  # noqa: F401  (fixture)
    CARBIDE,
    CPG,
    FUEL,
    TYPHOON,
    chain_db,
)
from tests.test_planner_plan import planner_db  # noqa: F401  (fixture)

ICE = 4102
TRITANIUM = 34

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _export(client) -> int:
    response = await client.post(
        "/plans", data={"target": 644, "qty": 10}, follow_redirects=False
    )
    assert response.status_code == 303
    return int(response.headers["location"].rsplit("/", 1)[1])


async def test_plans_requires_auth(client):
    response = await client.get("/plans", follow_redirects=False)
    assert response.status_code == 302


async def test_plan_detail_requires_auth(client):
    response = await client.get("/plans/1", follow_redirects=False)
    assert response.status_code == 302


async def test_plan_rerun_requires_auth(client):
    response = await client.get("/plans/1/rerun", follow_redirects=False)
    assert response.status_code == 302


@respx.mock
async def test_plans_list_renders_the_plan(client, chain_db):  # noqa: F811
    await _login(client)
    plan_id = await _export(client)
    response = await client.get("/plans")
    assert response.status_code == 200
    # The nav link lands with the section (Industry → Plans).
    assert 'href="/plans" class="active"' in response.text
    # The row: name, count column, pool badge, status badge, snapshot
    # counts, link.
    assert "Typhoon ×10" in response.text
    assert ">Target</th>" in response.text
    assert "Corp offices" in response.text
    assert "Draft" in response.text
    assert f'href="/plans/{plan_id}"' in response.text
    # Stat tiles over the snapshot.
    assert "4" in response.text  # buildable nodes


@respx.mock
async def test_plans_list_empty_state(client, chain_db):  # noqa: F811
    await _login(client)
    response = await client.get("/plans")
    assert response.status_code == 200
    assert "No plans yet" in response.text


@respx.mock
async def test_plan_detail_renders_the_snapshot(client, chain_db):  # noqa: F811
    await _login(client)
    plan_id = await _export(client)
    response = await client.get(f"/plans/{plan_id}")
    assert response.status_code == 200
    # Header: name, draft badge, read-only pool, the Copy, Branch, and
    # Re-plan buttons (blue, yellow, and purple highlights).
    assert "Typhoon ×10" in response.text
    assert "Draft" in response.text
    assert "Corp offices" in response.text
    assert 'class="icon-button copy"' in response.text
    assert f'href="/plans/{plan_id}/copy"' in response.text
    assert 'class="icon-button branch"' in response.text
    assert f'href="/plans/{plan_id}/branch"' in response.text
    assert 'class="icon-button replan"' in response.text
    assert f'href="/plans/{plan_id}/rerun"' in response.text
    # The phase tree: export-time stage states and gating text.
    assert "Phase 4" in response.text and "Phase 1" in response.text
    assert "Ready to build" in response.text and "Missing inputs" in response.text
    assert "waiting on phase 3" in response.text
    assert "no skilled character in the pool" in response.text
    # Snapshot tiles: the golden install cost.
    assert "960,471.87" in response.text
    # The draft-only sections: required blueprints and time.
    assert "Required blueprints" in response.text
    assert "Owned · BPC only" in response.text
    assert "short of the 157-run need by 146" in response.text
    assert "Test Pilot" in response.text
    # The acquisition table: gaps-only default, export-time measurement.
    assert "Raw materials — acquisition" in response.text
    assert "Tritanium" in response.text
    assert "short 66,582,789" in response.text
    assert "Test Ice Product" not in response.text
    assert "1 type fully covered — hidden in this view" in response.text
    # The counts render from the snapshot rows (not undefined-as-zero).
    assert "Show all 2 types" in response.text
    assert "2 raw types" in response.text


@respx.mock
async def test_plan_detail_all_toggle(client, chain_db):  # noqa: F811
    await _login(client)
    plan_id = await _export(client)
    everything = await client.get(f"/plans/{plan_id}", params={"all": "1"})
    assert everything.status_code == 200
    assert "Test Ice Product" in everything.text
    assert "100%" in everything.text
    assert "Gaps only" in everything.text


@respx.mock
async def test_plan_detail_unknown_plan_redirects_to_list(client, chain_db):  # noqa: F811
    await _login(client)
    response = await client.get("/plans/999", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/plans"


@respx.mock
async def test_rerun_redirects_to_the_planner_entry(client, chain_db):  # noqa: F811
    """Re-plan goes all the way back to the planner ENTRY (the target is
    a planning-phase input — the calculated chain is never edited in
    place), carrying the fork context so a save supersedes this plan."""
    await _login(client)
    plan_id = await _export(client)
    response = await client.get(
        f"/plans/{plan_id}/rerun", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/planner?target=644&qty=10&from_plan={plan_id}"
    )


@respx.mock
async def test_copy_redirects_to_the_calculated_page(client, chain_db):  # noqa: F811
    """Copy plan lands on the calculated page with the same context and
    NO fork context — the same build saved as a new, concurrent plan
    (the container-bucketing workflow); the source plan is untouched."""
    await _login(client)
    plan_id = await _export(client)
    response = await client.get(
        f"/plans/{plan_id}/copy", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/planner/plan?target=644&qty=10"


@respx.mock
async def test_branch_redirects_to_the_planner_entry(client, chain_db):  # noqa: F811
    """Branch plan lands on the planner ENTRY with the setup loaded and
    NO fork context — adjust anything, save as a new sibling; a branch
    diverges and keeps its origin (superseding is Re-plan's job)."""
    await _login(client)
    plan_id = await _export(client)
    response = await client.get(
        f"/plans/{plan_id}/branch", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/planner?target=644&qty=10"


@respx.mock
async def test_branch_unknown_plan_redirects_to_list(client, chain_db):  # noqa: F811
    await _login(client)
    response = await client.get("/plans/999/branch", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/plans"


@respx.mock
async def test_copy_unknown_plan_redirects_to_list(client, chain_db):  # noqa: F811
    await _login(client)
    response = await client.get("/plans/999/copy", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/plans"


@respx.mock
async def test_planner_entry_threads_fork_context_into_calculate(client, chain_db):  # noqa: F811
    """A Re-plan visit to the planner entry keeps its fork context
    through Calculate, so the eventual save supersedes the source plan
    (target changes included — the re-plan is still the re-plan)."""
    await _login(client)
    response = await client.get(
        "/planner", params={"target": 644, "qty": 10, "from_plan": 7}
    )
    assert response.status_code == 200
    assert 'href="/planner/plan?target=644&amp;qty=10&amp;from_plan=7"' in response.text
    # A plain visit carries no fork context.
    plain = await client.get("/planner", params={"target": 644, "qty": 10})
    assert "from_plan" not in plain.text


@respx.mock
async def test_rerun_unknown_plan_redirects_to_list(client, chain_db):  # noqa: F811
    await _login(client)
    response = await client.get("/plans/999/rerun", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/plans"


@respx.mock
async def test_plan_page_renders_the_export_form(client, chain_db):  # noqa: F811
    """The planner plan page's header grows the Save-plan form: the
    URL state as hidden fields, the prefilled default name, and the
    from_plan fork context when the visit came from Re-run."""
    await _login(client)
    response = await client.get("/planner/plan", params={"target": 644, "qty": 10})
    assert response.status_code == 200
    assert 'method="post" action="/plans"' in response.text
    assert '<input type="hidden" name="target" value="644">' in response.text
    assert '<input type="hidden" name="qty" value="10">' in response.text
    assert 'value="Typhoon ×10"' in response.text
    assert 'title="Render plan' in response.text
    # No fork context on a direct visit.
    assert 'name="from_plan"' not in response.text

    forked = await client.get(
        "/planner/plan",
        params={"target": 644, "qty": 10, "from_plan": 7},
    )
    assert forked.status_code == 200
    assert '<input type="hidden" name="from_plan" value="7">' in forked.text


@respx.mock
@respx.mock
async def test_plan_detail_pool_badge_reads_the_sources(client, chain_db):  # noqa: F811
    """The pool badge derives from the snapshot's source set — the
    planner URL semantics carried onto the plan."""
    await _login(client)
    response = await client.post(
        "/plans",
        data={
            "target": 644,
            "qty": 10,
            "src": ["office:8000", "hangar:1234:60003743"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    plan_id = int(response.headers["location"].rsplit("/", 1)[1])
    detail = await client.get(f"/plans/{plan_id}")
    assert "Corp + personal" in detail.text
    listing = await client.get("/plans")
    assert "Corp + personal" in listing.text


# --- Purchase⇄Build markings + multibuy (M6 PR 8) -------------------------------


async def _reload_node(db, plan_id, type_id) -> BuildPlanNode:
    # populate_existing, not expiry + get: a cached identity-map row
    # refreshes through a sync path on async sessions (MissingGreenlet).
    return (
        await db.execute(
            select(BuildPlanNode)
            .where(
                BuildPlanNode.plan_id == plan_id,
                BuildPlanNode.type_id == type_id,
            )
            .execution_options(populate_existing=True)
        )
    ).scalar_one()


async def _reload_material(db, plan_id, type_id) -> BuildPlanMaterial | None:
    return (
        await db.execute(
            select(BuildPlanMaterial)
            .where(
                BuildPlanMaterial.plan_id == plan_id,
                BuildPlanMaterial.type_id == type_id,
            )
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


async def test_sourcing_and_multibuy_require_auth(client):
    response = await client.post(
        "/plans/1/sourcing", data={"node": 1}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    response = await client.get("/plans/1/multibuy", follow_redirects=False)
    assert response.status_code == 302


@respx.mock
async def test_chip_post_marks_purchase_and_amends_raw_math(client, chain_db):  # noqa: F811
    """The chip POST flips a node's sourcing in place and amends the
    acquisition table BY RECOMPUTE: the node's raw demands leave the raw
    rows (ice — the fuel node is its only consumer — drops to zero), a
    purchase line appears for the node's own type, and the detail
    renders the purchased row with the phase split. Un-marking is
    symmetric."""
    await _login(client)
    plan_id = await _export(client)
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    demands = {
        material["type_id"]: material["required_qty"]
        for material in json.loads(fuel.materials_json)
    }
    trit_before = (await _reload_material(
        chain_db, plan_id, TRITANIUM
    )).required_qty

    response = await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": fuel.id, "sourcing": "purchase"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/plans/{plan_id}?open={fuel.phase}#phase-row-{fuel.phase}"
    )

    fuel = await _reload_node(chain_db, plan_id, FUEL)
    assert fuel.sourcing == "purchase"
    trit = await _reload_material(chain_db, plan_id, TRITANIUM)
    assert trit.required_qty == trit_before - demands[TRITANIUM]
    assert (await _reload_material(
        chain_db, plan_id, ICE
    )).required_qty == 0
    line = await _reload_material(chain_db, plan_id, FUEL)
    assert line is not None and line.is_purchase_line
    assert line.required_qty == fuel.qty

    html = (await client.get(f"/plans/{plan_id}")).text
    assert 'class="node-row purchased"' in html
    assert "0 build · 1 purchased" in html
    assert "Purchase all" in html

    # Un-marking restores the pristine raw math and drops the line.
    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": fuel.id, "sourcing": "build"},
        follow_redirects=False,
    )
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    assert fuel.sourcing == "build"
    assert (await _reload_material(
        chain_db, plan_id, TRITANIUM
    )).required_qty == trit_before
    assert (await _reload_material(
        chain_db, plan_id, ICE
    )).required_qty == demands[ICE]
    assert await _reload_material(chain_db, plan_id, FUEL) is None


@respx.mock
async def test_phase_bulk_toggles_both_directions(client, chain_db):  # noqa: F811
    """The phase summary's bulk toggle: Purchase-all marks every node in
    the phase (the summary flips to the split line and the toggle reads
    Build all); Build-all marks them back."""
    await _login(client)
    plan_id = await _export(client)
    response = await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"phase": 1, "sourcing": "purchase"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert (await _reload_node(chain_db, plan_id, FUEL)).sourcing == "purchase"
    html = (await client.get(f"/plans/{plan_id}")).text
    assert "Build all" in html  # the phase-1 toggle flipped

    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"phase": 1, "sourcing": "build"},
        follow_redirects=False,
    )
    assert (await _reload_node(chain_db, plan_id, FUEL)).sourcing == "build"
    html = (await client.get(f"/plans/{plan_id}")).text
    assert "Purchase all" in html
    # The marking redirects land at the changed phase: ?open=N renders
    # that phase's tree row expanded (phases past the first two default
    # collapsed).
    assert 'id="phase-row-3"' in html and 'id="phase-row-3" open' not in html
    html = (await client.get(
        f"/plans/{plan_id}", params={"open": 3}
    )).text
    assert 'id="phase-row-3" open' in html


@respx.mock
async def test_locked_chip_on_blueprint_missing(client, chain_db):  # noqa: F811
    """Missing blueprint forces Purchase: the chip consults the FRESH
    gate (pool blueprint existence, as the refresh computes it — never
    the export snapshot), renders a disabled Purchase chip, and the
    handler rejects Build markings for the locked node while Purchase
    markings still land (the Purchase-all workflow)."""
    await _login(client)
    plan_id = await _export(client)
    # The pool's CPG BPCs leave (both copies, by exact item id).
    for item_id in (3001, 3002):
        bp = (
            await chain_db.execute(
                select(Blueprint).where(Blueprint.item_id == item_id)
            )
        ).scalar_one()
        await chain_db.delete(bp)
    await chain_db.commit()

    html = (await client.get(f"/plans/{plan_id}")).text
    assert 'class="stage-chip purchase" disabled' in html
    assert "Purchase is forced" in html

    cpg = await _reload_node(chain_db, plan_id, CPG)
    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": cpg.id, "sourcing": "build"},
        follow_redirects=False,
    )
    assert (await _reload_node(chain_db, plan_id, CPG)).sourcing == "build"

    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": cpg.id, "sourcing": "purchase"},
        follow_redirects=False,
    )
    assert (await _reload_node(chain_db, plan_id, CPG)).sourcing == "purchase"


@respx.mock
async def test_multibuy_export_format(client, chain_db):  # noqa: F811
    """The multibuy export: the header's ↗ opens an on-page dialog whose
    fixed-width text box carries the shopping list (one line per short
    acquisition row `Item Name<TAB>Quantity` — raw gaps against the
    marking-amended requirement plus purchase lines — sorted by name,
    no header or footer); GET /plans/{id}/multibuy serves the same
    body as a text/plain attachment (the no-script fallback)."""
    await _login(client)
    plan_id = await _export(client)
    html = (await client.get(f"/plans/{plan_id}")).text
    assert f'href="/plans/{plan_id}/multibuy"' in html
    assert 'id="multibuy-dialog"' in html
    assert 'class="multibuy-text"' in html

    # Unmarked: the raw gap only (ice is covered by office stock).
    response = await client.get(f"/plans/{plan_id}/multibuy")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "attachment" in response.headers["content-disposition"]
    trit = await _reload_material(chain_db, plan_id, TRITANIUM)
    assert response.text == (
        f"Tritanium\t{trit.required_qty - trit.available_qty}\n"
    )
    # The dialog's text box carries the same body as the page render.
    assert f"Tritanium\t{trit.required_qty - trit.available_qty}\n" in html

    # Fuel marked Purchase with its office stock gone: the purchase
    # line's gap joins the amended Tritanium gap; ice drops out (its
    # requirement went to zero with the marking).
    stock = (
        await chain_db.execute(select(Asset).where(Asset.item_id == 9102))
    ).scalar_one()
    await chain_db.delete(stock)
    await chain_db.commit()
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": fuel.id, "sourcing": "purchase"},
        follow_redirects=False,
    )
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    trit = await _reload_material(chain_db, plan_id, TRITANIUM)
    response = await client.get(f"/plans/{plan_id}/multibuy")
    assert response.text == (
        f"Test Fuel Block\t{fuel.qty}\n"
        f"Tritanium\t{trit.required_qty - trit.available_qty}\n"
    )
    # The re-rendered detail carries the amended list in its dialog.
    html = (await client.get(f"/plans/{plan_id}")).text
    assert f"Test Fuel Block\t{fuel.qty}\n" in html


@respx.mock
async def test_abandoned_plan_rejects_markings(client, chain_db):  # noqa: F811
    """Terminal plans reject markings: the POST is a no-op redirect and
    the node rows never move."""
    await _login(client)
    plan_id = await _export(client)
    await client.post(f"/plans/{plan_id}/abandon", follow_redirects=False)
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    response = await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": fuel.id, "sourcing": "purchase"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert (await _reload_node(chain_db, plan_id, FUEL)).sourcing == "build"


@respx.mock
async def test_sourcing_post_validates(client, chain_db):  # noqa: F811
    """Unknown plan, unknown node, unknown phase, and a bad target value
    are no-op redirects — the server never trusts form construction."""
    await _login(client)
    plan_id = await _export(client)
    response = await client.post(
        "/plans/999/sourcing",
        data={"node": 1, "sourcing": "purchase"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/plans"
    for data in (
        {"node": 999_999, "sourcing": "purchase"},
        {"phase": 99, "sourcing": "purchase"},
        {"node": 1, "sourcing": "smuggle"},
    ):
        response = await client.post(
            f"/plans/{plan_id}/sourcing", data=data, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == f"/plans/{plan_id}"
    assert (await _reload_node(chain_db, plan_id, FUEL)).sourcing == "build"


@respx.mock
async def test_purchasing_a_later_phase_greys_upstream(client, chain_db):  # noqa: F811
    """Purchasing a later-phase node turns everything only it consumed
    unnecessary: the fuel node (the carbide's only supplier) greys out
    in the tree and the chain strip, and ITS raw demands leave the
    acquisition table too — not just the purchased node's own. Shared
    suppliers (Tritanium, still demanded by the target and the CPG)
    keep their quantities. Un-marking restores all of it."""
    await _login(client)
    plan_id = await _export(client)
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    fuel_demands = {
        material["type_id"]: material["required_qty"]
        for material in json.loads(fuel.materials_json)
    }
    trit_before = (await _reload_material(
        chain_db, plan_id, TRITANIUM
    )).required_qty

    carbide = await _reload_node(chain_db, plan_id, CARBIDE)
    carbide_demands = {
        material["type_id"]: material["required_qty"]
        for material in json.loads(carbide.materials_json)
    }
    response = await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": carbide.id, "sourcing": "purchase"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    # The fuel node stays build-marked but is dead: its demands (the
    # ice, and its Tritanium share) left with it, alongside the
    # purchased carbide's own direct Tritanium demand.
    fuel = await _reload_node(chain_db, plan_id, FUEL)
    assert fuel.sourcing == "build"
    assert (await _reload_material(
        chain_db, plan_id, ICE
    )).required_qty == 0
    trit = await _reload_material(chain_db, plan_id, TRITANIUM)
    assert trit.required_qty == (
        trit_before - fuel_demands[TRITANIUM] - carbide_demands[TRITANIUM]
    )
    # No fuel purchase line: the fuel node is dead, not acquired.
    assert await _reload_material(chain_db, plan_id, FUEL) is None
    # The carbide purchase line is there instead.
    line = await _reload_material(chain_db, plan_id, CARBIDE)
    assert line is not None and line.is_purchase_line

    html = (await client.get(f"/plans/{plan_id}")).text
    assert 'class="node-row unnecessary"' in html
    assert "unnecessary — a later-phase purchase supplies its consumer" in html
    assert "1 node · 0 runs · unnecessary" in html  # the dead phase summary
    assert html.count("unnecessary") >= 3  # node, phase, chain strip

    # Un-marking the carbide revives the whole upstream chain.
    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": carbide.id, "sourcing": "build"},
        follow_redirects=False,
    )
    assert (await _reload_material(
        chain_db, plan_id, ICE
    )).required_qty == fuel_demands[ICE]
    assert (await _reload_material(
        chain_db, plan_id, TRITANIUM
    )).required_qty == trit_before
    html = (await client.get(f"/plans/{plan_id}")).text
    assert 'class="node-row unnecessary"' not in html


@respx.mock
async def test_purchasing_the_target_greys_the_chain(client, chain_db):  # noqa: F811
    """Purchasing the target makes the entire chain unnecessary: every
    other phase greys out, every raw requirement drops to zero (the
    gaps-only acquisition table empties), and the target itself becomes
    the one purchase line."""
    await _login(client)
    plan_id = await _export(client)
    target = await _reload_node(chain_db, plan_id, TYPHOON)
    await client.post(
        f"/plans/{plan_id}/sourcing",
        data={"node": target.id, "sourcing": "purchase"},
        follow_redirects=False,
    )
    for type_id in (TRITANIUM, ICE):
        assert (await _reload_material(
            chain_db, plan_id, type_id
        )).required_qty == 0
    line = await _reload_material(chain_db, plan_id, TYPHOON)
    assert line is not None and line.is_purchase_line
    assert line.required_qty == target.qty

    html = (await client.get(f"/plans/{plan_id}")).text
    assert html.count('class="phase-row unnecessary"') == 3  # phases 1–3
    # Every raw row covered (required 0) — hidden in the gaps-only view.
    assert "types fully covered — hidden in this view" in html


# --- List-screen plan management (bulk activate / abandon / delete) --------------


async def _reload_plan(db, plan_id) -> BuildPlan | None:
    return (
        await db.execute(
            select(BuildPlan)
            .where(BuildPlan.id == plan_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


async def _plan_rows(db, plan_id, model):
    return (
        (
            await db.execute(
                select(model).where(model.plan_id == plan_id)
            )
        )
        .scalars()
        .all()
    )


async def test_plans_bulk_requires_auth(client):
    response = await client.post(
        "/plans/bulk",
        data={"plan_id": ["1"], "action": "delete"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


@respx.mock
async def test_plans_list_renders_the_management_surfaces(client, chain_db):  # noqa: F811
    """The list page carries the selection column, the bulk action bar
    (Activate / Abandon / Delete), and the abandon/delete confirm
    dialogs; with no plans the bar stays out of the empty state."""
    await _login(client)
    empty = (await client.get("/plans")).text
    assert 'class="bulk-bar"' not in empty  # no plans: no action bar

    await _export(client)
    html = (await client.get("/plans")).text
    assert 'id="plans-bulk-form"' in html
    assert 'id="bulk-select-all"' in html
    assert 'name="plan_id"' in html
    assert 'value="activate"' in html
    assert 'value="deactivate"' in html
    assert 'value="abandon"' in html and 'data-confirm="abandon"' in html
    assert 'value="delete"' in html and 'data-confirm="delete"' in html
    assert 'id="bulk-abandon-dialog"' in html
    assert 'id="bulk-delete-dialog"' in html


@respx.mock
async def test_bulk_activate_and_abandon_apply_to_the_applicable_subset(
    client, chain_db  # noqa: F811
):
    """Activate forces the selected drafts active (one refresh so the
    meter lands materialized); Abandon applies to drafts and active
    plans only — terminal plans in the selection are untouched, and
    claims clear immediately."""
    await _login(client)
    first_id = await _export(client)
    second_id = await _export(client)

    response = await client.post(
        "/plans/bulk",
        data={
            "plan_id": [str(first_id), str(second_id)],
            "action": "activate",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/plans"
    for plan_id in (first_id, second_id):
        plan = await _reload_plan(chain_db, plan_id)
        assert plan.status == "active" and plan.activated_at is not None

    # Abandon: the active plan and a fresh draft flip; an already-
    # abandoned plan in the same selection is untouched.
    third_id = await _export(client)
    await client.post(
        f"/plans/{third_id}/abandon", follow_redirects=False
    )
    terminal_before = (await _reload_plan(chain_db, third_id)).abandoned_at
    await client.post(
        "/plans/bulk",
        data={
            "plan_id": [str(first_id), str(third_id), "999999"],
            "action": "abandon",
        },
        follow_redirects=False,
    )
    assert (await _reload_plan(chain_db, first_id)).status == "abandoned"
    third = await _reload_plan(chain_db, third_id)
    assert third.status == "abandoned" and third.abandoned_at == terminal_before
    # Activating a terminal plan changes nothing.
    await client.post(
        "/plans/bulk",
        data={"plan_id": [str(first_id)], "action": "activate"},
        follow_redirects=False,
    )
    assert (await _reload_plan(chain_db, first_id)).status == "abandoned"


@respx.mock
async def test_bulk_delete_removes_abandoned_plans_and_cascades(
    client, chain_db  # noqa: F811
):
    """Delete removes the selected ABANDONED plans permanently — the
    snapshot rows cascade away (the FK rules, enforced now that the
    engine enables SQLite foreign keys) — while drafts in the same
    selection survive. A superseded-by pointer to a deleted plan nulls
    out, never dangles."""
    await _login(client)
    keep_id = await _export(client)
    gone_id = await _export(client)
    assert (await _plan_rows(chain_db, gone_id, BuildPlanNode))
    assert (await _plan_rows(chain_db, gone_id, BuildPlanMaterial))
    await client.post(f"/plans/{gone_id}/abandon", follow_redirects=False)

    response = await client.post(
        "/plans/bulk",
        data={
            "plan_id": [str(gone_id), str(keep_id), "999999", "smuggle"],
            "action": "delete",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/plans"
    assert await _reload_plan(chain_db, gone_id) is None
    assert not (await _plan_rows(chain_db, gone_id, BuildPlanNode))
    assert not (await _plan_rows(chain_db, gone_id, BuildPlanMaterial))
    assert (await _reload_plan(chain_db, keep_id)).status == "draft"

    # The superseded-by pointer: a re-plan fork makes the source point
    # at its replacement; deleting the replacement nulls the pointer.
    source_id = await _export(client)
    fork = await client.post(
        "/plans",
        data={"target": 644, "qty": 10, "from_plan": source_id},
        follow_redirects=False,
    )
    fork_id = int(fork.headers["location"].rsplit("/", 1)[1])
    source = await _reload_plan(chain_db, source_id)
    assert source.superseded_by_plan_id == fork_id
    await client.post(f"/plans/{fork_id}/abandon", follow_redirects=False)
    await client.post(
        "/plans/bulk",
        data={"plan_id": [str(fork_id)], "action": "delete"},
        follow_redirects=False,
    )
    source = await _reload_plan(chain_db, source.id)
    assert source is not None and source.superseded_by_plan_id is None


@respx.mock
async def test_deactivate_returns_active_plans_to_draft(client, chain_db):  # noqa: F811
    """Deactivate is the false-positive escape hatch: active→draft with
    activated_at preserved (it is the tick's never-activated marker, so
    the plan stays draft while its jobs correlate), non-active plans are
    a no-op, and the detail renders the button only where it applies."""
    await _login(client)
    plan_id = await _export(client)
    await client.post(f"/plans/{plan_id}/activate", follow_redirects=False)
    plan = await _reload_plan(chain_db, plan_id)
    activated_at = plan.activated_at
    assert plan.status == "active"

    html = (await client.get(f"/plans/{plan_id}")).text
    assert f'action="/plans/{plan_id}/deactivate"' in html

    response = await client.post(
        f"/plans/{plan_id}/deactivate", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/plans/{plan_id}"
    plan = await _reload_plan(chain_db, plan_id)
    assert plan.status == "draft" and plan.activated_at == activated_at

    # A draft (or terminal) plan is a no-op; the button is absent.
    response = await client.post(
        f"/plans/{plan_id}/deactivate", follow_redirects=False
    )
    assert response.status_code == 303
    assert (await _reload_plan(chain_db, plan_id)).status == "draft"
    html = (await client.get(f"/plans/{plan_id}")).text
    assert f'action="/plans/{plan_id}/deactivate"' not in html


@respx.mock
async def test_bulk_deactivate_applies_to_active_plans(client, chain_db):  # noqa: F811
    """The bulk bar's Deactivate flips the selected active plans back to
    draft; drafts in the same selection are untouched."""
    await _login(client)
    active_id = await _export(client)
    draft_id = await _export(client)
    await client.post(f"/plans/{active_id}/activate", follow_redirects=False)

    response = await client.post(
        "/plans/bulk",
        data={
            "plan_id": [str(active_id), str(draft_id)],
            "action": "deactivate",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert (await _reload_plan(chain_db, active_id)).status == "draft"
    assert (await _reload_plan(chain_db, draft_id)).status == "draft"


@respx.mock
async def test_plans_bulk_validates(client, chain_db):  # noqa: F811
    """A bad action, no selection, or non-numeric plan ids are no-op
    redirects — the server never trusts form construction."""
    await _login(client)
    plan_id = await _export(client)
    for data in (
        {"plan_id": [str(plan_id)], "action": "smuggle"},
        {"action": "delete"},
        {"plan_id": ["not-a-number"], "action": "delete"},
    ):
        response = await client.post(
            "/plans/bulk", data=data, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/plans"
    assert (await _reload_plan(chain_db, plan_id)).status == "draft"
