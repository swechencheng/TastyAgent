"""Async token-bucket rate limiter.

Used to throttle requests to broker gateways and avoid pacing violations.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import time


class AsyncTokenBucket:
    def __init__(
        self,
        rate: float = 2.0,  # tokens added per second
        capacity: float = 2.0,  # max burst
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], "asyncio.Future"] | None = None,
    ) -> None:
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be positive")
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._clock = clock
        self._sleep = sleep or asyncio.sleep
        self._updated = clock()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._updated = now

    @property
    def tokens(self) -> float:
        self._refill()
        return self._tokens

    async def acquire(self, amount: float = 1.0) -> None:
        """Block until ``amount`` tokens are available, then consume them."""
        if amount > self._capacity:
            raise ValueError("amount exceeds bucket capacity")
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= amount:
                    self._tokens -= amount
                    return
                deficit = amount - self._tokens
                await self._sleep(deficit / self._rate)
