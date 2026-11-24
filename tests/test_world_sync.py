"""Public world-state sync tests (the M15 framework slice): cold pulls,
ETag revalidation, error preservation, the never-raising tick, and the
admin status surface. ESI is respx-mocked; the ETag mechanics reuse the
hardening suite's Past/Future-Expires pattern."""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from sqlalchemy import func, select

from app.esi.client import ESIClient
from app.esi.world import (
    KIND_COST_INDICES,
    KIND_MARKET_PRICES,
    PUBLIC_OWNER_ID,
    PUBLIC_OWNER_TYPE,
    sync_cost_indices,
    sync_market_prices,
    world_sync_tick,
)
from app.models import CostIndex, DataSync, MarketPrice
from tests.conftest import TEST_SETTINGS, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
SYSTEMS_URL = "https://esi.test/latest/industry/systems/"
PRICES_URL = "https://esi.test/latest/markets/prices/"

PAST_EXPIRES = "Thu, 01 Jan 2026 00:00:00 GMT"
FUTURE_EXPIRES = "Wed, 01 Jan 2031 00:00:00 GMT"

SYSTEMS_BODY = [
    {
        "solar_system_id": 30002510,
        "cost_indices": [
            # ESI's own activity strings, stored verbatim (the enum pin).
            {"activity": "manufacturing", "cost_index": 0.0046},
            {"activity": "reaction", "cost_index": 0.0017},
        ],
    },
    {
        "solar_system_id": 30002670,
        "cost_indices": [
            {"activity": "manufacturing", "cost_index": 0.0014},
        ],
    },
]

PRICES_BODY = [
    {"type_id": 34, "adjusted_price": 2.7, "average_price": 2.6},
    # average_price absent — the column is nullable, consumers degrade.
    {"type_id": 9836, "adjusted_price": 1213.0},
]


def _make_esi(app, db_session) -> ESIClient:
    return ESIClient(
        app.state.http,
        TEST_SETTINGS,
        db_session,
        clock=app.state.esi_clock,
        limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


async def _sync_row(db_session, kind: str) -> DataSync | None:
    return await db_session.get(DataSync, (kind, PUBLIC_OWNER_TYPE, PUBLIC_OWNER_ID))


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


@respx.mock
async def test_cold_pull_populates_tables_and_records_ok(app, db_session):
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY)
    respx.get(PRICES_URL).respond(json=PRICES_BODY)

    indices = await sync_cost_indices(db_session, _make_esi(app, db_session))
    prices = await sync_market_prices(db_session, _make_esi(app, db_session))

    assert indices.status == "synced" and indices.item_count == 3
    assert prices.status == "synced" and prices.item_count == 2

    rows = (
        (
            await db_session.execute(
                select(CostIndex.system_id, CostIndex.activity, CostIndex.cost_index)
                .order_by(CostIndex.system_id, CostIndex.activity)
            )
        ).all()
    )
    # Verbatim activity strings from ESI's enum, values untouched.
    assert rows == [
        (30002510, "manufacturing", pytest.approx(0.0046)),
        (30002510, "reaction", pytest.approx(0.0017)),
        (30002670, "manufacturing", pytest.approx(0.0014)),
    ]
    price = await db_session.get(MarketPrice, 9836)
    assert price is not None
    assert price.adjusted_price == pytest.approx(1213.0)
    assert price.average_price is None  # absent in the payload, not zero

    for kind in (KIND_COST_INDICES, KIND_MARKET_PRICES):
        sync = await _sync_row(db_session, kind)
        assert sync is not None and sync.status == "ok"


@respx.mock
async def test_etag_revalidation_preserves_rows(app, db_session):
    systems = respx.get(SYSTEMS_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json=SYSTEMS_BODY,
                headers={"ETag": '"sys-v1"', "Expires": PAST_EXPIRES},
            ),
            httpx.Response(304, headers={"ETag": '"sys-v1"', "Expires": FUTURE_EXPIRES}),
        ]
    )
    respx.get(PRICES_URL).respond(json=[])

    first = await sync_cost_indices(db_session, _make_esi(app, db_session))
    second = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert first.status == second.status == "synced"
    assert systems.call_count == 2  # the second pass revalidated, not refetched
    assert systems.calls.last.request.headers["If-None-Match"] == '"sys-v1"'

    count = (
        await db_session.execute(select(func.count()).select_from(CostIndex))
    ).scalar_one()
    assert count == 3  # the cached snapshot re-landed intact
    sync = await _sync_row(db_session, KIND_COST_INDICES)
    assert sync is not None and sync.status == "ok"


@respx.mock
async def test_esi_error_records_error_and_preserves_snapshot(app, db_session):
    respx.get(SYSTEMS_URL).mock(
        side_effect=[
            httpx.Response(200, json=SYSTEMS_BODY),
            # 500 is not retryable: raises straight through.
            httpx.Response(500, json={"error": "boom"}),
        ]
    )
    respx.get(PRICES_URL).respond(json=[])

    first = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert first.status == "synced"
    second = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert second.status == "error"
    assert "500" in (second.detail or "")

    # The previous snapshot survived the failed pull.
    count = (
        await db_session.execute(select(func.count()).select_from(CostIndex))
    ).scalar_one()
    assert count == 3
    sync = await _sync_row(db_session, KIND_COST_INDICES)
    assert sync is not None and sync.status == "error"
    assert sync.detail is not None


@respx.mock
async def test_world_sync_tick_never_raises(app):
    # ESI entirely unreachable: the tick records errors internally and
    # returns normally — the loop must survive outages.
    respx.get(SYSTEMS_URL).mock(side_effect=httpx.ConnectError("down"))
    respx.get(PRICES_URL).mock(side_effect=httpx.ConnectError("down"))
    await world_sync_tick(app.state.session_factory, app.state.http, TEST_SETTINGS)


@respx.mock
async def test_admin_sync_page_lists_families(app, client, db_session):
    await _login(client)
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY)
    respx.get(PRICES_URL).respond(json=PRICES_BODY)
    esi = _make_esi(app, db_session)
    await sync_cost_indices(db_session, esi)
    await sync_market_prices(db_session, esi)

    response = await client.get("/admin/sync")
    assert response.status_code == 200
    assert "Cost indices" in response.text and "Market prices" in response.text
    assert "3" in response.text and "2" in response.text  # row counts

    run = await client.post("/admin/sync/run", follow_redirects=False)
    assert run.status_code == 303
    assert run.headers["location"] == "/admin/sync"
