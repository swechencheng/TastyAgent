"""Candidate generation: scan a watchlist into concrete CandidateTrades.

For each underlying we pull IV rank (prod metrics), the option chain + streamed
greeks/quotes (sandbox), pick the ~target-DTE expiration, choose short strikes near
the target delta, and assemble a short strangle. The pure builders are unit-tested;
the live scanner is a thin async wrapper around them.

Known approximations (sandbox limits, refine later):
- Buying-power reduction for undefined-risk strangles is *estimated*; the real figure
  comes from the dry-run preflight at placement time.
- Open interest / volume aren't reliably streamable in the sandbox, so liquidity uses
  the (real) bid/ask width plus placeholder OI/volume that pass the floor. The width
  check — the most important liquidity signal — is real.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from tastytrade.instruments import Option, OptionType as TTOptionType, get_option_chain

from ..config import StrategyParams
from ..models import Action, CandidateTrade, Leg, Liquidity, OptionType, Strategy
from ..tt.client import TastytradeClient
from ..tt.marketdata import (
    OptionSnapshot,
    get_underlying_price,
    select_by_delta,
    snapshot_options,
)
from ..tt.metrics import get_iv_metrics

# Sandbox-limitation placeholders (see module docstring).
_PLACEHOLDER_OI = 1000
_PLACEHOLDER_VOL = 500


def pick_expiration(expirations: list[date], params: StrategyParams, today: date) -> date | None:
    """Choose the listed expiration closest to target DTE within the [min,max] window."""
    target = today + timedelta(days=params.target_dte)
    valid = [d for d in expirations if params.min_dte <= (d - today).days <= params.max_dte]
    if not valid:
        return None
    return min(valid, key=lambda d: abs((d - target).days))


def estimate_undefined_bp(underlying_price: float) -> float:
    """Rough per-contract margin for an undefined-risk short option (~20% notional)."""
    return round(0.20 * underlying_price * 100, 2)


def _width_pct(snap: OptionSnapshot) -> float:
    if snap.bid is None or snap.ask is None or snap.mid in (None, 0):
        return 1.0  # treat unknown as illiquid
    return float((snap.ask - snap.bid) / snap.mid)


def build_strangle_candidate(
    symbol: str,
    underlying_price: float,
    iv_rank: float,
    dte: int,
    put: Option,
    call: Option,
    put_snap: OptionSnapshot,
    call_snap: OptionSnapshot,
    *,
    earnings_in_days: int | None = None,
) -> CandidateTrade | None:
    if put_snap.mid is None or call_snap.mid is None:
        return None
    credit = (float(put_snap.mid) + float(call_snap.mid)) * 100  # dollars per contract
    if credit <= 0:
        return None

    legs = (
        Leg(OptionType.PUT, float(put.strike_price), put.expiration_date,
            Action.SELL_TO_OPEN, delta=put_snap.delta or 0.0),
        Leg(OptionType.CALL, float(call.strike_price), call.expiration_date,
            Action.SELL_TO_OPEN, delta=call_snap.delta or 0.0),
    )
    liquidity = Liquidity(
        bid_ask_width_pct=max(_width_pct(put_snap), _width_pct(call_snap)),
        open_interest=_PLACEHOLDER_OI,
        daily_volume=_PLACEHOLDER_VOL,
    )
    return CandidateTrade(
        symbol=symbol,
        strategy=Strategy.SHORT_STRANGLE,
        legs=legs,
        dte=dte,
        net_credit=credit,
        max_profit=credit,
        max_loss=float("inf"),
        buying_power_reduction=estimate_undefined_bp(underlying_price),
        underlying_price=underlying_price,
        iv_rank=iv_rank,
        liquidity=liquidity,
        earnings_in_days=earnings_in_days,
    )


def build_naked_put_candidate(
    symbol, underlying_price, iv_rank, dte, put: Option, put_snap: OptionSnapshot,
    *, earnings_in_days: int | None = None,
) -> CandidateTrade | None:
    if put_snap.mid is None:
        return None
    credit = float(put_snap.mid) * 100
    if credit <= 0:
        return None
    strike = float(put.strike_price)
    legs = (
        Leg(OptionType.PUT, strike, put.expiration_date, Action.SELL_TO_OPEN, delta=put_snap.delta or 0.0),
    )
    return CandidateTrade(
        symbol=symbol, strategy=Strategy.NAKED_PUT, legs=legs, dte=dte,
        net_credit=credit, max_profit=credit, max_loss=strike * 100 - credit,
        buying_power_reduction=estimate_undefined_bp(underlying_price),
        underlying_price=underlying_price, iv_rank=iv_rank,
        liquidity=Liquidity(_width_pct(put_snap), _PLACEHOLDER_OI, _PLACEHOLDER_VOL),
        earnings_in_days=earnings_in_days,
    )


def build_credit_spread_candidate(
    symbol, underlying_price, iv_rank, dte, short_opt: Option, long_opt: Option,
    short_snap: OptionSnapshot, long_snap: OptionSnapshot,
    *, option_type: OptionType, strategy: Strategy, earnings_in_days: int | None = None,
) -> CandidateTrade | None:
    """Defined-risk vertical: short + protective long of the same type."""
    if short_snap.mid is None or long_snap.mid is None:
        return None
    net_ps = float(short_snap.mid) - float(long_snap.mid)
    width = abs(float(short_opt.strike_price) - float(long_opt.strike_price))
    if net_ps <= 0 or width <= 0:
        return None
    credit = net_ps * 100
    max_loss = (width - net_ps) * 100
    legs = (
        Leg(option_type, float(short_opt.strike_price), short_opt.expiration_date,
            Action.SELL_TO_OPEN, delta=short_snap.delta or 0.0),
        Leg(option_type, float(long_opt.strike_price), long_opt.expiration_date,
            Action.BUY_TO_OPEN, delta=long_snap.delta or 0.0),
    )
    return CandidateTrade(
        symbol=symbol, strategy=strategy, legs=legs, dte=dte,
        net_credit=credit, max_profit=credit, max_loss=max_loss,
        buying_power_reduction=max_loss,  # defined risk: BP == max loss
        underlying_price=underlying_price, iv_rank=iv_rank,
        liquidity=Liquidity(_width_pct(short_snap), _PLACEHOLDER_OI, _PLACEHOLDER_VOL),
        earnings_in_days=earnings_in_days,
    )


def build_iron_condor_candidate(
    symbol, underlying_price, iv_rank, dte,
    put_short: Option, put_long: Option, call_short: Option, call_long: Option,
    snaps: dict, *, earnings_in_days: int | None = None,
) -> CandidateTrade | None:
    ps, pl = snaps.get(put_short.streamer_symbol), snaps.get(put_long.streamer_symbol)
    cs, cl = snaps.get(call_short.streamer_symbol), snaps.get(call_long.streamer_symbol)
    if not all(s is not None and s.mid is not None for s in (ps, pl, cs, cl)):
        return None
    net_ps = (float(ps.mid) + float(cs.mid)) - (float(pl.mid) + float(cl.mid))
    if net_ps <= 0:
        return None
    put_width = abs(float(put_short.strike_price) - float(put_long.strike_price))
    call_width = abs(float(call_short.strike_price) - float(call_long.strike_price))
    width = max(put_width, call_width)
    credit = net_ps * 100
    max_loss = (width - net_ps) * 100
    legs = (
        Leg(OptionType.PUT, float(put_short.strike_price), put_short.expiration_date, Action.SELL_TO_OPEN, delta=ps.delta or 0.0),
        Leg(OptionType.PUT, float(put_long.strike_price), put_long.expiration_date, Action.BUY_TO_OPEN, delta=pl.delta or 0.0),
        Leg(OptionType.CALL, float(call_short.strike_price), call_short.expiration_date, Action.SELL_TO_OPEN, delta=cs.delta or 0.0),
        Leg(OptionType.CALL, float(call_long.strike_price), call_long.expiration_date, Action.BUY_TO_OPEN, delta=cl.delta or 0.0),
    )
    return CandidateTrade(
        symbol=symbol, strategy=Strategy.IRON_CONDOR, legs=legs, dte=dte,
        net_credit=credit, max_profit=credit, max_loss=max_loss,
        buying_power_reduction=max_loss, underlying_price=underlying_price, iv_rank=iv_rank,
        liquidity=Liquidity(max(_width_pct(ps), _width_pct(cs)), _PLACEHOLDER_OI, _PLACEHOLDER_VOL),
        earnings_in_days=earnings_in_days,
    )


async def _candidates_for_symbol(
    client: TastytradeClient, params: StrategyParams, today: date, symbol: str, m
) -> list[CandidateTrade]:
    """Build every feasible strategy for one underlying from a single snapshot."""
    chain = await get_option_chain(client.session, symbol)
    exp = pick_expiration(sorted(chain), params, today)
    if exp is None:
        return []

    underlying = float(await get_underlying_price(client.session, symbol))
    lo, hi = underlying * 0.5, underlying * 1.5  # wide enough for ~7Δ long wings
    opts = [o for o in chain[exp] if lo <= float(o.strike_price) <= hi]
    puts = [o for o in opts if o.option_type == TTOptionType.PUT]
    calls = [o for o in opts if o.option_type == TTOptionType.CALL]
    snaps = await snapshot_options(client.session, [o.streamer_symbol for o in opts], timeout=8.0)

    dte = (exp - today).days
    ivr = m.iv_rank
    earn = (m.next_earnings - today).days if m.next_earnings else None

    p_short = select_by_delta(puts, snaps, params.target_short_delta)
    c_short = select_by_delta(calls, snaps, params.target_short_delta)
    p_long = select_by_delta(puts, snaps, params.spread_long_delta)
    c_long = select_by_delta(calls, snaps, params.spread_long_delta)

    def sn(o):
        return snaps[o.streamer_symbol]

    out: list[CandidateTrade] = []

    if p_short and c_short:
        out.append(build_strangle_candidate(symbol, underlying, ivr, dte, p_short, c_short, sn(p_short), sn(c_short), earnings_in_days=earn))
    if p_short:
        out.append(build_naked_put_candidate(symbol, underlying, ivr, dte, p_short, sn(p_short), earnings_in_days=earn))
    if p_short and p_long and float(p_long.strike_price) < float(p_short.strike_price):
        out.append(build_credit_spread_candidate(symbol, underlying, ivr, dte, p_short, p_long, sn(p_short), sn(p_long), option_type=OptionType.PUT, strategy=Strategy.PUT_CREDIT_SPREAD, earnings_in_days=earn))
    if c_short and c_long and float(c_long.strike_price) > float(c_short.strike_price):
        out.append(build_credit_spread_candidate(symbol, underlying, ivr, dte, c_short, c_long, sn(c_short), sn(c_long), option_type=OptionType.CALL, strategy=Strategy.CALL_CREDIT_SPREAD, earnings_in_days=earn))
    if (
        p_short and c_short and p_long and c_long
        and float(p_long.strike_price) < float(p_short.strike_price)
        and float(c_long.strike_price) > float(c_short.strike_price)
    ):
        out.append(build_iron_condor_candidate(symbol, underlying, ivr, dte, p_short, p_long, c_short, c_long, snaps, earnings_in_days=earn))

    return [c for c in out if c is not None]


async def generate_candidates(
    client: TastytradeClient,
    metrics_session,
    params: StrategyParams,
    watchlist: list[str],
    *,
    concurrency: int = 6,
    metrics: dict | None = None,
) -> list[CandidateTrade]:
    """Live scan: build all feasible strategies per eligible underlying, concurrently.

    Each symbol yields a strangle, naked put, put/call credit spreads, and an iron
    condor (where strikes exist); guardrails + the LLM then choose among them. A bad
    symbol is skipped, never aborting the scan. ``metrics`` may be passed in to avoid
    re-fetching IV rank (the runner already fetched it for the whole universe).
    """
    today = date.today()
    if metrics is None:
        metrics = await get_iv_metrics(metrics_session, watchlist) if metrics_session else {}
    eligible = [s for s in watchlist if (m := metrics.get(s)) and m.iv_rank is not None]

    sem = asyncio.Semaphore(concurrency)

    async def guarded(symbol: str) -> list[CandidateTrade]:
        async with sem:
            try:
                return await _candidates_for_symbol(client, params, today, symbol, metrics[symbol])
            except Exception:  # noqa: BLE001 - skip a bad symbol, don't abort the scan
                return []

    results = await asyncio.gather(*(guarded(s) for s in eligible))
    return [c for lst in results for c in lst]
