"""SSO client unit tests: authorize URL, JWT decoding, token exchange."""

from urllib.parse import parse_qs

import httpx
import pytest
import respx

from app.esi.sso import SSOClient, SSOError, decode_access_token
from tests.conftest import TEST_SETTINGS, make_access_token


@pytest.fixture
def sso():
    return SSOClient(httpx.AsyncClient(), TEST_SETTINGS)


def test_authorize_url_contains_required_params(sso):
    url = httpx.URL(sso.authorize_url("some-state"))
    assert str(url).startswith("https://sso.test/v2/oauth/authorize")
    params = url.params
    assert params["response_type"] == "code"
    assert params["client_id"] == "test-client-id"
    assert params["redirect_uri"] == "http://testserver/auth/eve/callback"
    assert params["scope"] == (
        "publicData esi-wallet.read_character_wallet.v1 esi-assets.read_assets.v1"
    )
    assert params["state"] == "some-state"


def test_decode_access_token_parses_claims():
    token = make_access_token(
        character_id=987, name="A Pilot", owner="hash-x", scopes=["publicData"]
    )
    claims = decode_access_token(token)
    assert claims.character_id == 987
    assert claims.name == "A Pilot"
    assert claims.owner_hash == "hash-x"
    assert claims.scopes == ["publicData"]


def test_decode_access_token_handles_bare_string_scope():
    claims = decode_access_token(make_access_token(scopes="publicData"))
    assert claims.scopes == ["publicData"]


def test_decode_access_token_rejects_stale_token():
    token = make_access_token(expires_in=-60)
    with pytest.raises(SSOError):
        decode_access_token(token)


def test_decode_access_token_rejects_unexpected_sub():
    import jwt as pyjwt

    token = pyjwt.encode({"sub": "CORPORATION:EVE:1"}, key="0" * 32, algorithm="HS256")
    with pytest.raises(SSOError):
        decode_access_token(token)


@respx.mock
async def test_exchange_code_posts_correct_grant(sso):
    route = respx.post("https://sso.test/v2/oauth/token").respond(
        json={
            "access_token": make_access_token(),
            "refresh_token": "R1",
            "expires_in": 1199,
        }
    )
    tokens = await sso.exchange_code("the-code")
    assert tokens.refresh_token == "R1"
    assert tokens.expires_in == 1199

    request = route.calls.last.request
    assert request.headers["Authorization"].startswith("Basic ")
    body = parse_qs(request.read().decode())
    assert body["grant_type"] == ["authorization_code"]
    assert body["code"] == ["the-code"]
    assert body["redirect_uri"] == ["http://testserver/auth/eve/callback"]


@respx.mock
async def test_refresh_posts_rotated_grant(sso):
    route = respx.post("https://sso.test/v2/oauth/token").respond(
        json={"access_token": "A2", "refresh_token": "R2", "expires_in": 1199}
    )
    tokens = await sso.refresh("R1")
    assert tokens.access_token == "A2"
    body = parse_qs(route.calls.last.request.read().decode())
    assert body["grant_type"] == ["refresh_token"]
    assert body["refresh_token"] == ["R1"]


@respx.mock
async def test_token_error_surfaces_status(sso):
    respx.post("https://sso.test/v2/oauth/token").respond(
        status_code=400, json={"error": "invalid_grant"}
    )
    with pytest.raises(SSOError) as excinfo:
        await sso.refresh("dead-token")
    assert "invalid_grant" in str(excinfo.value)
