"""Exit management: backstops plus the ahead-of-pace profit schedule.

Decision order (first match wins):
  1. 21-DTE backstop  -> manage / roll / close (gamma & assignment risk rises)
  2. Stop loss        -> close (loss reached N x credit)
  3. 50% max profit   -> close (standard winner management)
  4. Ahead-of-pace    -> close earlier at a lower milestone hit ahead of schedule
  5. otherwise        -> hold
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..config import StrategyParams
from ..models import OpenPosition
from .profit_schedule import ahead_of_pace_milestone


class ExitAction(str, Enum):
    HOLD = "hold"
    CLOSE = "close"
    MANAGE_DTE = "manage_dte"  # close or roll near expiration


@dataclass(frozen=True)
class ExitDecision:
    action: ExitAction
    reason: str

    @property
    def should_exit(self) -> bool:
        return self.action is not ExitAction.HOLD


def evaluate_exit(position: OpenPosition, params: StrategyParams) -> ExitDecision:
    profit_pct = position.profit_pct
    days_held = position.days_held

    # 1. 21-DTE backstop — never hold past this.
    if position.dte_remaining <= params.manage_dte:
        return ExitDecision(
            ExitAction.MANAGE_DTE,
            f"{position.dte_remaining} DTE <= {params.manage_dte}: manage/roll",
        )

    # 2. Stop loss — loss reached N x the credit received.
    if profit_pct <= -params.stop_loss_multiple:
        return ExitDecision(
            ExitAction.CLOSE,
            f"loss {profit_pct:.0%} of credit <= -{params.stop_loss_multiple:.0f}x stop",
        )

    # 3. Standard 50%-of-max-profit winner management.
    if profit_pct >= params.take_profit_pct:
        return ExitDecision(
            ExitAction.CLOSE,
            f"profit {profit_pct:.0%} >= {params.take_profit_pct:.0%} max-profit target",
        )

    # 4. Ahead-of-pace: lock in a lower milestone reached faster than average.
    milestone = ahead_of_pace_milestone(position.strategy, profit_pct, days_held)
    if milestone is not None:
        return ExitDecision(
            ExitAction.CLOSE,
            f"profit {profit_pct:.0%} hit {milestone:.0%} milestone by day "
            f"{days_held} (ahead of pace)",
        )

    return ExitDecision(ExitAction.HOLD, "no exit trigger")
