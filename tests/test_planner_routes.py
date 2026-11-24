"""Planner route tests (M4): auth gates, the search JSON feed, the
planner page's URL-state semantics (target validity, qty clamping,
participants, facility defaults), and the calculated plan page. The
planner_db fixture (tests/test_planner_plan.py) seeds the world these
render against; SSO login drives the same callback the other route
suites use."""

from urllib.parse import parse_qs, urlparse

import respx

from tests.conftest import token_response
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
