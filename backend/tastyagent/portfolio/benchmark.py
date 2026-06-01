"""S&P-500 benchmark comparison.

The dashboard shows the agent's equity curve vs. "what if I'd put the same starting
capital in the S&P 500." The comparison math is pure and testable; the actual price
fetch is pluggable (lazy yfinance import) so tests don't hit the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class BenchmarkComparison:
    strategy_return_pct: float
    sp500_return_pct: float
    # Equity curve rebased so both start at the same starting capital.
    strategy_curve: list[tuple[date, float]]
    sp500_curve: list[tuple[date, float]]

    @property
    def outperformance_pct(self) -> float:
        return self.strategy_return_pct - self.sp500_return_pct


def _return_pct(first: float, last: float) -> float:
    if first == 0:
        return 0.0
    return (last - first) / first


def compare(
    equity_curve: list[tuple[date, float]],
    sp500_closes: list[tuple[date, float]],
) -> BenchmarkComparison:
    """Compare an equity curve to the S&P, rebasing the S&P to the same start capital.

    Both inputs are ascending (date, value). The S&P series is scaled so its first
    point equals the strategy's starting net liq, giving an apples-to-apples curve.
    """
    if not equity_curve or not sp500_closes:
        return BenchmarkComparison(0.0, 0.0, list(equity_curve), [])

    start_capital = equity_curve[0][1]
    strat_return = _return_pct(start_capital, equity_curve[-1][1])

    sp_first = sp500_closes[0][1]
    sp_return = _return_pct(sp_first, sp500_closes[-1][1])
    scale = (start_capital / sp_first) if sp_first else 0.0
    sp_curve = [(d, close * scale) for d, close in sp500_closes]

    return BenchmarkComparison(
        strategy_return_pct=strat_return,
        sp500_return_pct=sp_return,
        strategy_curve=list(equity_curve),
        sp500_curve=sp_curve,
    )


_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/SPY"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 tastyagent/0.1"


def _yahoo_chart(params: dict) -> list[tuple[date, float]]:
    """Daily SPY closes from Yahoo's keyless chart API. SPY proxies the S&P 500."""
    import httpx  # noqa: PLC0415

    resp = httpx.get(_YAHOO_URL, params=params, headers={"User-Agent": _UA}, timeout=20.0)
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    out: list[tuple[date, float]] = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        out.append((datetime.utcfromtimestamp(ts).date(), float(close)))
    return out


def fetch_sp500_closes(start: date, end: date) -> list[tuple[date, float]]:
    """Daily SPY closes between two dates. Best-effort: [] on any error."""
    try:
        p1 = int(datetime(start.year, start.month, start.day).timestamp())
        p2 = int(datetime(end.year, end.month, end.day).timestamp())
        return _yahoo_chart({"period1": p1, "period2": p2, "interval": "1d"})
    except Exception:  # noqa: BLE001 - benchmark data is best-effort
        return []


def latest_sp500_close() -> float | None:
    """Most recent SPY close (by range, so it's robust to the system clock). None if down."""
    try:
        data = _yahoo_chart({"range": "5d", "interval": "1d"})
        return data[-1][1] if data else None
    except Exception:  # noqa: BLE001
        return None
