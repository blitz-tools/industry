"""Planner route tests (M4): auth gates, the search JSON feed, the
planner page's URL-state semantics (target validity, qty clamping,
participants, facility defaults), and the calculated plan page. The
planner_db fixture (tests/test_planner_plan.py) seeds the world these
render against; SSO login drives the same callback the other route
suites use."""

from urllib.parse import parse_qs, urlparse

import respx

from tests.conftest import token_response
from tests.test_planner_chain import chain_db  # noqa: F401  (fixture)
from tests.test_planner_plan import MAIN, planner_db  # noqa: F401  (fixture)

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def test_planner_requires_auth(client):
    response = await client.get("/planner", follow_redirects=False)
    assert response.status_code == 302


async def test_planner_search_requires_auth(client):
    response = await client.get("/planner/search", params={"q": "typh"})
    assert response.status_code == 403
    assert (response.json())["entries"] == []


async def test_plan_page_requires_auth(client):
    response = await client.get("/planner/plan", follow_redirects=False)
    assert response.status_code == 302


@respx.mock
async def test_planner_bare_page_is_search_only(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner")
    assert response.status_code == 200
    assert "Find a target" in response.text
    assert "Target build" not in response.text  # sections appear on selection
    assert "5,014" not in response.text  # the live count, never a constant


@respx.mock
async def test_planner_search_feed(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner/search", params={"q": "typh"})
    assert response.status_code == 200
    entries = (response.json())["entries"]
    assert [entry["type_name"] for entry in entries] == [
        "Typhoon",
        "Typhoon Fleet Issue",
    ]
    typhoon = entries[0]
    assert typhoon["type_id"] == 644
    assert typhoon["blueprint_name"] == "Typhoon Blueprint"
    assert typhoon["owned_originals"] == 1

    # Match From Inventory filters to owned products.
    response = await client.get(
        "/planner/search", params={"q": "typh", "owned": "1"}
    )
    assert [entry["type_name"] for entry in (response.json())["entries"]] == [
        "Typhoon"
    ]


@respx.mock
async def test_planner_with_target_renders_tiers(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner", params={"target": 644, "qty": 10})
    assert response.status_code == 200
    assert "Target build" in response.text
    # The depth-1 tiers: the producer blueprint, the buildable input,
    # the raw input with its adjusted quantity (the golden chain).
    assert "Typhoon Blueprint" in response.text
    assert "Capital Power Generator" in response.text
    assert "68,571,360" in response.text
    assert "Tritanium" in response.text
    # The owned-copies overlay and the Calculate bar.
    assert "Owned copies of Typhoon Blueprint" in response.text
    assert "Calculate" in response.text
    # Participants: the default pool (corp members) with the main.
    assert "Test Pilot" in response.text and "Corp Mate" in response.text


@respx.mock
async def test_planner_invalid_target_redirects(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner", params={"target": 34}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/planner"


@respx.mock
async def test_planner_clamps_qty(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner", params={"target": 644, "qty": 0})
    assert response.status_code == 200
    assert "×1" in response.text  # qty floor is 1


@respx.mock
async def test_planner_participants_param(client, planner_db):  # noqa: F811
    await _login(client)
    # An explicit empty pool: the `?p=` sentinel means nobody.
    response = await client.get("/planner", params={"target": 644, "p": ""})
    assert response.status_code == 200
    # No gate-holding participant remains for the time readout.
    response = await client.get("/planner/plan", params={"target": 644, "p": ""})
    assert response.status_code == 200
    assert "No participants in the pool" in response.text

    # An explicit single-participant pool narrows the time table.
    response = await client.get("/planner/plan", params={"target": 644, "p": MAIN})
    assert response.status_code == 200
    assert "Corp Mate" not in response.text


@respx.mock
async def test_plan_page_renders_calculation(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner/plan", params={"target": 644, "qty": 10})
    assert response.status_code == 200
    assert "Build Plan — Typhoon ×10" in response.text
    assert "Draft" in response.text
    # The golden values from the plan suite: adjusted materials, the
    # install cost, and the per-participant time table.
    assert "68,571,360" in response.text
    assert "958,869.37" in response.text
    assert "48,568" in response.text or "13.5 h" in response.text
    assert "Test Pilot" in response.text


@respx.mock
async def test_plan_page_without_target_redirects(client, planner_db):  # noqa: F811
    await _login(client)
    response = await client.get("/planner/plan", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/planner"


@respx.mock
async def test_planner_facility_override_and_default(client, planner_db):  # noqa: F811
    """A facility param overrides the registry default; an invalid id
    falls back to it (the server never trusts link construction)."""
    from sqlalchemy import text

    await _login(client)
    base = await client.get("/planner", params={"target": 644})
    assert base.status_code == 200

    # An invalid registration id: ignored, default resolution stands.
    bogus = await client.get(
        "/planner", params={"target": 644, "manufacturing": 99999}
    )
    assert bogus.status_code == 200

    # The seeded registration's id resolves as an explicit override.
    registration_id = (
        await planner_db.execute(
            text(
                "SELECT id FROM structure_registrations"
                " WHERE activity = 'manufacturing'"
            )
        )
    ).scalar_one()
    overridden = await client.get(
        "/planner", params={"target": 644, "manufacturing": registration_id}
    )
    assert overridden.status_code == 200


@respx.mock
async def test_plan_page_renders_chain_surfaces(client, chain_db):  # noqa: F811
    """The M5 chain surfaces: the flow strip, the phase tree with
    computed stage states, the chain-wide blueprint overlay with its
    exceptions, and the acquisition table's gaps-only default."""
    await _login(client)
    response = await client.get("/planner/plan", params={"target": 644, "qty": 10})
    assert response.status_code == 200

    # The flow strip: one card per buildable phase, target at Phase 4.
    assert "Phase 1" in response.text and "Phase 4" in response.text
    # The phase tree: computed stage states and gating reasons.
    assert "Ready to build" in response.text and "Missing inputs" in response.text
    assert "waiting on phase 3" in response.text
    assert "no skilled character in the pool" in response.text
    # The chain-wide blueprint overlay: all four types owned, the
    # BPC-only CPG as the exception with its run-coverage shortfall.
    assert "4 / 4 blueprints owned" in response.text
    assert "Owned · BPC only" in response.text
    assert "short of the 157-run need by 146" in response.text
    # The acquisition table: Tritanium's gap shows by default (the
    # office's 2M covered, the main's personal stock not measured).
    assert "Raw materials — acquisition" in response.text
    assert "Tritanium" in response.text
    assert "short 66,582,789" in response.text


@respx.mock
async def test_plan_page_acquisition_toggle(client, chain_db):  # noqa: F811
    """The gaps-only default hides covered terminators; `all=1` shows
    them, and the toggle link flips the param (absence-means-default)."""
    await _login(client)
    gaps = await client.get("/planner/plan", params={"target": 644, "qty": 10})
    assert gaps.status_code == 200
    # The covered ice product hides; the footer counts it.
    assert "Test Ice Product" not in gaps.text
    assert "1 type fully covered — hidden in this view" in gaps.text
    assert "Show all 2 types" in gaps.text

    everything = await client.get(
        "/planner/plan", params={"target": 644, "qty": 10, "all": "1"}
    )
    assert everything.status_code == 200
    assert "Test Ice Product" in everything.text
    assert "100%" in everything.text
    assert "Gaps only" in everything.text
    # The toggle link back drops the param entirely.
    assert "all=1" not in everything.text.split("Gaps only")[0][-600:]


@respx.mock
async def test_planner_renders_deepened_tiers(client, chain_db):  # noqa: F811
    """The requirement overview deepened to the full chain: every
    buildable node's blueprint, intermediates grouped by phase, and the
    full-chain terminators by category."""
    await _login(client)
    response = await client.get("/planner", params={"target": 644, "qty": 10})
    assert response.status_code == 200
    # Tier 1: chain-wide blueprints (4 buildable nodes).
    assert "4 types" in response.text
    assert "4 / 4 owned" in response.text
    assert "Test Fuel Block Blueprint" in response.text
    # Tier 2: intermediates grouped by phase, titled by the modal
    # invGroups name (the owner's call over commodity names).
    assert "phase 1 — Fuel Block" in response.text
    assert "phase 4 — Battleship" in response.text
    assert "phase 3 — Capital Component" in response.text
    # Tier 3: full-chain terminators by category.
    assert "Minerals" in response.text and "Ice products" in response.text
    assert "68,582,789" in response.text


@respx.mock
async def test_personal_stock_param_threads_into_coverage(client, chain_db):  # noqa: F811
    """The `ps` URL param (personal-stock characters, backend plumbing
    for the upcoming Material sources selector — no UI ships yet)
    threads through both pages into the coverage measurement: the
    Tritanium gap shrinks by exactly the listed characters' personal
    stock, and ids outside the participant pool are ignored."""
    await _login(client)
    default = await client.get("/planner/plan", params={"target": 644, "qty": 10})
    assert default.status_code == 200
    assert "short 66,582,789" in default.text

    main_counted = await client.get(
        "/planner/plan", params=[("target", 644), ("qty", 10), ("ps", 1234)]
    )
    assert main_counted.status_code == 200
    assert "short 65,582,789" in main_counted.text

    both = await client.get(
        "/planner/plan",
        params=[("target", 644), ("qty", 10), ("ps", 1234), ("ps", 5678)],
    )
    assert both.status_code == 200
    assert "short 65,082,789" in both.text

    # Outside the pool: no effect even in a hand-built URL.
    outside = await client.get(
        "/planner/plan", params=[("target", 644), ("qty", 10), ("ps", 9999)]
    )
    assert outside.status_code == 200
    assert "short 66,582,789" in outside.text
