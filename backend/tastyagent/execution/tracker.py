"""Fill tracking and exit application — reconcile our ledger with broker state.

Kept broker-agnostic: callers pass plain dicts (order-id -> status, trade-id -> mark)
gathered from the broker, so this is deterministic and unit-testable. The exit
decisions themselves come from ``strategy/exits.py``; this module just applies them
to the ledger.
"""

from __future__ import annotations

from ..db.models import TradeStatus
from ..portfolio.ledger import Ledger

# Broker order states we treat as filled vs dead.
FILLED = {"Filled", "filled"}
DEAD = {
    "Cancelled",
    "Canceled",
    "Rejected",
    "Expired",
    "Removed",
    "rejected",
    "expired",
}


def reconcile_fills(ledger: Ledger, order_status: dict[str, str]) -> None:
    """Flip WORKING trades to OPEN (filled) or CANCELED (dead) per broker status."""
    for trade in ledger.open_trades():
        if trade.status is not TradeStatus.WORKING or not trade.broker_order_id:
            continue
        status = order_status.get(trade.broker_order_id)
        if status in FILLED:
            ledger.mark_open(trade)
        elif status in DEAD:
            ledger.cancel_trade(trade, reason=f"broker: {status}")


def apply_marks(ledger: Ledger, marks: dict[int, float]) -> None:
    """Update the current cost-to-close (mark) for open trades by trade id."""
    for trade in ledger.open_trades():
        if trade.id in marks:
            ledger.update_mark(trade, marks[trade.id])
