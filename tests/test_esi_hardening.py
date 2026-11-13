"""ESI client hardening tests: ETag caching, limiter pauses, back-off.

All sleeps go through the app fixture's FakeClock, so pauses are recorded,
never waited out. Directly-constructed clients (for exact backoff timing)
inject zero jitter.
"""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from sqlalchemy import select

from app.esi.client import ESIClient, ESIError
from app.esi.etag import make_key, parse_http_date
from app.esi.limiter import ESILimiter
from app.models import Character, EsiCache
from tests.conftest import TEST_SETTINGS, token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
WALLET_URL = "https://esi.test/latest/characters/1234/wallet/"
ASSETS_URL = "https://esi.test/latest/characters/1234/assets/"

PAST_EXPIRES = "Thu, 01 Jan 2026 00:00:00 GMT"
FUTURE_EXPIRES = "Wed, 01 Jan 2031 00:00:00 GMT"


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


def _make_client(app, db_session) -> ESIClient:
    """Direct client with zero jitter, for exact backoff assertions."""
    return ESIClient(
        app.state.http,
        TEST_SETTINGS,
        db_session,
        clock=app.state.esi_clock,
        limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


async def _get_character(db_session) -> Character:
    character = await db_session.get(Character, 1234)
    assert character is not None
    return character


# --- ETag caching ---------------------------------------------------------


@respx.mock
async def test_second_call_sends_if_none_match(client, db_session):
    await _login(client)
    wallet = respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json=4321.5,
                headers={"ETag": '"wallet-v1"', "Expires": PAST_EXPIRES},
            ),
            httpx.Response(304, headers={"ETag": '"wallet-v1"'}),
        ]
    )

    first = await client.get("/dashboard")
    second = await client.get("/dashboard")
    assert "4,321.50" in first.text
    assert "4,321.50" in second.text

    assert wallet.call_count == 2
    assert wallet.calls.last.request.headers["If-None-Match"] == '"wallet-v1"'


@respx.mock
async def test_fresh_window_makes_no_request(client):
    await _login(client)
    wallet = respx.get(WALLET_URL).respond(json=99.0, headers={"Expires": FUTURE_EXPIRES})

    assert "99.00" in (await client.get("/dashboard")).text
    assert "99.00" in (await client.get("/dashboard")).text
    assert "99.00" in (await client.get("/dashboard")).text
    assert wallet.call_count == 1  # the fresh window served the rest


@respx.mock
async def test_304_refreshes_expiry_window(client):
    await _login(client)
    wallet = respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(
                200, json=1.0, headers={"ETag": '"w"', "Expires": PAST_EXPIRES}
            ),
            httpx.Response(304, headers={"ETag": '"w"', "Expires": FUTURE_EXPIRES}),
        ]
    )

    await client.get("/dashboard")  # 200: store body + ETag
    await client.get("/dashboard")  # 304: revalidate, refresh expiry
    await client.get("/dashboard")  # fresh window: no request
    assert wallet.call_count == 2


@respx.mock
async def test_stray_304_without_cache_refetches(app, client, db_session):
    await _login(client)
    wallet = respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(304, headers={"ETag": '"w"'}),
            httpx.Response(200, json=7.0),
        ]
    )
    esi = _make_client(app, db_session)
    character = await _get_character(db_session)

    result = await esi.get(character, "/characters/{character_id}/wallet/")
    assert result == 7.0
    assert wallet.call_count == 2


@respx.mock
async def test_params_keying_produces_distinct_rows(app, client, db_session):
    await _login(client)
    respx.get(url__startswith=ASSETS_URL).respond(json=[])
    esi = _make_client(app, db_session)
    character = await _get_character(db_session)

    await esi.get(character, "/characters/{character_id}/assets/", params={"page": 1})
    await esi.get(character, "/characters/{character_id}/assets/", params={"page": 2})

    rows = (await db_session.execute(select(EsiCache))).scalars().all()
    assert sorted(r.params_json for r in rows) == ['{"page":1}', '{"page":2}']


def test_make_key_ignores_param_order():
    assert make_key(1, "/p", {"a": 1, "b": 2}) == make_key(1, "/p", {"b": 2, "a": 1})
    assert make_key(1, "/p", {"a": 1}) != make_key(2, "/p", {"a": 1})


def test_parse_http_date():
    parsed = parse_http_date("Thu, 01 Jan 2026 00:00:00 GMT")
    assert parsed is not None and parsed.year == 2026 and parsed.tzinfo is None
    assert parse_http_date(None) is None
    assert parse_http_date("garbage") is None


# --- Limiter and back-off -------------------------------------------------


@respx.mock
async def test_error_limit_pause_before_next_request(client, fake_clock):
    await _login(client)
    respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json=1.0,
                headers={
                    "X-Esi-Error-Limit-Remain": "10",
                    "X-Esi-Error-Limit-Reset": "30",
                },
            ),
            httpx.Response(200, json=2.0),
        ]
    )

    await client.get("/dashboard")
    assert fake_clock.sleeps == []  # nothing paused before the first request

    await client.get("/dashboard")
    # Remain <= floor paused us for Reset + skew.
    assert len(fake_clock.sleeps) == 1
    assert 30 <= fake_clock.sleeps[0] <= 32


@respx.mock
async def test_420_sets_global_pause_from_reset(client, fake_clock):
    await _login(client)
    wallet = respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(420, headers={"X-Esi-Error-Limit-Reset": "20"}),
            httpx.Response(200, json=3.0),
        ]
    )

    response = await client.get("/dashboard")
    assert "3.00" in response.text
    assert wallet.call_count == 2
    assert len(fake_clock.sleeps) == 1
    assert 20 <= fake_clock.sleeps[0] <= 22


@respx.mock
async def test_429_respects_retry_after(client, fake_clock):
    await _login(client)
    respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "5"}),
            httpx.Response(200, json=4.0),
        ]
    )
    assert "4.00" in (await client.get("/dashboard")).text
    assert len(fake_clock.sleeps) == 1
    assert 5 <= fake_clock.sleeps[0] <= 7


@respx.mock
async def test_429_without_headers_uses_default_pause(client, fake_clock):
    await _login(client)
    respx.get(WALLET_URL).mock(
        side_effect=[httpx.Response(429), httpx.Response(200, json=4.0)]
    )
    assert "4.00" in (await client.get("/dashboard")).text
    assert len(fake_clock.sleeps) == 1
    assert 4 <= fake_clock.sleeps[0] <= 8


@respx.mock
async def test_5xx_exponential_backoff_then_success(app, client, db_session, fake_clock):
    await _login(client)
    wallet = respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, json=5.0),
        ]
    )
    esi = _make_client(app, db_session)
    character = await _get_character(db_session)

    result = await esi.get(character, "/characters/{character_id}/wallet/")
    assert result == 5.0
    assert wallet.call_count == 3
    assert fake_clock.sleeps == [0.5, 1.0]  # base * 2**attempt, zero jitter


@respx.mock
async def test_persistent_5xx_gives_up_after_max_attempts(
    app, client, db_session, fake_clock
):
    await _login(client)
    wallet = respx.get(WALLET_URL).respond(status_code=503)
    esi = _make_client(app, db_session)
    character = await _get_character(db_session)

    with pytest.raises(ESIError, match="gave up"):
        await esi.get(character, "/characters/{character_id}/wallet/")
    assert wallet.call_count == 4


@respx.mock
async def test_client_error_never_retries(app, client, db_session, fake_clock):
    await _login(client)
    wallet = respx.get(WALLET_URL).respond(status_code=404, json={"error": "not found"})
    esi = _make_client(app, db_session)
    character = await _get_character(db_session)

    with pytest.raises(ESIError, match="404"):
        await esi.get(character, "/characters/{character_id}/wallet/")
    assert wallet.call_count == 1
    assert fake_clock.sleeps == []


@respx.mock
async def test_mid_flight_401_refreshes_token_and_retries(client, db_session):
    await _login(client)
    respx.post(SSO_TOKEN_URL).respond(
        json={"access_token": "A2", "refresh_token": "R2", "expires_in": 1199}
    )
    wallet = respx.get(WALLET_URL).mock(
        side_effect=[
            httpx.Response(401, json={"error": "invalid_token"}),
            httpx.Response(200, json=6.0),
        ]
    )

    assert "6.00" in (await client.get("/dashboard")).text
    assert wallet.call_count == 2
    assert wallet.calls.last.request.headers["Authorization"] == "Bearer A2"


# --- Limiter unit tests ---------------------------------------------------


def test_limiter_observes_error_limit_headers(fake_clock):
    limiter = ESILimiter(fake_clock)
    limiter.observe(
        httpx.Response(
            200,
            headers={"X-Esi-Error-Limit-Remain": "5", "X-Esi-Error-Limit-Reset": "45"},
        )
    )
    assert fake_clock.sleeps == []  # observing alone does not sleep


async def test_limiter_waits_for_global_pause(fake_clock):
    limiter = ESILimiter(fake_clock)
    limiter.observe(
        httpx.Response(
            200,
            headers={"X-Esi-Error-Limit-Remain": "5", "X-Esi-Error-Limit-Reset": "45"},
        )
    )
    await limiter.wait_if_paused()
    assert len(fake_clock.sleeps) == 1
    assert 45 <= fake_clock.sleeps[0] <= 47


async def test_limiter_group_pause_is_not_global(fake_clock):
    limiter = ESILimiter(fake_clock)
    limiter.observe(
        httpx.Response(
            200,
            headers={
                "X-Ratelimit-Group": "assets",
                "X-Ratelimit-Remaining": "3",
            },
        )
    )
    # A different group (and the global check) must not wait.
    await limiter.wait_if_paused("wallets")
    await limiter.wait_if_paused()
    assert fake_clock.sleeps == []
    # The paused group does wait.
    await limiter.wait_if_paused("assets")
    assert len(fake_clock.sleeps) == 1


def test_limiter_tolerates_missing_and_garbage_headers(fake_clock):
    limiter = ESILimiter(fake_clock)
    limiter.observe(httpx.Response(200))  # no headers at all
    limiter.observe(httpx.Response(200, headers={"X-Esi-Error-Limit-Remain": "garbage"}))
    limiter.observe(httpx.Response(420, headers={"X-Esi-Error-Limit-Reset": "garbage"}))
