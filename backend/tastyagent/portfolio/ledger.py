"""The trade ledger: record decisions/trades and drive their status transitions.

This is the agent's own source of truth (the sandbox wipes state every 24h).

Money convention: a premium-selling trade's ``max_profit`` is the credit received
per contract (dollars), so the total entry credit = ``max_profit * contracts`` and
``buying_power = buying_power_reduction * contracts``. Realized P/L on close =
entry credit kept minus the debit paid to close.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import TradingMode
from ..db.models import Decision, Trade, TradeLeg, TradeStatus, utcnow
from ..models import CandidateTrade


class Ledger:
    def __init__(self, session: Session) -> None:
        self.s = session

    # --- decisions ---
    def record_decision(self, mode: TradingMode, commentary: str, considered: int) -> Decision:
        d = Decision(mode=mode.value, commentary=commentary, considered=considered)
        self.s.add(d)
        self.s.commit()
        return d

    # --- trade creation ---
    def _new_trade(
        self,
        candidate: CandidateTrade,
        contracts: int,
        rationale: str,
        mode: TradingMode,
        status: TradeStatus,
        decision: Decision | None,
    ) -> Trade:
        trade = Trade(
            decision_id=decision.id if decision else None,
            symbol=candidate.symbol,
            strategy=candidate.strategy.value,
            contracts=contracts,
            status=status,
            mode=mode.value,
            rationale=rationale,
            entry_credit=candidate.max_profit * contracts,
            buying_power=candidate.buying_power_reduction * contracts,
            dte_at_entry=candidate.dte,
            current_cost_to_close=candidate.max_profit * contracts,  # 0% profit at entry
        )
        trade.legs = [
            TradeLeg(
                option_type=leg.option_type.value,
                strike=leg.strike,
                expiration=leg.expiration,
                action=leg.action.value,
                quantity=leg.quantity * contracts,
                delta=leg.delta,
            )
            for leg in candidate.legs
        ]
        self.s.add(trade)
        self.s.commit()
        return trade

    def record_planned(self, candidate, contracts, rationale, mode, decision=None) -> Trade:
        """Record a trade awaiting action. Initial status depends on the mode."""
        status = {
            TradingMode.LIVE_APPROVAL: TradeStatus.PENDING_APPROVAL,
            TradingMode.BACKTEST: TradeStatus.PLANNED,
        }.get(mode, TradeStatus.WORKING)
        return self._new_trade(candidate, contracts, rationale, mode, status, decision)

    def record_rejected(self, candidate, reason, mode, decision=None) -> Trade:
        t = self._new_trade(candidate, 0, reason, mode, TradeStatus.REJECTED, decision)
        return t

    # --- status transitions ---
    def mark_working(self, trade: Trade, broker_order_id: str) -> None:
        trade.status = TradeStatus.WORKING
        trade.broker_order_id = broker_order_id
        self.s.commit()

    def mark_open(self, trade: Trade, opened_at: datetime | None = None) -> None:
        trade.status = TradeStatus.OPEN
        trade.opened_at = opened_at or utcnow()
        if trade.entry_date is None and trade.opened_at is not None:
            trade.entry_date = trade.opened_at.date()
        self.s.commit()

    def update_mark(self, trade: Trade, current_cost_to_close: float) -> None:
        trade.current_cost_to_close = current_cost_to_close
        self.s.commit()

    def close_trade(
        self, trade: Trade, exit_debit: float, exit_reason: str, closed_at: datetime | None = None
    ) -> None:
        trade.exit_debit = exit_debit
        trade.exit_reason = exit_reason
        trade.realized_pnl = trade.entry_credit - exit_debit
        trade.status = TradeStatus.CLOSED
        trade.closed_at = closed_at or utcnow()
        self.s.commit()

    def cancel_trade(self, trade: Trade, reason: str = "canceled") -> None:
        trade.status = TradeStatus.CANCELED
        trade.exit_reason = reason
        self.s.commit()

    # --- queries ---
    def get(self, trade_id: int) -> Trade | None:
        return self.s.get(Trade, trade_id)

    def _by_status(self, *statuses: TradeStatus) -> list[Trade]:
        stmt = select(Trade).where(Trade.status.in_(statuses)).order_by(Trade.created_at)
        return list(self.s.scalars(stmt))

    def open_trades(self) -> list[Trade]:
        return self._by_status(TradeStatus.OPEN, TradeStatus.WORKING)

    def closed_trades(self) -> list[Trade]:
        return self._by_status(TradeStatus.CLOSED)

    def pending_approval(self) -> list[Trade]:
        return self._by_status(TradeStatus.PENDING_APPROVAL)

    def all_trades(self) -> list[Trade]:
        return list(self.s.scalars(select(Trade).order_by(Trade.created_at)))

    def positions_by_symbol(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for t in self.open_trades():
            counts[t.symbol] = counts.get(t.symbol, 0) + 1
        return counts
