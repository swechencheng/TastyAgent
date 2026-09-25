"""Order construction and margin preflight for IBKR combo/BAG orders.

Constructs multi-leg BAG contracts (Strangles, Iron Condors, Credit Spreads)
and maps credit/debit limit orders with walk-the-book and take-profit support.
"""

from __future__ import annotations

from decimal import Decimal
import logging
from typing import List, Optional, Tuple

from ib_async import ComboLeg, Contract, IB, LimitOrder, Option, Order

logger = logging.getLogger(__name__)


def build_combo_contract(
    symbol: str,
    legs: List[Tuple[Option, str]],  # (qualified Option contract, action: 'BUY' | 'SELL')
) -> Contract:
    """Build an IBKR BAG (combo) contract from qualified option legs."""
    combo_legs = [
        ComboLeg(
            conId=opt.conId,
            ratio=1,
            action=action.upper(),
            exchange="SMART",
        )
        for opt, action in legs
    ]
    return Contract(
        symbol=symbol,
        secType="BAG",
        exchange="SMART",
        currency="USD",
        comboLegs=combo_legs,
    )


def build_opening_credit_order(
    contracts: int,
    credit_per_share: float,
    account: str = "",
    order_ref: str = "",
    transmit: bool = True,
) -> LimitOrder:
    """Build an opening limit order for a net credit combo.

    In IBKR BAG combo pricing:
      Action 'BUY' with a negative limit price means receiving net credit (cash received).
    """
    credit = round(float(credit_per_share), 2)
    limit_price = -credit  # Negative price = net credit

    order = LimitOrder(
        action="BUY",
        totalQuantity=contracts,
        lmtPrice=limit_price,
        tif="DAY",
    )
    order.overridePercentageConstraints = True
    order.transmit = transmit
    if account:
        order.account = account
    if order_ref:
        order.orderRef = order_ref

    return order


def build_closing_tp_order(
    contracts: int,
    tp_debit_per_share: float,
    account: str = "",
    order_ref: str = "",
    parent_id: int = 0,
    transmit: bool = True,
) -> LimitOrder:
    """Build a Take-Profit limit order to close the credit combo at 50% max profit.

    To close a position opened via BUY at -credit, we SELL the BAG at -debit.
    Selling at -0.50 means paying 0.50 debit to close.
    """
    debit = round(float(tp_debit_per_share), 2)
    limit_price = -debit  # Sell at -debit closes the position for net payment

    order = LimitOrder(
        action="SELL",
        totalQuantity=contracts,
        lmtPrice=limit_price,
        tif="GTC",  # Good-til-Cancelled so the TP remains working on IBKR servers
    )
    order.overridePercentageConstraints = True
    order.transmit = transmit
    if parent_id > 0:
        order.parentId = parent_id
    if account:
        order.account = account
    if order_ref:
        order.orderRef = order_ref

    return order


def build_manual_close_order(
    contracts: int,
    debit_per_share: float,
    account: str = "",
    order_ref: str = "",
) -> LimitOrder:
    """Build a manual or defensive closing order (e.g. for rolls or stops)."""
    debit = round(float(debit_per_share), 2)
    limit_price = -debit

    order = LimitOrder(
        action="SELL",
        totalQuantity=contracts,
        lmtPrice=limit_price,
        tif="DAY",
    )
    order.overridePercentageConstraints = True
    order.transmit = True
    if account:
        order.account = account
    if order_ref:
        order.orderRef = order_ref

    return order


async def check_margin_preflight(
    ib: IB,
    contract: Contract,
    order: Order,
) -> dict[str, float]:
    """Execute whatIfOrderAsync to inspect IBKR margin impact before live placement."""
    try:
        order_state = await ib.whatIfOrderAsync(contract, order)
        init_margin = float(order_state.initMarginChange or 0.0)
        maint_margin = float(order_state.maintMarginChange or 0.0)
        commission = float(order_state.commission or 0.0)
        logger.info(
            "Preflight margin: InitChange=$%.2f, MaintChange=$%.2f, EstCommission=$%.2f",
            init_margin,
            maint_margin,
            commission,
        )
        return {
            "init_margin_change": init_margin,
            "maint_margin_change": maint_margin,
            "commission": commission,
        }
    except Exception as e:
        logger.warning("Margin preflight failed: %s", e)
        return {"init_margin_change": 0.0, "maint_margin_change": 0.0, "commission": 0.0}
