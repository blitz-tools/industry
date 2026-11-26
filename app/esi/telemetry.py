"""ESI observability telemetry (M15): rate-control header observations
and sync-run history, persisted for the Admin > Observability page.

Storage follows the band's mirror philosophy: rows carry what the server
said, verbatim — the X-Ratelimit floating-window family (Group/Limit/
Remaining/Used) and the legacy error-limit family (Remain/Reset), either
or both per response — plus the client-side correlation keys (path,
owner). Interpretation (headroom percentages, window sums, staleness)
lives in this module's query functions, never in the writers. Record
shapes stay OTel-convention-friendly: one row is one HTTP observation
with attributes (group, path, owner, status) and measurements.

Two ESI-docs facts the derivations honor (developers.eveonline.com,
rate-limiting): X-Ratelimit-Limit is a compound "max/window" string
("150/15m"), and X-Ratelimit-Used is the single request's token cost
(2XX=2, 3XX=1, 4XX=5 with 429 exempt, 5XX=0) — never cumulative. The
server's own Remaining against the parsed max is the headroom number;
the trailing-window sum of Used is an app-side cross-check only.

Never-raise contract: recording and pruning swallow their failures (a
poisoned shared session is rolled back so the sync's own writes
survive). Single-process like the sync locks and the default limiter.

Local storage only; Prometheus/Loki/Thanos export and OpenTelemetry
tracing are future work (TODO.md).
"""

import contextlib
import logging
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import utc_now
from ..models import RateLimitObservation, SyncRun
from .limiter import header_float, header_int

logger = logging.getLogger(__name__)

# Retention: rate windows are minutes long, so a week is ample trend;
# sync-run history wants a month of cadence to eyeball. Not Settings —
# nothing deployment-tunable about either.
RATE_LIMIT_RETENTION_DAYS = 7
SYNC_RUN_RETENTION_DAYS = 30

# "150/15m" — max tokens, window size (m = minutes, h = hours).
_RATE_LIMIT_RE = re.compile(r"^(\d+)/(\d+)([mh])$")


def monotonic_start() -> int:
    """Start a duration measurement (monotonic, immune to wall-clock
    jumps). Durations are operational facts, not app-time logic — the
    injectable Clock stays out of it."""
    return time.monotonic_ns()


def elapsed_ms(start_ns: int) -> int:
    return (time.monotonic_ns() - start_ns) // 1_000_000


async def record_rate_limit(
    db: AsyncSession,
    response: httpx.Response,
    *,
    path: str,
    owner_id: int,
) -> None:
    """Append one verbatim rate-control observation for an ESI response.

    Skips responses that said nothing rate-related (all six values
    absent). Never raises; commits immediately like ETagCache.store —
    nothing else is pending on the shared session mid-fetch.
    """
    group = response.headers.get("X-Ratelimit-Group")
    rate_limit = response.headers.get("X-Ratelimit-Limit")
    rate_remaining = header_int(response, "X-Ratelimit-Remaining")
    rate_used = header_int(response, "X-Ratelimit-Used")
    error_remain = header_int(response, "X-Esi-Error-Limit-Remain")
    error_reset = header_float(response, "X-Esi-Error-Limit-Reset")
    if (
        group is None
        and rate_limit is None
        and rate_remaining is None
        and rate_used is None
        and error_remain is None
        and error_reset is None
    ):
        return
    try:
        db.add(
            RateLimitObservation(
                observed_at=utc_now(),
                status_code=response.status_code,
                group=group,
                rate_limit=rate_limit,
                rate_remaining=rate_remaining,
                rate_used=rate_used,
                error_limit_remain=error_remain,
                error_limit_reset=error_reset,
                path=path,
                owner_id=owner_id,
            )
        )
        await db.commit()
    except Exception:
        logger.warning("rate-limit telemetry recording failed", exc_info=True)
        with contextlib.suppress(Exception):
            await db.rollback()


async def record_sync_run(
    db: AsyncSession,
    *,
    kind: str,
    owner_type: str,
    owner_id: int,
    status: str,
    duration_ms: int | None = None,
    item_count: int | None = None,
    detail: str | None = None,
) -> None:
    """Append one sync-run history row. `started_at` anchors on the run's
    start (finish derives); error runs that end as fast as they began
    still carry a meaningful timestamp. Never raises."""
    started_at = utc_now()
    if duration_ms is not None:
        started_at -= timedelta(milliseconds=duration_ms)
    try:
        db.add(
            SyncRun(
                kind=kind,
                owner_type=owner_type,
                owner_id=owner_id,
                status=status,
                duration_ms=duration_ms,
                item_count=item_count,
                detail=detail,
                started_at=started_at,
            )
        )
        await db.commit()
    except Exception:
        logger.warning("sync-run telemetry recording failed", exc_info=True)
        with contextlib.suppress(Exception):
            await db.rollback()


async def prune_telemetry(db: AsyncSession) -> None:
    """Delete observations and runs past their retention windows.
    Never raises; rides the world tick (which runs unconditionally,
    unlike the roster-gated character tick)."""
    try:
        rate_cutoff = utc_now() - timedelta(days=RATE_LIMIT_RETENTION_DAYS)
        run_cutoff = utc_now() - timedelta(days=SYNC_RUN_RETENTION_DAYS)
        await db.execute(
            delete(RateLimitObservation).where(
                RateLimitObservation.observed_at < rate_cutoff
            )
        )
        await db.execute(delete(SyncRun).where(SyncRun.started_at < run_cutoff))
        await db.commit()
    except Exception:
        logger.warning("telemetry pruning failed", exc_info=True)
        with contextlib.suppress(Exception):
            await db.rollback()


async def latest_sync_runs(
    db: AsyncSession,
    *,
    owner_type: str | None = None,
    kinds: Sequence[str] | None = None,
) -> list[SyncRun]:
    """Latest run per (kind, owner_type, owner_id) — the Observability
    page's family rows. The filters are the subset rule's mechanism:
    page-filtered views (the markets sync panel, later) pass their own
    kind list; the central page passes nothing."""
    query = select(SyncRun).order_by(SyncRun.started_at, SyncRun.id)
    if owner_type is not None:
        query = query.where(SyncRun.owner_type == owner_type)
    if kinds is not None:
        query = query.where(SyncRun.kind.in_(kinds))
    runs = (await db.execute(query)).scalars().all()
    latest: dict[tuple[str, str, int], SyncRun] = {}
    for run in runs:  # ascending: later rows overwrite earlier ones
        latest[(run.kind, run.owner_type, run.owner_id)] = run
    return sorted(
        latest.values(), key=lambda run: (run.owner_type, run.owner_id, run.kind)
    )


def parse_rate_limit(value: str | None) -> tuple[int, timedelta] | None:
    """ESI's compound limit string "150/15m" to (max tokens, window).
    Tolerant like header_int: a malformed value never breaks a render."""
    if value is None:
        return None
    match = _RATE_LIMIT_RE.match(value.strip())
    if match is None:
        return None
    max_tokens = int(match.group(1))
    size = int(match.group(2))
    window = (
        timedelta(minutes=size) if match.group(3) == "m" else timedelta(hours=size)
    )
    return max_tokens, window


@dataclass
class RateGroupHeadroom:
    """One rate group's derived headroom, from its latest observation."""

    group: str
    # The verbatim "150/15m" string the server sent.
    limit_raw: str | None
    max_tokens: int | None
    window: timedelta | None
    remaining: int | None
    # The gate number: 100 * (max - remaining) / max, from the latest
    # observation — the server maintains the floating window and the
    # bucket holds only this app's traffic, so Remaining is
    # authoritative. None when the limit is missing or unparseable.
    pct_used: float | None
    # Cross-check: tokens this app burned in the trailing window (sum
    # of per-request Used). App-side bookkeeping, never the gate number
    # — a mismatch between the two is itself signal.
    window_used: int | None
    observed_at: datetime


async def rate_group_headroom(db: AsyncSession) -> list[RateGroupHeadroom]:
    """Headroom per X-Ratelimit-Group: the latest observation's parsed
    limit and remaining, plus the trailing-window Used sum."""
    observations = (
        await db.execute(
            select(RateLimitObservation)
            .where(RateLimitObservation.group.is_not(None))
            .order_by(RateLimitObservation.observed_at, RateLimitObservation.id)
        )
    ).scalars().all()
    latest: dict[str, RateLimitObservation] = {}
    for obs in observations:  # ascending: later rows overwrite earlier ones
        latest[obs.group] = obs
    now = utc_now()
    result = []
    for group, obs in latest.items():
        parsed = parse_rate_limit(obs.rate_limit)
        max_tokens = parsed[0] if parsed is not None else None
        window = parsed[1] if parsed is not None else None
        pct_used = None
        if max_tokens and obs.rate_remaining is not None:
            used = max(0, max_tokens - obs.rate_remaining)
            pct_used = round(100 * used / max_tokens, 1)
        window_used = None
        if window is not None:
            cutoff = now - window
            window_used = sum(
                other.rate_used or 0
                for other in observations
                if other.group == group and other.observed_at >= cutoff
            )
        result.append(
            RateGroupHeadroom(
                group=group,
                limit_raw=obs.rate_limit,
                max_tokens=max_tokens,
                window=window,
                remaining=obs.rate_remaining,
                pct_used=pct_used,
                window_used=window_used,
                observed_at=obs.observed_at,
            )
        )
    return sorted(result, key=lambda headroom: headroom.group)


async def latest_error_limit(db: AsyncSession) -> RateLimitObservation | None:
    """The latest observation carrying the legacy error-limit remainder
    (that budget is global, not per group)."""
    return (
        await db.execute(
            select(RateLimitObservation)
            .where(RateLimitObservation.error_limit_remain.is_not(None))
            .order_by(
                RateLimitObservation.observed_at.desc(),
                RateLimitObservation.id.desc(),
            )
            .limit(1)
        )
    ).scalar_one_or_none()


async def rate_group_history(
    db: AsyncSession,
) -> dict[str, list[tuple[datetime, float]]]:
    """Per group, (observed_at, percent of window used) for every
    observation whose limit parses and remaining is present — the
    over-time sparkline feed. Interpretation runs per observation (the
    server can change a group's limit between windows); observations
    that don't compute simply don't chart."""
    observations = (
        await db.execute(
            select(RateLimitObservation)
            .where(RateLimitObservation.group.is_not(None))
            .order_by(RateLimitObservation.observed_at, RateLimitObservation.id)
        )
    ).scalars().all()
    history: dict[str, list[tuple[datetime, float]]] = {}
    for obs in observations:
        parsed = parse_rate_limit(obs.rate_limit)
        if parsed is None or not parsed[0] or obs.rate_remaining is None:
            continue
        max_tokens = parsed[0]
        used = max(0, max_tokens - obs.rate_remaining)
        history.setdefault(obs.group, []).append(
            (obs.observed_at, round(100 * used / max_tokens, 1))
        )
    return history


async def error_limit_history(db: AsyncSession) -> list[tuple[datetime, float]]:
    """(observed_at, percent of the documented error budget used) for
    every observation of the legacy family — the budget meter's
    sparkline feed."""
    observations = (
        await db.execute(
            select(RateLimitObservation)
            .where(RateLimitObservation.error_limit_remain.is_not(None))
            .order_by(RateLimitObservation.observed_at, RateLimitObservation.id)
        )
    ).scalars().all()
    return [
        (
            obs.observed_at,
            round(
                100
                * max(0, ERROR_LIMIT_BUDGET - obs.error_limit_remain)
                / ERROR_LIMIT_BUDGET,
                1,
            ),
        )
        for obs in observations
    ]


async def sync_duration_history(
    db: AsyncSession,
    *,
    owner_type: str | None = None,
    kinds: Sequence[str] | None = None,
) -> dict[str, list[tuple[datetime, float]]]:
    """Per kind, (started_at, duration in seconds) across the retained
    run history — the durations chart's feed. Same filters as
    latest_sync_runs (the subset rule's kind list)."""
    query = select(SyncRun).where(SyncRun.duration_ms.is_not(None))
    if owner_type is not None:
        query = query.where(SyncRun.owner_type == owner_type)
    if kinds is not None:
        query = query.where(SyncRun.kind.in_(kinds))
    runs = (
        await db.execute(query.order_by(SyncRun.started_at, SyncRun.id))
    ).scalars().all()
    history: dict[str, list[tuple[datetime, float]]] = {}
    for run in runs:
        history.setdefault(run.kind, []).append(
            (run.started_at, run.duration_ms / 1000)
        )
    return history


# The legacy error budget's documented size: at most 100 non-2xx/3xx
# responses per minute (ESI Best Practices). The server states the
# remainder but never the maximum, so this is the query layer's one
# documented-constant derivation.
ERROR_LIMIT_BUDGET = 100


def error_limit_pct_used(observation: RateLimitObservation | None) -> float | None:
    """Percentage of the legacy error budget consumed (100 = breached,
    the 420 penalty). None without an observation of that family."""
    if observation is None or observation.error_limit_remain is None:
        return None
    consumed = max(0, ERROR_LIMIT_BUDGET - observation.error_limit_remain)
    return round(100 * consumed / ERROR_LIMIT_BUDGET, 1)
