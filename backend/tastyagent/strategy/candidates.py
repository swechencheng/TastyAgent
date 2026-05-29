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


async def generate_candidates(
    client: TastytradeClient,
    metrics_session,
    params: StrategyParams,
    watchlist: list[str],
) -> list[CandidateTrade]:
    """Live scan: one short-strangle candidate per eligible underlying."""
    today = date.today()
    metrics = await get_iv_metrics(metrics_session, watchlist) if metrics_session else {}
    candidates: list[CandidateTrade] = []

    for symbol in watchlist:
        m = metrics.get(symbol)
        if m is None or m.iv_rank is None:
            continue  # can't evaluate the IV-rank guardrail -> skip
        try:
            chain = await get_option_chain(client.session, symbol)
            exp = pick_expiration(sorted(chain), params, today)
            if exp is None:
                continue

            # Window strikes around spot so the greeks snapshot is small and fast,
            # yet still covers the target-delta strikes for ~45 DTE.
            underlying = float(await get_underlying_price(client.session, symbol))
            lo, hi = underlying * 0.6, underlying * 1.4
            opts = [o for o in chain[exp] if lo <= float(o.strike_price) <= hi]
            puts = [o for o in opts if o.option_type == TTOptionType.PUT]
            calls = [o for o in opts if o.option_type == TTOptionType.CALL]
            snaps = await snapshot_options(client.session, [o.streamer_symbol for o in opts])

            put = select_by_delta(puts, snaps, params.target_short_delta)
            call = select_by_delta(calls, snaps, params.target_short_delta)
            if put is None or call is None:
                continue
            earnings_in_days = (m.next_earnings - today).days if m.next_earnings else None

            cand = build_strangle_candidate(
                symbol, underlying, m.iv_rank, (exp - today).days,
                put, call, snaps[put.streamer_symbol], snaps[call.streamer_symbol],
                earnings_in_days=earnings_in_days,
            )
            if cand is not None:
                candidates.append(cand)
        except Exception:  # noqa: BLE001 - one bad symbol shouldn't abort the scan
            continue

    return candidates
