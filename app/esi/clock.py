"""Injectable clock so time-dependent code (limiter pauses, retry backoff)
can be tested without real sleeps."""

import asyncio
from datetime import datetime
from typing import Protocol

from ..db import utc_now


class Clock(Protocol):
    def now(self) -> datetime: ...

    async def sleep(self, seconds: float) -> None: ...


class RealClock:
    def now(self) -> datetime:
        return utc_now()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
