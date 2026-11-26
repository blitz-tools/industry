"""Observability telemetry tests (M15): verbatim rate-limit header
recording off every ESI response, per-kind sync-run history for all
sync kinds (public, character, corporation — the one stored dataset),
the headroom query layer, and the Admin > Observability page. ESI is
respx-mocked; the ETag mechanics reuse the world-sync suite's
Past/Future-Expires pattern."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from sqlalchemy import func, select, text

from app.charts import chart_data, line_chart, sparkline
from app.db import utc_now
from app.esi.assets import (
    KIND_CHAR_ASSETS,
    sync_all_characters,
    sync_corporation,
)
from app.esi.client import ESIClient
from app.esi.telemetry import (
    error_limit_history,
    error_limit_pct_used,
    latest_error_limit,
    latest_sync_runs,
    parse_rate_limit,
    prune_telemetry,
    rate_group_headroom,
    rate_group_history,
    sync_duration_history,
)
from app.esi.universe import UniverseResolver
from app.esi.world import (
    KIND_COST_INDICES,
    PUBLIC_OWNER_ID,
    PUBLIC_OWNER_TYPE,
    sync_cost_indices,
    sync_market_prices,
)
from app.models import Character, CostIndex, RateLimitObservation, SyncRun
from tests.conftest import TEST_SETTINGS, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
SYSTEMS_URL = "https://esi.test/latest/industry/systems/"
PRICES_URL = "https://esi.test/latest/markets/prices/"

PAST_EXPIRES = "Thu, 01 Jan 2026 00:00:00 GMT"
FUTURE_EXPIRES = "Wed, 31 Jan 2031 00:00:00 GMT"

SYSTEMS_BODY = [
    {
        "solar_system_id": 30002510,
        "cost_indices": [
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
    {"type_id": 9836, "adjusted_price": 1213.0},
]

# The full rate-control header set, both families at once (the limiter
# tolerates this defensively; so does the recorder). The limit is ESI's
# compound "max/window" string — never an integer on the wire.
RATE_HEADERS = {
    "X-Ratelimit-Group": "markets",
    "X-Ratelimit-Limit": "100/15m",
    "X-Ratelimit-Remaining": "38",
    "X-Ratelimit-Used": "2",
    "X-Esi-Error-Limit-Remain": "84",
    "X-Esi-Error-Limit-Reset": "120.5",
}

CHAR_ID = 1234
MAIN_ID = 5678
CORP_ID = 98000001

ALL_CHAR_SCOPES = (
    "publicData esi-assets.read_assets.v1 esi-characters.read_blueprints.v1 "
    "esi-skills.read_skills.v1 esi-characters.read_loyalty.v1 "
    "esi-industry.read_character_jobs.v1"
)
ALL_CORP_SCOPES = (
    "publicData esi-characters.read_corporation_roles.v1 "
    "esi-assets.read_corporation_assets.v1 "
    "esi-corporations.read_blueprints.v1 "
    "esi-industry.read_corporation_jobs.v1"
)


def _make_esi(app, db_session) -> ESIClient:
    return ESIClient(
        app.state.http,
        TEST_SETTINGS,
        db_session,
        clock=app.state.esi_clock,
        limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


async def _seed_character(
    db_session,
    character_id: int = CHAR_ID,
    name: str = "Test Pilot",
    scopes: str = ALL_CHAR_SCOPES,
) -> Character:
    character = Character(
        character_id=character_id,
        name=name,
        owner_hash=f"owner-{character_id}",
        scopes=scopes,
        access_token=f"tok-{character_id}",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token=f"R-{character_id}",
    )
    db_session.add(character)
    await db_session.commit()
    return character


async def _observations(db_session) -> list[RateLimitObservation]:
    return list(
        (
            await db_session.execute(
                select(RateLimitObservation).order_by(RateLimitObservation.id)
            )
        )
        .scalars()
        .all()
    )


async def _runs(db_session, kind: str | None = None) -> list[SyncRun]:
    query = select(SyncRun).order_by(SyncRun.id)
    if kind is not None:
        query = query.where(SyncRun.kind == kind)
    return list((await db_session.execute(query)).scalars().all())


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


# --- Block A: rate-limit recording (the client hook) ---


@respx.mock
async def test_rate_limit_headers_recorded_verbatim(app, db_session):
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY, headers=RATE_HEADERS)

    outcome = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert outcome.status == "synced"

    rows = await _observations(db_session)
    assert len(rows) == 1
    obs = rows[0]
    assert obs.group == "markets"
    # The compound limit stays a verbatim string — parsing is the query
    # layer's job, never the write's.
    assert obs.rate_limit == "100/15m"
    assert obs.rate_remaining == 38
    assert obs.rate_used == 2
    assert obs.error_limit_remain == 84
    assert obs.error_limit_reset == pytest.approx(120.5)
    assert obs.status_code == 200
    assert obs.path == "/industry/systems/"
    assert obs.owner_id == 0  # the public owner made the request


@respx.mock
async def test_legacy_error_family_only(app, db_session):
    respx.get(SYSTEMS_URL).respond(
        json=SYSTEMS_BODY,
        headers={"X-Esi-Error-Limit-Remain": "60", "X-Esi-Error-Limit-Reset": "30"},
    )

    await sync_cost_indices(db_session, _make_esi(app, db_session))

    rows = await _observations(db_session)
    assert len(rows) == 1
    assert rows[0].group is None
    assert rows[0].rate_limit is None
    assert rows[0].rate_remaining is None
    assert rows[0].rate_used is None
    assert rows[0].error_limit_remain == 60


@respx.mock
async def test_rate_group_family_only(app, db_session):
    respx.get(SYSTEMS_URL).respond(
        json=SYSTEMS_BODY,
        headers={
            "X-Ratelimit-Group": "assets",
            "X-Ratelimit-Limit": "90/1h",
            "X-Ratelimit-Remaining": "70",
            "X-Ratelimit-Used": "2",
        },
    )

    await sync_cost_indices(db_session, _make_esi(app, db_session))

    rows = await _observations(db_session)
    assert len(rows) == 1
    assert rows[0].group == "assets"
    assert rows[0].rate_limit == "90/1h"
    assert rows[0].error_limit_remain is None
    assert rows[0].error_limit_reset is None


@respx.mock
async def test_headerless_response_records_nothing(app, db_session):
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY)

    await sync_cost_indices(db_session, _make_esi(app, db_session))

    assert await _observations(db_session) == []


@respx.mock
async def test_rate_limit_recording_never_raises(app, db_session):
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY, headers=RATE_HEADERS)
    # Break the telemetry table so the recorder's commit fails inside its
    # own guard: the failure must be swallowed, the session rolled back
    # to usable, and the sync's own writes must survive.
    await db_session.execute(text("DROP TABLE rate_limit_observations"))
    await db_session.commit()

    outcome = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert outcome.status == "synced" and outcome.item_count == 3
    count = (
        await db_session.execute(select(func.count()).select_from(CostIndex))
    ).scalar_one()
    assert count == 3  # the snapshot landed despite the telemetry failure


@respx.mock
async def test_revalidation_records_each_response_per_request_used(
    app, db_session
):
    # A 200 then its 304 revalidation: two real responses, two rows, each
    # carrying its own single-request X-Ratelimit-Used (never cumulative).
    respx.get(SYSTEMS_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json=SYSTEMS_BODY,
                headers={"ETag": '"sys-v1"', "Expires": PAST_EXPIRES, **RATE_HEADERS},
            ),
            httpx.Response(
                304,
                headers={
                    "ETag": '"sys-v1"',
                    "Expires": FUTURE_EXPIRES,
                    "X-Ratelimit-Group": "markets",
                    "X-Ratelimit-Limit": "100/15m",
                    "X-Ratelimit-Remaining": "60",
                    "X-Ratelimit-Used": "1",
                },
            ),
        ]
    )
    respx.get(PRICES_URL).respond(json=[])

    first = await sync_cost_indices(db_session, _make_esi(app, db_session))
    second = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert first.status == second.status == "synced"

    rows = await _observations(db_session)
    assert len(rows) == 2
    assert [row.status_code for row in rows] == [200, 304]
    assert [row.rate_used for row in rows] == [2, 1]


@respx.mock
async def test_malformed_limit_stored_verbatim(app, db_session):
    respx.get(SYSTEMS_URL).respond(
        json=SYSTEMS_BODY,
        headers={
            "X-Ratelimit-Group": "markets",
            "X-Ratelimit-Limit": "garbage",
            "X-Ratelimit-Remaining": "38",
        },
    )

    await sync_cost_indices(db_session, _make_esi(app, db_session))

    rows = await _observations(db_session)
    assert len(rows) == 1
    assert rows[0].rate_limit == "garbage"  # mirrored, not dropped
    assert parse_rate_limit("garbage") is None
    assert parse_rate_limit(None) is None
    assert parse_rate_limit("150/15m") == (150, timedelta(minutes=15))
    assert parse_rate_limit("90/1h") == (90, timedelta(hours=1))


# --- Block B: sync-run history (the public kinds) ---


@respx.mock
async def test_sync_run_recorded_with_duration(app, db_session):
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY)
    respx.get(PRICES_URL).respond(json=PRICES_BODY)

    await sync_cost_indices(db_session, _make_esi(app, db_session))
    await sync_market_prices(db_session, _make_esi(app, db_session))

    runs = await _runs(db_session, KIND_COST_INDICES)
    assert len(runs) == 1
    run = runs[0]
    assert run.owner_type == PUBLIC_OWNER_TYPE
    assert run.owner_id == PUBLIC_OWNER_ID
    assert run.status == "ok"
    assert run.duration_ms is not None and run.duration_ms >= 0
    assert run.item_count == 3
    assert run.started_at is not None
    assert run.detail is None


@respx.mock
async def test_sync_run_error_path(app, db_session):
    respx.get(SYSTEMS_URL).mock(
        side_effect=[
            httpx.Response(200, json=SYSTEMS_BODY),
            httpx.Response(500, json={"error": "boom"}),
        ]
    )

    first = await sync_cost_indices(db_session, _make_esi(app, db_session))
    second = await sync_cost_indices(db_session, _make_esi(app, db_session))
    assert first.status == "synced" and second.status == "error"

    runs = await _runs(db_session, KIND_COST_INDICES)
    assert len(runs) == 2
    assert runs[0].status == "ok"
    assert runs[1].status == "error"
    assert "500" in (runs[1].detail or "")
    assert runs[1].duration_ms is not None and runs[1].duration_ms >= 0


@respx.mock
async def test_repeated_syncs_append_history(app, db_session):
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY)

    await sync_cost_indices(db_session, _make_esi(app, db_session))
    await sync_cost_indices(db_session, _make_esi(app, db_session))

    assert len(await _runs(db_session, KIND_COST_INDICES)) == 2  # not an upsert


# --- Block C: character and corporation kinds join the one dataset ---


@respx.mock
async def test_every_sync_kind_writes_sync_runs(app, db_session):
    character = await _seed_character(db_session, CHAR_ID, "Test Pilot")
    main = await _seed_character(db_session, MAIN_ID, "Main Pilot", ALL_CORP_SCOPES)
    main.is_main = True
    main.corporation_id = CORP_ID
    await db_session.commit()

    base = "https://esi.test/latest"
    # Character kinds (empty payloads keep universe resolution a no-op).
    for path in (
        "assets",
        "blueprints",
        "loyalty/points",
        "industry/jobs",
    ):
        respx.get(f"{base}/characters/{CHAR_ID}/{path}/").respond(json=[])
    respx.get(f"{base}/characters/{CHAR_ID}/skills/").respond(json={"skills": []})
    # Corporation kinds: the role gate plus the three corp endpoints.
    respx.get(f"{base}/characters/{MAIN_ID}/roles/").respond(
        json={"roles": ["Director"]}
    )
    for path in ("assets", "blueprints", "industry/jobs"):
        respx.get(f"{base}/corporations/{CORP_ID}/{path}/").respond(json=[])

    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    await sync_all_characters(db_session, esi, [character], resolver=resolver)
    corp_outcomes = await sync_corporation(db_session, esi, resolver=resolver)
    assert corp_outcomes is not None
    assert all(o.status == "synced" for o in corp_outcomes)

    runs = await _runs(db_session)
    by_key = {(run.kind, run.owner_type, run.owner_id): run for run in runs}
    # Every kind records the data_syncs/asset_syncs vocabulary — "ok" on
    # success (the in-memory SyncOutcome's "synced" never reaches storage).
    for kind in (
        "char-assets",
        "char-blueprints",
        "char-skills",
        "char-loyalty",
        "char-jobs",
    ):
        run = by_key.get((kind, "character", CHAR_ID))
        assert run is not None, kind
        assert run.status == "ok"
        assert run.duration_ms is not None and run.duration_ms >= 0
    for kind in ("corp-assets", "corp-blueprints", "corp-jobs"):
        run = by_key.get((kind, "corporation", CORP_ID))
        assert run is not None, kind
        assert run.status == "ok"
        assert run.duration_ms is not None and run.duration_ms >= 0


@respx.mock
async def test_scope_gate_records_sync_run(app, db_session):
    character = await _seed_character(db_session, CHAR_ID, scopes="publicData")

    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    await sync_all_characters(db_session, esi, [character], resolver=resolver)

    runs = await _runs(db_session, KIND_CHAR_ASSETS)
    assert len(runs) == 1
    run = runs[0]
    assert run.owner_type == "character" and run.owner_id == CHAR_ID
    assert run.status == "no-scope"
    assert run.duration_ms is not None and run.duration_ms >= 0
    assert "esi-assets.read_assets.v1" in (run.detail or "")


# --- Block D: the query layer ---


async def test_latest_sync_runs_filters_and_selects_latest(db_session):
    now = utc_now()

    def run(kind, owner_type, owner_id, status, hours_ago):
        return SyncRun(
            kind=kind,
            owner_type=owner_type,
            owner_id=owner_id,
            status=status,
            duration_ms=1,
            started_at=now - timedelta(hours=hours_ago),
        )

    db_session.add_all(
        [
            run("char-skills", "character", 1, "synced", 2),
            run("char-skills", "character", 1, "error", 1),  # newer: wins
            run("char-skills", "character", 2, "synced", 1),
            run("corp-jobs", "corporation", 9, "synced", 0),
        ]
    )
    await db_session.commit()

    latest = await latest_sync_runs(db_session)
    assert {(r.kind, r.owner_type, r.owner_id) for r in latest} == {
        ("char-skills", "character", 1),
        ("char-skills", "character", 2),
        ("corp-jobs", "corporation", 9),
    }
    by_key = {(r.kind, r.owner_type, r.owner_id): r for r in latest}
    assert by_key[("char-skills", "character", 1)].status == "error"

    char_only = await latest_sync_runs(db_session, owner_type="character")
    assert len(char_only) == 2
    assert all(r.owner_type == "character" for r in char_only)

    skills = await latest_sync_runs(db_session, kinds=["char-skills"])
    assert len(skills) == 2
    assert all(r.kind == "char-skills" for r in skills)


async def test_rate_group_headroom_latest_per_group(db_session):
    now = utc_now()

    def obs(group, minutes_ago, *, rate_limit, remaining, used):
        return RateLimitObservation(
            observed_at=now - timedelta(minutes=minutes_ago),
            status_code=200,
            group=group,
            rate_limit=rate_limit,
            rate_remaining=remaining,
            rate_used=used,
            path="/x/",
            owner_id=0,
        )

    db_session.add_all(
        [
            obs("markets", 10, rate_limit="150/15m", remaining=140, used=2),
            obs("markets", 1, rate_limit="150/15m", remaining=57, used=2),
            # No parseable limit: the meter degrades, remaining still shown.
            obs("contracts", 0, rate_limit=None, remaining=10, used=2),
        ]
    )
    await db_session.commit()

    headroom = {h.group: h for h in await rate_group_headroom(db_session)}
    markets = headroom["markets"]
    assert markets.limit_raw == "150/15m"
    assert markets.max_tokens == 150
    assert markets.window == timedelta(minutes=15)
    assert markets.remaining == 57  # the newer observation won
    assert markets.pct_used == 62.0  # (150 - 57) / 150, the gate number
    contracts = headroom["contracts"]
    assert contracts.max_tokens is None
    assert contracts.pct_used is None
    assert contracts.remaining == 10


async def test_window_used_cross_check_sums_trailing_window(db_session):
    now = utc_now()

    def obs(minutes_ago, used):
        return RateLimitObservation(
            observed_at=now - timedelta(minutes=minutes_ago),
            status_code=200,
            group="markets",
            rate_limit="100/1h",
            rate_remaining=50,
            rate_used=used,
            path="/x/",
            owner_id=0,
        )

    db_session.add_all(
        [
            obs(5, 2),
            obs(5, 5),
            obs(5, 1),
            obs(120, 4),  # outside the 1h window: excluded
        ]
    )
    await db_session.commit()

    (headroom,) = await rate_group_headroom(db_session)
    assert headroom.window_used == 8


async def test_latest_error_limit(db_session):
    now = utc_now()

    def obs(minutes_ago, remain):
        return RateLimitObservation(
            observed_at=now - timedelta(minutes=minutes_ago),
            status_code=200,
            group=None,
            error_limit_remain=remain,
            path="/x/",
            owner_id=0,
        )

    db_session.add_all([obs(3, 80), obs(1, 90)])
    # A newer observation without the legacy family must not win.
    db_session.add(
        RateLimitObservation(
            observed_at=now, status_code=200, group="markets", path="/x/", owner_id=0
        )
    )
    await db_session.commit()

    latest = await latest_error_limit(db_session)
    assert latest is not None and latest.error_limit_remain == 90
    # Percentage toward the documented budget (100 = the 420 penalty):
    # derived at read time from the documented ~100/window maximum.
    assert error_limit_pct_used(latest) == 10.0
    assert error_limit_pct_used(None) is None
    assert error_limit_pct_used(obs(0, 100)) == 0.0


async def test_prune_telemetry_bounds_growth(db_session):
    now = utc_now()
    old_obs = RateLimitObservation(
        observed_at=now - timedelta(days=8), status_code=200, path="/x/", owner_id=0
    )
    new_obs = RateLimitObservation(
        observed_at=now - timedelta(days=1), status_code=200, path="/x/", owner_id=0
    )
    old_run = SyncRun(
        kind="char-skills",
        owner_type="character",
        owner_id=1,
        status="synced",
        started_at=now - timedelta(days=40),
    )
    new_run = SyncRun(
        kind="char-skills",
        owner_type="character",
        owner_id=1,
        status="synced",
        started_at=now - timedelta(days=1),
    )
    db_session.add_all([old_obs, new_obs, old_run, new_run])
    await db_session.commit()

    await prune_telemetry(db_session)

    assert [row.id for row in await _observations(db_session)] == [new_obs.id]
    assert [row.id for row in await _runs(db_session)] == [new_run.id]


# --- Block E: the Admin > Observability page ---


# --- Over-time views: the history queries and the SVG charts ---


async def test_rate_group_history_per_observation(db_session):
    now = utc_now()

    def obs(minutes_ago, group, rate_limit, remaining):
        return RateLimitObservation(
            observed_at=now - timedelta(minutes=minutes_ago),
            status_code=200,
            group=group,
            rate_limit=rate_limit,
            rate_remaining=remaining,
            path="/x/",
            owner_id=0,
        )

    db_session.add_all(
        [
            obs(10, "markets", "100/15m", 90),  # 10% used
            obs(5, "markets", "100/15m", 50),  # 50% used
            obs(3, "markets", "garbage", 50),  # unparseable: skipped
            obs(1, "assets", "200/15m", 100),  # 50% used
        ]
    )
    await db_session.commit()

    history = await rate_group_history(db_session)
    assert [pct for _, pct in history["markets"]] == [10.0, 50.0]
    assert [pct for _, pct in history["assets"]] == [50.0]


async def test_error_limit_history(db_session):
    now = utc_now()
    db_session.add_all(
        [
            RateLimitObservation(
                observed_at=now - timedelta(minutes=2),
                status_code=200,
                error_limit_remain=80,
                path="/x/",
                owner_id=0,
            ),
            RateLimitObservation(
                observed_at=now - timedelta(minutes=1),
                status_code=200,
                error_limit_remain=90,
                path="/x/",
                owner_id=0,
            ),
        ]
    )
    await db_session.commit()
    assert [pct for _, pct in await error_limit_history(db_session)] == [20.0, 10.0]


async def test_sync_duration_history_filters(db_session):
    now = utc_now()

    def run(kind, owner_type, started_at, duration_ms):
        return SyncRun(
            kind=kind,
            owner_type=owner_type,
            owner_id=1,
            status="ok",
            duration_ms=duration_ms,
            started_at=started_at,
        )

    db_session.add_all(
        [
            run("cost-indices", "public", now - timedelta(hours=2), 1500),
            run("cost-indices", "public", now - timedelta(hours=1), 500),
            run("char-skills", "character", now, 100),
            # No duration: excluded from the chart feed.
            SyncRun(
                kind="market-prices",
                owner_type="public",
                owner_id=0,
                status="ok",
                started_at=now,
            ),
        ]
    )
    await db_session.commit()

    history = await sync_duration_history(db_session, owner_type="public")
    assert sorted(history) == ["cost-indices"]
    assert [secs for _, secs in history["cost-indices"]] == [1.5, 0.5]
    filtered = await sync_duration_history(db_session, kinds=["char-skills"])
    assert sorted(filtered) == ["char-skills"]


def test_sparkline_renders_trend():
    now = utc_now()
    points = [(now - timedelta(minutes=m), float(m)) for m in (10, 5, 0)]
    svg = sparkline(points, unit="%")
    assert '<svg class="sparkline"' in svg
    assert "<polyline" in svg and "stroke-width=\"2\"" in svg
    assert "<circle" in svg  # the accent end dot with its surface ring
    assert 'aria-label="trend: latest 0 %, range 0 to 10 %"' in svg
    # Flat and single-point series degrade to a centered line, not a crash.
    assert "<polyline" in sparkline([(now, 5.0)])
    assert sparkline([]) == ""


def test_line_chart_renders_series_grid_and_data_twin():
    now = utc_now()
    series = [
        {
            "name": "Cost indices",
            "hue": "#1f99b0",
            "points": [(now - timedelta(hours=1), 0.5), (now, 1.5)],
        },
        {
            "name": "Market prices",
            "hue": "#a8942a",
            "points": [(now - timedelta(hours=1), 1.0), (now, 0.25)],
        },
    ]
    svg = line_chart(series, y_unit=" s", value_format="{:.2f}")
    assert svg.count("<polyline") == 2  # one line per series
    assert svg.count("chart-tick") >= 5  # y ticks + x ticks
    assert 'class="chart-crosshair"' in svg
    assert "1.50 s" in svg and "0.25 s" in svg  # selective end labels
    # The JSON twin carries the drawn pixel coordinates and values.
    data = chart_data(series, y_unit=" s", value_format="{:.2f}")
    assert [s["name"] for s in data["series"]] == ["Cost indices", "Market prices"]
    last = data["series"][0]["points"][-1]
    assert last["value"] == "1.50 s"
    assert last["x"] > data["series"][0]["points"][0]["x"]  # time runs right
    assert line_chart([]) == ""


@respx.mock
async def test_admin_observability_page_renders(app, client, db_session):
    await _login(client)
    respx.get(SYSTEMS_URL).respond(json=SYSTEMS_BODY, headers=RATE_HEADERS)
    respx.get(PRICES_URL).respond(json=PRICES_BODY)
    esi = _make_esi(app, db_session)
    await sync_cost_indices(db_session, esi)
    await sync_market_prices(db_session, esi)

    response = await client.get("/admin/sync")
    assert response.status_code == 200
    text = response.text
    assert "Observability" in text
    assert ">Observability</a>" in text  # the nav entry renamed
    assert "Cost indices" in text and "Market prices" in text
    assert "Rate-limit headroom" in text
    assert "markets" in text  # the group name from the live headers
    assert "62.0% of window used" in text  # (100 - 38) / 100 tokens
    # The legacy error budget gets the same percentage treatment
    # (84 of the documented ~100 remaining → 16% consumed).
    assert "legacy error-limit budget — 16.0% used (84/100 remaining)" in text
    # Over-time views: the durations chart with its legend, JSON twin,
    # and table view; sparklines beside the headroom meters.
    assert "Sync durations over time" in text
    assert 'class="line-chart"' in text
    assert '<span class="chart-legend-item">' in text
    assert "#1f99b0" in text  # the validated series hue, in the legend key
    assert "application/json" in text
    assert "Table view" in text
    assert 'class="sparkline"' in text
    assert "never rides its rate limits" in text
    assert "just now" in text  # format_age, never a raw datetime
    assert "resets" not in text  # the group family has no reset header
    # The Database section: storage facts and per-table row counts.
    assert "Database" in text
    assert "journal mode" in text
    assert "esi_cache" in text  # a table row from the live counts

    run = await client.post("/admin/sync/run", follow_redirects=False)
    assert run.status_code == 303
    assert run.headers["location"] == "/admin/sync"


@respx.mock
async def test_admin_observability_character_panels(app, client, db_session):
    await _login(client)  # creates character 1234 "Test Pilot"
    # Seeded runs (not a live sync): the page groups per owner into
    # expanding panels — the roster's corp-row presentation.
    now = utc_now()
    db_session.add_all(
        [
            SyncRun(
                kind="char-skills",
                owner_type="character",
                owner_id=CHAR_ID,
                status="ok",
                duration_ms=132,
                item_count=306,
                started_at=now - timedelta(minutes=1),
            ),
            SyncRun(
                kind="char-jobs",
                owner_type="character",
                owner_id=CHAR_ID,
                status="error",
                duration_ms=40,
                detail="ESI 500",
                started_at=now,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/admin/sync")
    assert response.status_code == 200
    text = response.text
    assert 'details class="corp-row obs-owner" data-owner="character-1234"' in text
    assert "Test Pilot" in text
    assert "2 kinds" in text
    assert "Skills" in text and "Jobs" in text
    # The summary chip carries the owner's worst kind status.
    assert '<span class="job-status failed">error</span>' in text
    assert "observability.js" in text


@respx.mock
async def test_admin_observability_page_empty(app, client):
    await _login(client)

    response = await client.get("/admin/sync")
    assert response.status_code == 200
    text = response.text
    assert "never" in text
    assert "meter-fill" not in text
    assert "no observations yet" in text


async def test_sqlite_stats_reads_pages_and_counts(db_session):
    from app.db import sqlite_stats

    stats = await sqlite_stats(db_session, "sqlite+aiosqlite://")
    # In-memory engine: page stats and counts read, file sizes absent.
    assert stats["file_bytes"] is None
    assert stats["wal_bytes"] is None
    assert stats["journal_mode"] == "memory"
    assert stats["used_bytes"] > 0
    names = {table["name"]: table["rows"] for table in stats["tables"]}
    assert names.get("sync_runs") == 0
    assert stats["total_rows"] == sum(names.values())
