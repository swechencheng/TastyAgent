import pytest

from tastyagent.ibkr.ratelimit import AsyncTokenBucket


class FakeClock:
    """Deterministic clock; fake sleep advances virtual time instead of waiting."""

    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    async def sleep(self, seconds: float) -> None:
        self.t += seconds


async def test_initial_burst_consumes_without_waiting():
    clk = FakeClock()
    bucket = AsyncTokenBucket(rate=2.0, capacity=2.0, clock=clk.now, sleep=clk.sleep)
    await bucket.acquire()
    await bucket.acquire()
    assert clk.t == 0.0  # full bucket served the burst with no sleeping
    assert bucket.tokens < 1.0


async def test_blocks_and_advances_time_when_depleted():
    clk = FakeClock()
    bucket = AsyncTokenBucket(rate=2.0, capacity=2.0, clock=clk.now, sleep=clk.sleep)
    await bucket.acquire()
    await bucket.acquire()
    await bucket.acquire()  # must wait for 1 token at 2/sec -> 0.5s
    assert clk.t == pytest.approx(0.5)


async def test_refills_over_time():
    clk = FakeClock()
    bucket = AsyncTokenBucket(rate=2.0, capacity=2.0, clock=clk.now, sleep=clk.sleep)
    await bucket.acquire(2.0)  # drain
    clk.t += 1.0  # one second passes -> +2 tokens, capped at capacity
    assert bucket.tokens == pytest.approx(2.0)


async def test_amount_exceeding_capacity_raises():
    bucket = AsyncTokenBucket(rate=2.0, capacity=2.0)
    with pytest.raises(ValueError):
        await bucket.acquire(5.0)


def test_invalid_construction():
    with pytest.raises(ValueError):
        AsyncTokenBucket(rate=0, capacity=2.0)
