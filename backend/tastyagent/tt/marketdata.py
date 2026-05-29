"""Market data via DXLink: underlying quotes, option quotes + greeks, and
delta-based strike selection.

Sandbox note: quotes are 15-minute delayed but the stream works; greeks flow
normally. Market-metrics (IV rank) are NOT served in the cert environment
(see ``metrics.py``).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal

from tastytrade import DXLinkStreamer, Session
from tastytrade.dxfeed import Greeks, Quote
from tastytrade.instruments import Option


@dataclass
class OptionSnapshot:
    streamer_symbol: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    delta: float | None = None

    @property
    def complete(self) -> bool:
        return self.bid is not None and self.ask is not None and self.delta is not None

    @property
    def mid(self) -> Decimal | None:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2


async def get_underlying_price(session: Session, symbol: str, timeout: float = 8.0) -> Decimal:
    """Return the mid price of the underlying from a single streamed quote."""
    async with DXLinkStreamer(session) as streamer:
        await streamer.subscribe(Quote, [symbol])
        quote = await asyncio.wait_for(streamer.get_event(Quote), timeout)
    return (quote.bid_price + quote.ask_price) / 2


async def snapshot_options(
    session: Session,
    streamer_symbols: list[str],
    timeout: float = 12.0,
) -> dict[str, OptionSnapshot]:
    """Collect the latest Quote + Greeks for each option symbol.

    Returns as soon as every symbol has both a quote and greeks, or when the
    timeout elapses (whatever we have so far).
    """
    snaps: dict[str, OptionSnapshot] = {
        s: OptionSnapshot(streamer_symbol=s) for s in streamer_symbols
    }

    async with DXLinkStreamer(session) as streamer:
        await streamer.subscribe(Quote, streamer_symbols)
        await streamer.subscribe(Greeks, streamer_symbols)

        async def pump() -> None:
            async def quotes() -> None:
                async for q in streamer.listen(Quote):
                    snap = snaps.get(q.event_symbol)
                    if snap:
                        snap.bid, snap.ask = q.bid_price, q.ask_price
                    if all(s.complete for s in snaps.values()):
                        return

            async def greeks() -> None:
                async for g in streamer.listen(Greeks):
                    snap = snaps.get(g.event_symbol)
                    if snap:
                        snap.delta = float(g.delta)
                    if all(s.complete for s in snaps.values()):
                        return

            await asyncio.gather(quotes(), greeks())

        try:
            await asyncio.wait_for(pump(), timeout)
        except asyncio.TimeoutError:
            pass

    return snaps


def select_by_delta(
    options: list[Option],
    snapshots: dict[str, OptionSnapshot],
    target_delta: float,
) -> Option | None:
    """Pick the option whose |delta| is closest to ``target_delta``.

    Only considers options for which we have a streamed delta.
    """
    best: tuple[float, Option] | None = None
    for opt in options:
        snap = snapshots.get(opt.streamer_symbol)
        if snap is None or snap.delta is None:
            continue
        diff = abs(abs(snap.delta) - target_delta)
        if best is None or diff < best[0]:
            best = (diff, opt)
    return best[1] if best else None
