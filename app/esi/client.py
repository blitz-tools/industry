"""Authenticated ESI data client with transparent token refresh.

Call sites ask for data (`await esi.get(character, "/characters/{character_id}/wallet/")`)
and never touch tokens directly; refresh-on-expiry with SSO v2 rotation is
handled here. Rate-limit (X-Esi-Error-Limit-*) and ETag awareness will hook
into `_request` later without changing call sites.
"""

import asyncio
from datetime import timedelta
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..db import utc_now
from ..models import Character
from .sso import SSOClient, SSOTokenError

# Refresh this many seconds before actual expiry, to avoid sending a token
# that expires mid-flight.
EXPIRY_SKEW_SECONDS = 60

# Per-character refresh locks. EVE SSO v2 rotates refresh tokens: two
# concurrent refreshes with the same token make the second fail with
# invalid_grant. Single-process only — revisit if we ever run multiple
# uvicorn workers.
_refresh_locks: dict[int, asyncio.Lock] = {}


def _lock_for(character_id: int) -> asyncio.Lock:
    lock = _refresh_locks.get(character_id)
    if lock is None:
        lock = _refresh_locks[character_id] = asyncio.Lock()
    return lock


class ReauthorizationRequired(Exception):
    """The stored refresh token is dead; the user must authorize again."""


class ESIError(Exception):
    """ESI returned an error response."""


class ESIClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        settings: Settings,
        db: AsyncSession,
    ):
        self._http = http
        self._settings = settings
        self._db = db
        self._sso = SSOClient(http, settings)

    async def get(
        self,
        character: Character,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """GET an authenticated ESI endpoint. `path` may contain
        "{character_id}", formatted with the character's ID."""
        path = path.format(character_id=character.character_id)
        url = f"{self._settings.esi_base_url}{path}"
        token = await self.ensure_access_token(character)
        response = await self._request(url, token, params)
        if response.status_code == 401:
            # Token revoked server-side; force one refresh and retry once.
            token = await self.ensure_access_token(character, force=True)
            response = await self._request(url, token, params)
        if response.status_code >= 400:
            raise ESIError(
                f"ESI {response.status_code} for {path}: {response.text[:200]}"
            )
        return response.json()

    async def get_wallet_balance(self, character: Character) -> float:
        """Demo endpoint proving the full token chain: bare JSON number."""
        return float(await self.get(character, "/characters/{character_id}/wallet/"))

    async def ensure_access_token(
        self, character: Character, *, force: bool = False
    ) -> str:
        """Return a valid access token, refreshing (and persisting the
        rotated refresh token) when expired or when forced."""
        if not force and self._is_fresh(character):
            return character.access_token
        async with _lock_for(character.character_id):
            # Double-checked locking: another coroutine may have refreshed
            # while we waited on the lock.
            if not force and self._is_fresh(character):
                return character.access_token
            try:
                tokens = await self._sso.refresh(character.refresh_token)
            except SSOTokenError as exc:
                if exc.status_code == 400:
                    raise ReauthorizationRequired(
                        f"refresh token rejected for {character.name}"
                    ) from exc
                raise
            character.access_token = tokens.access_token
            character.refresh_token = tokens.refresh_token  # rotation
            character.access_token_expires_at = utc_now() + timedelta(
                seconds=tokens.expires_in
            )
            self._db.add(character)
            await self._db.commit()
            return character.access_token

    def _is_fresh(self, character: Character) -> bool:
        return (
            character.access_token_expires_at - timedelta(seconds=EXPIRY_SKEW_SECONDS)
            > utc_now()
        )

    async def _request(
        self, url: str, token: str, params: dict[str, Any] | None
    ) -> httpx.Response:
        # Future home of ETag cache headers and error-limit tracking.
        return await self._http.get(
            url, params=params, headers={"Authorization": f"Bearer {token}"}
        )
