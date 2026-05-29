"""In-memory runtime state for the API: mode, kill switch, starting capital, placer."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Awaitable, Callable

from ..config import RiskLimits, StrategyParams, TradingMode
from ..db.models import Trade

Placer = Callable[[Trade], Awaitable[str]]


@dataclass
class Runtime:
    mode: TradingMode = TradingMode.SANDBOX
    starting_capital: float = 1_000_000.0
    kill_switch: bool = False
    strategy: StrategyParams = field(default_factory=StrategyParams)
    placer: Placer | None = None  # set when a live/sandbox broker adapter is wired

    def risk_limits(self) -> RiskLimits:
        """Effective risk limits, reflecting the live kill-switch toggle."""
        return replace(RiskLimits(), kill_switch=self.kill_switch)
