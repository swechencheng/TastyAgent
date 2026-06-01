"""Core domain models shared across the strategy, risk, and execution layers.

Stdlib-only so the safety-critical core stays dependency-free and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


def probability_of_profit(short_deltas: list[float]) -> float:
    """Model-free PoP estimate from short-leg deltas.

    Delta approximates an option's probability of finishing in-the-money, so the
    probability that all short legs expire OTM (the trade is profitable) is
    ~ 1 - sum(|short deltas|). This is the heuristic behind "16-delta strangle ≈
    ~68% PoP". It ignores the small breakeven cushion from the credit, so it's a
    slightly conservative estimate. Clamped to [0, 1].
    """
    pop = 1.0 - sum(abs(d) for d in short_deltas)
    return max(0.0, min(1.0, pop))


class Strategy(str, Enum):
    SHORT_STRANGLE = "short_strangle"
    NAKED_PUT = "naked_put"
    NAKED_CALL = "naked_call"
    SHORT_STRADDLE = "short_straddle"
    IRON_CONDOR = "iron_condor"
    PUT_CREDIT_SPREAD = "put_credit_spread"
    CALL_CREDIT_SPREAD = "call_credit_spread"

    @property
    def is_defined_risk(self) -> bool:
        return self in (
            Strategy.IRON_CONDOR,
            Strategy.PUT_CREDIT_SPREAD,
            Strategy.CALL_CREDIT_SPREAD,
        )


class OptionType(str, Enum):
    PUT = "put"
    CALL = "call"


class Action(str, Enum):
    SELL_TO_OPEN = "sell_to_open"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_CLOSE = "sell_to_close"
    BUY_TO_CLOSE = "buy_to_close"


@dataclass(frozen=True)
class Leg:
    """One option leg of a candidate or open trade."""

    option_type: OptionType
    strike: float
    expiration: date
    action: Action
    quantity: int = 1
    delta: float = 0.0  # signed greek delta of the leg as quoted

    @property
    def is_short(self) -> bool:
        return self.action in (Action.SELL_TO_OPEN, Action.SELL_TO_CLOSE)


@dataclass(frozen=True)
class Liquidity:
    bid_ask_width_pct: float  # (ask - bid) / mid
    open_interest: int
    daily_volume: int


@dataclass(frozen=True)
class CandidateTrade:
    """A proposed opening trade, before guardrail/risk validation."""

    symbol: str
    strategy: Strategy
    legs: tuple[Leg, ...]
    dte: int
    net_credit: float  # credit received to open (per contract, dollars)
    max_profit: float  # dollars per position
    max_loss: float  # dollars per position; float('inf') for undefined risk
    buying_power_reduction: float  # dollars of BP per position
    underlying_price: float
    iv_rank: float  # 0..1
    liquidity: Liquidity
    earnings_in_days: int | None = None  # None == no earnings scheduled in window

    @property
    def max_short_leg_delta(self) -> float:
        shorts = [abs(leg.delta) for leg in self.legs if leg.is_short]
        return max(shorts) if shorts else 0.0

    @property
    def probability_of_profit(self) -> float:
        return probability_of_profit([leg.delta for leg in self.legs if leg.is_short])


@dataclass(frozen=True)
class OpenPosition:
    """An open trade we are managing."""

    symbol: str
    strategy: Strategy
    legs: tuple[Leg, ...]
    entry_date: date
    entry_credit: float  # credit received at open (per position, dollars)
    current_cost_to_close: float  # debit to close now (per position, dollars)
    buying_power_reduction: float
    dte_remaining: int
    as_of: date
    current_max_short_delta: float | None = None  # live |delta| of the most-tested short leg

    @property
    def days_held(self) -> int:
        return max((self.as_of - self.entry_date).days, 0)

    @property
    def profit_pct(self) -> float:
        """Fraction of max profit captured. Positive=winning, negative=losing.

        For a credit position max profit == entry credit; current profit is
        the entry credit minus what it costs to close now.
        """
        if self.entry_credit <= 0:
            return 0.0
        return (self.entry_credit - self.current_cost_to_close) / self.entry_credit
