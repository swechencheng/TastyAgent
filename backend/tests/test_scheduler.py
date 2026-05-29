import asyncio
from datetime import datetime, timedelta

from tastyagent.scheduler import ET, is_market_open, run_loop


def test_midday_weekday_open_matches_rule():
    dt = datetime(2026, 6, 1, 12, 0, tzinfo=ET)
    # At noon the time window is satisfied, so openness == is-a-weekday.
    assert is_market_open(dt) == (dt.weekday() < 5)


def test_after_hours_closed():
    assert not is_market_open(datetime(2026, 6, 1, 17, 30, tzinfo=ET))


def test_weekend_closed():
    d = datetime(2026, 6, 1, 12, 0, tzinfo=ET)
    while d.weekday() != 5:  # advance to a Saturday
        d += timedelta(days=1)
    assert not is_market_open(d)


async def test_run_loop_ticks_then_stops():
    stop = asyncio.Event()
    calls = []

    async def tick():
        calls.append(1)
        if len(calls) >= 2:
            stop.set()

    await run_loop(tick, interval_seconds=0.01, market_hours_only=False, stop=stop)
    assert len(calls) >= 2


async def test_run_loop_survives_tick_errors():
    stop = asyncio.Event()
    calls = []

    async def tick():
        calls.append(1)
        if len(calls) >= 2:
            stop.set()
        raise RuntimeError("boom")

    await run_loop(tick, interval_seconds=0.01, market_hours_only=False, stop=stop)
    assert len(calls) >= 2  # a failing tick didn't kill the loop
