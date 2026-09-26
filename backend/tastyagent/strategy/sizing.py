"""Position sizing: buying-power based, respecting per-trade and portfolio caps."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..config import RiskLimits
from ..models import CandidateTrade


@dataclass(frozen=True)
class SizingResult:
    contracts: int  # 0 means the trade cannot be placed within limits
    bp_used: float  # dollars of buying power the sized trade consumes
    reason: str


def size_trade(
    candidate: CandidateTrade,
    net_liq: float,
    current_bp_used: float,
    limits: RiskLimits,
) -> SizingResult:
    """Determine how many contracts to trade within BP caps.

    - per-trade BP must not exceed ``max_trade_bp_pct`` of net liquidation value
    - aggregate BP (existing + new) must not exceed ``max_total_bp_pct``
    """
    per_contract_bp = candidate.buying_power_reduction
    if per_contract_bp <= 0 or net_liq <= 0:
        return SizingResult(0, 0.0, "invalid BP or net liq")

    per_trade_budget = limits.max_trade_bp_pct * net_liq
    total_budget_remaining = limits.max_total_bp_pct * net_liq - current_bp_used
    budget = min(per_trade_budget, total_budget_remaining)

    if budget < per_contract_bp:
        return SizingResult(
            0,
            0.0,
            f"need ${per_contract_bp:,.0f}/contract but only ${budget:,.0f} available",
        )

    contracts = int(math.floor(budget / per_contract_bp))
    bp_used = contracts * per_contract_bp
    return SizingResult(
        contracts, bp_used, f"{contracts} contract(s), ${bp_used:,.0f} BP"
    )
