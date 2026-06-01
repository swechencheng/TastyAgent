"""Market metrics: IV rank / IV percentile / liquidity / earnings.

IMPORTANT: the cert (sandbox) environment does NOT serve this endpoint — it
returns 502. IV rank is a key entry guardrail input, so when paper-trading in
sandbox these metrics must be sourced from production market data (a separate
prod OAuth grant) or an external cache. ``get_iv_metrics`` surfaces the sandbox
gap as ``MarketMetricsUnavailable`` rather than silently passing bad data to the
guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from tastytrade import Session
from tastytrade.metrics import get_market_metrics


class MarketMetricsUnavailable(RuntimeError):
    """Raised when IV-rank metrics can't be fetched (e.g. sandbox 502)."""


@dataclass(frozen=True)
class IVMetrics:
    symbol: str
    iv_rank: float | None  # 0..1
    iv_percentile: float | None  # 0..1
    liquidity_rating: int | None
    next_earnings: date | None


def _to_rank(value: Decimal | None) -> float | None:
    """TastyTrade reports IV rank as a 0..1 fraction (e.g. 0.34 == 34%)."""
    return float(value) if value is not None else None


async def get_iv_metrics(session: Session, symbols: list[str]) -> dict[str, IVMetrics]:
    """Batched IV metrics for a (possibly large) universe.

    Chunks the request so big watchlists work. Raises MarketMetricsUnavailable only
    if *every* chunk fails (the sandbox-502 case); a single bad chunk is skipped so
    one typo'd symbol can't blank the whole universe.
    """
    out: dict[str, IVMetrics] = {}
    errored = any_ok = False

    for i in range(0, len(symbols), 90):
        chunk = symbols[i : i + 90]
        try:
            raw = await get_market_metrics(session, chunk)
            any_ok = True
        except Exception:  # noqa: BLE001 - tolerate a bad chunk; detect all-fail below
            errored = True
            continue
        for m in raw:
            # Prefer the tastyworks IV rank, fall back to the generic index rank.
            rank = m.tw_implied_volatility_index_rank or m.implied_volatility_index_rank
            earnings_date = None
            if m.earnings is not None:
                earnings_date = getattr(m.earnings, "expected_report_date", None)
            out[m.symbol] = IVMetrics(
                symbol=m.symbol,
                iv_rank=_to_rank(rank),
                iv_percentile=_to_rank(m.implied_volatility_percentile),
                liquidity_rating=m.liquidity_rating,
                next_earnings=earnings_date,
            )

    if errored and not any_ok:
        raise MarketMetricsUnavailable(f"market metrics unavailable for {symbols[:5]}…")
    return out
