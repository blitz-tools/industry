"""Authenticated ESI data client with transparent token refresh, ETag
caching, and rate-limit awareness.

Call sites ask for data (`await esi.get(character, "/characters/{character_id}/wallet/")`)
and never touch tokens, ETags, or back-off directly. Request minimization:
a fresh-window cache hit makes zero HTTP calls; expired entries revalidate
with If-None-Match (304s are free on both of ESI's rate-control systems);
the limiter pauses before requests when ESI says we should slow down.
"""

import asyncio
import json
import random
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..db import utc_now
from ..models import Character
from .clock import Clock, RealClock
from .etag import ETagCache, make_key, parse_http_date
from .limiter import ESILimiter, header_float
from .sso import SSOClient, SSOTokenError

# Refresh this many seconds before actual expiry, to avoid sending a token
# that expires mid-flight.
EXPIRY_SKEW_SECONDS = 60

# Initial attempt plus this many retries for transient failures.
MAX_ATTEMPTS = 4
RETRY_BACKOFF_BASE = 0.5
RETRY_BACKOFF_CAP = 30.0
# 429/502/503/504 are documented as "not bugs — retry later"; 520 is ESI's
# internal rate limit. Other 4xx never retry (except the one-shot 401
# token-refresh retry, which is not backoff).
RETRYABLE_STATUSES = {420, 429, 502, 503, 504, 520}

# Per-character refresh locks. EVE SSO v2 rotates refresh tokens: two
# concurrent refreshes with the same token make the second fail with
# invalid_grant. Single-process only — revisit if we ever run multiple
# uvicorn workers.
_refresh_locks: dict[int, asyncio.Lock] = {}

# Module-level limiter default (single-process; see ESILimiter docstring).
_default_limiter = ESILimiter(RealClock())


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
        *,
        clock: Clock | None = None,
        limiter: ESILimiter | None = None,
        jitter: Callable[[], float] | None = None,
    ):
        self._http = http
        self._settings = settings
        self._db = db
        self._sso = SSOClient(http, settings)
        self._clock = clock or RealClock()
        self._limiter = limiter or _default_limiter
        self._jitter = jitter or (lambda: random.uniform(0.0, 0.25))
        self._cache = ETagCache(db, self._clock)
        # Route group memory: the X-Ratelimit-Group for a path is only known
        # after a response, so remember it to gate retries of the same path.
        self._route_groups: dict[str, str] = {}

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
        key = make_key(character.character_id, path, params)

        cached = await self._cache.get(key)
        if cached is not None and self._cache.is_fresh(cached):
            # Fresh window: the server's Expires header says newer data is
            # not available. Re-requesting would circumvent ESI's caching.
            return json.loads(cached.body)

        token = await self.ensure_access_token(character)
        etag = cached.etag if cached is not None else None
        refreshed_401 = False
        response: httpx.Response | None = None
        for attempt in range(MAX_ATTEMPTS):
            await self._limiter.wait_if_paused(self._route_groups.get(path))
            try:
                response = await self._request(url, token, params, etag)
            except httpx.HTTPError as exc:
                if attempt == MAX_ATTEMPTS - 1:
                    raise ESIError(f"ESI unreachable for {path}: {exc}") from exc
                await self._clock.sleep(self._backoff_delay(attempt))
                continue
            self._limiter.observe(response)
            group = response.headers.get("X-Ratelimit-Group")
            if group is not None:
                self._route_groups[path] = group

            if response.status_code == 304 and cached is not None:
                # Revalidated: keep body and ETag, refresh the expiry window
                # from the 304's own Expires header.
                await self._cache.store(
                    key,
                    character_id=character.character_id,
                    path=path,
                    params=params,
                    body=cached.body,
                    etag=cached.etag,
                    expires_at=parse_http_date(response.headers.get("Expires"))
                    or cached.expires_at,
                    last_modified=cached.last_modified,
                )
                return json.loads(cached.body)
            if response.status_code == 200:
                await self._cache.store(
                    key,
                    character_id=character.character_id,
                    path=path,
                    params=params,
                    body=response.text,
                    etag=response.headers.get("ETag"),
                    expires_at=parse_http_date(response.headers.get("Expires")),
                    last_modified=parse_http_date(response.headers.get("Last-Modified")),
                )
                return response.json()
            if response.status_code == 401 and not refreshed_401:
                # Token revoked server-side; force one refresh and retry.
                # This is not backoff and never repeats.
                refreshed_401 = True
                token = await self.ensure_access_token(character, force=True)
                continue
            if response.status_code == 304:
                # Stray 304 with no cached row: drop the ETag and refetch.
                etag = None
                cached = None
                continue
            if response.status_code == 420:
                # observe() already set the global pause from Reset; the
                # loop gate sleeps before the next attempt.
                continue
            if response.status_code == 429:
                self._limiter.pause_for_retry_after(header_float(response, "Retry-After"))
                continue
            if response.status_code in RETRYABLE_STATUSES:
                await self._clock.sleep(self._backoff_delay(attempt))
                continue
            raise ESIError(
                f"ESI {response.status_code} for {path}: {response.text[:200]}"
            )
        last = response.status_code if response is not None else "unreachable"
        raise ESIError(
            f"ESI gave up on {path} after {MAX_ATTEMPTS} attempts (last: {last})"
        )

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

    def _backoff_delay(self, attempt: int) -> float:
        delay = min(RETRY_BACKOFF_BASE * 2**attempt, RETRY_BACKOFF_CAP)
        return delay + self._jitter()

    async def _request(
        self,
        url: str,
        token: str,
        params: dict[str, Any] | None,
        etag: str | None = None,
    ) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {token}",
            # ESI best practices: identify the app so CCP can make contact.
            "User-Agent": self._settings.esi_user_agent,
        }
        if etag is not None:
            headers["If-None-Match"] = etag
        return await self._http.get(url, params=params, headers=headers)
