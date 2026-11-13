"""ESI rate-control awareness.

Two coexisting systems, with mutually exclusive header families per response:

- Legacy error limiter: X-Esi-Error-Limit-Remain/-Reset. Only 4xx/5xx
  decrement (304s are free). Breaching it 420s the client across ALL
  endpoints for the rest of the window — so this pause is GLOBAL.
- Floating-window rate limiter (rolled out late 2025): X-Ratelimit-Group/
  -Limit/-Remaining/-Used per route group; on limit, 429 + Retry-After.
  Buckets are per group+app+character — so this throttle is PER GROUP.

Both mechanisms are heuristics layered on server-provided truth: preempt
with floors, react to 420/429 with the server's own numbers, and cap every
pause so a hostile or buggy header can never wedge the app.
"""

from datetime import datetime, timedelta

import httpx

from .clock import Clock

# Pause when the error-limit remainder is at or below this (~100 per window).
ERROR_LIMIT_FLOOR = 20
# Pad the server's reset countdown slightly so we wake just after the roll.
RESET_SKEW_SECONDS = 1.0
# Never trust a header enough to pause longer than this.
PAUSE_CAP_SECONDS = 120.0
# Per-group throttle when X-Ratelimit-Remaining is at or below this.
RATE_GROUP_FLOOR = 6
# Heuristic cooldown for a group near its floor; the floating window is not
# fully modelable from the headers alone.
RATE_GROUP_COOLDOWN_SECONDS = 60.0
# Fallback for a header-less 429 ("deep EVE Server code" can emit these).
DEFAULT_RETRY_AFTER_SECONDS = 5.0


class ESILimiter:
    """Tracks ESI rate-control headers and pauses requests accordingly.

    Single-process by design (module-level default below), mirroring the
    refresh-lock precedent in client.py; a multi-worker deployment would
    need shared state.
    """

    def __init__(self, clock: Clock):
        self._clock = clock
        self._error_paused_until: datetime = clock.now()
        self._group_paused_until: dict[str, datetime] = {}

    def observe(self, response: httpx.Response) -> None:
        """Record rate-control state from any ESI response.

        Tolerates either header family, neither, or (defensively) both;
        missing or unparseable values are ignored.
        """
        now = self._clock.now()
        remain = header_int(response, "X-Esi-Error-Limit-Remain")
        reset = header_float(response, "X-Esi-Error-Limit-Reset")
        if (remain is not None and remain <= ERROR_LIMIT_FLOOR) or (
            response.status_code == 420 and reset is not None
        ):
            self._pause_global(now, reset)

        group = response.headers.get("X-Ratelimit-Group")
        if group is not None:
            remaining = header_int(response, "X-Ratelimit-Remaining")
            if remaining is not None and remaining <= RATE_GROUP_FLOOR:
                until = now + timedelta(seconds=RATE_GROUP_COOLDOWN_SECONDS)
                current = self._group_paused_until.get(group)
                if current is None or until > current:
                    self._group_paused_until[group] = until

    async def wait_if_paused(self, group: str | None = None) -> None:
        """Sleep (via the injectable clock) until the relevant pause lifts."""
        now = self._clock.now()
        till = self._error_paused_until
        if group is not None:
            group_till = self._group_paused_until.get(group)
            if group_till is not None and group_till > till:
                till = group_till
        if till > now:
            await self._clock.sleep((till - now).total_seconds())

    def pause_for_retry_after(self, seconds: float | None) -> None:
        """Global pause from a 429's Retry-After, clamped to the cap."""
        wait = DEFAULT_RETRY_AFTER_SECONDS if seconds is None else max(seconds, 0.0)
        self._pause_global(self._clock.now(), min(wait, PAUSE_CAP_SECONDS))

    def _pause_global(self, now, reset_seconds: float | None) -> None:
        wait = (
            min(reset_seconds + RESET_SKEW_SECONDS, PAUSE_CAP_SECONDS)
            if reset_seconds is not None
            else DEFAULT_RETRY_AFTER_SECONDS
        )
        until = now + timedelta(seconds=wait)
        if until > self._error_paused_until:
            self._error_paused_until = until


def header_int(response: httpx.Response, name: str) -> int | None:
    try:
        value = response.headers.get(name)
        return None if value is None else int(value)
    except ValueError:
        return None


def header_float(response: httpx.Response, name: str) -> float | None:
    try:
        value = response.headers.get(name)
        return None if value is None else float(value)
    except ValueError:
        return None
