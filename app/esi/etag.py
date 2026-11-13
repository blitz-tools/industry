"""DB-backed ESI response cache: ETag revalidation and Expires fresh windows.

CCP's ETag best practices: store the ETag with the body independent of cache
timers (expired data is revalidated with the old ETag, not dropped), and do
not re-request before the Expires header allows — circumventing ESI caching
is a bannable offense, so the fresh window is compliance, not optimization.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EsiCache
from .clock import Clock

# Cached rows older than this are pruned opportunistically on store().
CACHE_TTL_DAYS = 14


def canonical_params(params: dict[str, Any] | None) -> str:
    """Deterministic serialization for cache keys — never str(params)."""
    return json.dumps(params or {}, sort_keys=True, separators=(",", ":"))


def make_key(character_id: int, path: str, params: dict[str, Any] | None) -> str:
    """Cache key: sha256 of character + path + canonical params.

    character_id is included explicitly (it also appears in authenticated
    paths) so unauthenticated routes key correctly too.
    """
    material = f"{character_id}\n{path}\n{canonical_params(params)}"
    return hashlib.sha256(material.encode()).hexdigest()


def parse_http_date(value: str | None) -> datetime | None:
    """Parse an HTTP date header to naive UTC; None for missing/garbage."""
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone(UTC).replace(tzinfo=None)


class ETagCache:
    def __init__(self, db: AsyncSession, clock: Clock):
        self._db = db
        self._clock = clock

    async def get(self, key: str) -> EsiCache | None:
        return await self._db.get(EsiCache, key)

    async def store(
        self,
        key: str,
        *,
        character_id: int,
        path: str,
        body: str,
        etag: str | None,
        expires_at: datetime | None,
        last_modified: datetime | None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Upsert a cache entry and prune stale rows."""
        entry = await self._db.get(EsiCache, key)
        if entry is None:
            entry = EsiCache(key=key)
            self._db.add(entry)
        entry.character_id = character_id
        entry.path = path
        entry.params_json = canonical_params(params)
        entry.body = body
        entry.etag = etag
        entry.expires_at = expires_at
        entry.last_modified = last_modified
        await self._db.commit()

        # Opportunistic housekeeping keeps the table bounded; disposable data.
        cutoff = self._clock.now() - timedelta(days=CACHE_TTL_DAYS)
        await self._db.execute(delete(EsiCache).where(EsiCache.updated_at < cutoff))
        await self._db.commit()

    def is_fresh(self, entry: EsiCache) -> bool:
        """True while the server's Expires window still covers us."""
        return entry.expires_at is not None and entry.expires_at > self._clock.now()


async def purge_character(db: AsyncSession, character_id: int) -> None:
    """Drop all cached rows for a character (e.g. after an owner transfer)."""
    await db.execute(delete(EsiCache).where(EsiCache.character_id == character_id))
    await db.commit()
