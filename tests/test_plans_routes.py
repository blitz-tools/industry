"""Plans route tests (M6 PR 5): the Plans section's list and read-only
draft detail — auth gates, the nav link, the export form on the planner
plan page, the detail render (snapshot-faithful: phase tree with
export-time stage states, acquisition table with the gaps-only
default), and the Re-run redirect."""

from urllib.parse import parse_qs, urlparse

import respx

from tests.conftest import token_response
from tests.test_planner_chain import chain_db  # noqa: F401  (fixture)
from tests.test_planner_plan import planner_db  # noqa: F401  (fixture)

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
    assert 'title="Save plan' in response.text
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
