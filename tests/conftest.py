"""Shared fixtures: in-memory DB, test app, mocked SSO/ESI, JWT factory."""

import os

# app.main instantiates a module-level app (for `uvicorn app.main:app`),
# which loads Settings from the environment. Keep tests hermetic when no
# .env exists; explicit TEST_SETTINGS below overrides everything anyway.
os.environ.setdefault("ESI_CLIENT_ID", "conftest-placeholder")
os.environ.setdefault("ESI_CLIENT_SECRET", "conftest-placeholder")
os.environ.setdefault("SECRET_KEY", "conftest-placeholder-secret")

import time

import httpx
import jwt
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (register models)
from app.config import Settings
from app.db import Base
from app.main import create_app

TEST_SETTINGS = Settings(
    esi_client_id="test-client-id",
    esi_client_secret="test-client-secret",
    esi_callback_url="http://testserver/auth/eve/callback",
    esi_scopes=["publicData", "esi-wallet.read_character_wallet.v1"],
    base_url="http://testserver",
    secret_key="test-secret-key",
    database_url="sqlite+aiosqlite://",
    # Point SSO/ESI at hosts respx mocks.
    sso_base_url="https://sso.test",
    esi_base_url="https://esi.test/latest",
)


def make_access_token(
    character_id: int = 1234,
    name: str = "Test Pilot",
    owner: str = "owner-hash-1",
    scopes: list[str] | str | None = None,
    expires_in: int = 1200,
) -> str:
    """Fabricate an SSO v2 access-token JWT. Decoding is unverified, so any
    signature works; scopes exercise both the list and bare-string forms."""
    if scopes is None:
        scopes = ["publicData", "esi-wallet.read_character_wallet.v1"]
    now = int(time.time())
    payload = {
        "sub": f"CHARACTER:EVE:{character_id}",
        "name": name,
        "owner": owner,
        "scp": scopes,
        "iss": "login.eveonline.com",
        "exp": now + expires_in,
        "jti": "test-jti",
    }
    # 32-byte key: PyJWT warns on short HMAC keys even for throwaway tokens.
    return jwt.encode(payload, key="0" * 32, algorithm="HS256")


def token_response(
    character_id: int = 1234,
    owner: str = "owner-hash-1",
    name: str = "Test Pilot",
    access_token: str | None = None,
    refresh_token: str = "R1",
    expires_in: int = 1200,
) -> dict:
    return {
        "access_token": access_token or make_access_token(character_id, name, owner),
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "token_type": "Bearer",
    }


@pytest_asyncio.fixture
async def app():
    """App wired to a fresh in-memory database per test.

    ASGITransport does not run the lifespan, so the shared httpx client the
    lifespan would create is provided here directly; respx intercepts it
    regardless of which client instance makes the call.
    """
    application = create_app(TEST_SETTINGS)
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # keeps the shared :memory: database alive
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    application.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    application.state.http = httpx.AsyncClient()
    yield application
    await application.state.http.aclose()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(app):
    """Browser-like client that carries the session cookie."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest_asyncio.fixture
async def db_session(app):
    """Direct DB access for seeding and asserting rows."""
    async with app.state.session_factory() as session:
        yield session
