"""Market-hours decision loop.

A lightweight async loop that invokes an async ``tick`` callable on an interval,
optionally gated to regular US equity market hours. The tick (wired in the app
layer) runs one full cycle: gather state -> orchestrate -> execute -> reconcile.

Holiday awareness is intentionally omitted here; TastyTrade's market-sessions
endpoint can refine ``is_market_open`` later. Kept free of broker/LLM imports so
the gating logic stays simple and the loop is easy to drive from the API or a CLI.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, time
from typing import Awaitable, Callable
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


def is_market_open(now: datetime | None = None) -> bool:
    """True during regular US equity hours (weekday 9:30-16:00 ET). No holidays."""
    now = (now or datetime.now(ET)).astimezone(ET)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


async def run_loop(
    tick: Callable[[], Awaitable[None]],
    *,
    interval_seconds: float = 300.0,
    market_hours_only: bool = True,
    stop: asyncio.Event | None = None,
) -> None:
    """Run ``tick`` every ``interval_seconds`` until ``stop`` is set.

    When ``market_hours_only`` is True, ticks outside market hours are skipped
    (the loop keeps sleeping). Exceptions in a tick are swallowed and logged so a
    single bad cycle never kills the loop.
    """
    stop = stop or asyncio.Event()
    while not stop.is_set():
        if not market_hours_only or is_market_open():
            try:
                await tick()
            except Exception as e:  # noqa: BLE001 - never let one cycle kill the loop
                import logging

                logging.getLogger("tastyagent.scheduler").exception("cycle failed: %s", e)
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass
