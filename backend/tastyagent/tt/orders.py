"""Order construction and placement.

Multi-leg credit orders (strangles, credit spreads) plus placement with a
dry-run preflight. The tastyware SDK encodes credit/debit via the SIGN of
``price``: a credit you receive is a NEGATIVE price. ``place`` defaults to a
dry run so callers can validate buying-power effect and fees before committing.
"""

from __future__ import annotations

from decimal import Decimal

from tastytrade import Account, Session
from tastytrade.instruments import Option
from tastytrade.order import (
    NewOrder,
    OrderAction,
    OrderTimeInForce,
    OrderType,
    PlacedOrderResponse,
)

# Credit is received -> negative price in the SDK's sign convention.
CREDIT_SIGN = Decimal(-1)


def build_short_strangle(
    put: Option,
    call: Option,
    quantity: int,
    credit: Decimal,
    *,
    tif: OrderTimeInForce = OrderTimeInForce.DAY,
) -> NewOrder:
    """Sell-to-open a put and a call for a net ``credit`` (positive dollars)."""
    legs = [
        put.build_leg(quantity, OrderAction.SELL_TO_OPEN),
        call.build_leg(quantity, OrderAction.SELL_TO_OPEN),
    ]
    return NewOrder(
        time_in_force=tif,
        order_type=OrderType.LIMIT,
        legs=legs,
        price=CREDIT_SIGN * abs(credit),
    )


def build_naked_short(
    option: Option,
    quantity: int,
    credit: Decimal,
    *,
    tif: OrderTimeInForce = OrderTimeInForce.DAY,
) -> NewOrder:
    """Sell-to-open a single option (naked put/call) for a ``credit``."""
    return NewOrder(
        time_in_force=tif,
        order_type=OrderType.LIMIT,
        legs=[option.build_leg(quantity, OrderAction.SELL_TO_OPEN)],
        price=CREDIT_SIGN * abs(credit),
    )


def build_credit_order(
    legs: list[tuple[Option, OrderAction]],
    quantity: int,
    credit: Decimal,
    *,
    tif: OrderTimeInForce = OrderTimeInForce.DAY,
) -> NewOrder:
    """Generic multi-leg credit order from (option, action) pairs."""
    return NewOrder(
        time_in_force=tif,
        order_type=OrderType.LIMIT,
        legs=[opt.build_leg(quantity, action) for opt, action in legs],
        price=CREDIT_SIGN * abs(credit),
    )


def build_debit_order(
    legs: list[tuple[Option, OrderAction]],
    quantity: int,
    debit: Decimal,
    *,
    tif: OrderTimeInForce = OrderTimeInForce.DAY,
) -> NewOrder:
    """Generic multi-leg debit order (e.g. buying back a short strangle to close).

    A debit you pay is a POSITIVE price in the SDK's sign convention.
    """
    return NewOrder(
        time_in_force=tif,
        order_type=OrderType.LIMIT,
        legs=[opt.build_leg(quantity, action) for opt, action in legs],
        price=abs(debit),
    )


async def place(
    account: Account,
    session: Session,
    order: NewOrder,
    *,
    dry_run: bool = True,
) -> PlacedOrderResponse:
    """Place (or preflight) an order. dry_run=True validates without sending."""
    return await account.place_order(session, order, dry_run=dry_run)
