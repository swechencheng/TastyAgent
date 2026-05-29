"""Broker placer: turn a recorded Trade into a real (sandbox/live) order.

Implements the ``Placer`` seam the Executor depends on. Given a persisted Trade
(with its legs), it reconstructs the option instruments from the live chain, builds
a multi-leg credit order, runs a dry-run preflight, then submits for real. Returns
the broker order id.

Used for SANDBOX and LIVE_AUTO. In LIVE_APPROVAL the same placer is invoked, but
only after the user approves via the dashboard.
"""

from __future__ import annotations

from decimal import Decimal

from tastytrade.instruments import OptionType as TTOptionType, get_option_chain
from tastytrade.order import OrderAction

from ..db.models import Trade
from ..tt.client import TastytradeClient
from ..tt.orders import build_credit_order, place

_ACTION = {
    "sell_to_open": OrderAction.SELL_TO_OPEN,
    "buy_to_open": OrderAction.BUY_TO_OPEN,
    "sell_to_close": OrderAction.SELL_TO_CLOSE,
    "buy_to_close": OrderAction.BUY_TO_CLOSE,
}
_TYPE = {"put": TTOptionType.PUT, "call": TTOptionType.CALL}


class SandboxPlacer:
    def __init__(self, client: TastytradeClient) -> None:
        self.client = client

    async def __call__(self, trade: Trade) -> str:
        account = await self.client.primary_account()
        chain = await get_option_chain(self.client.session, trade.symbol)

        leg_pairs = []
        for leg in trade.legs:
            opts = chain.get(leg.expiration, [])
            match = next(
                (
                    o
                    for o in opts
                    if o.option_type == _TYPE[leg.option_type]
                    and abs(float(o.strike_price) - leg.strike) < 0.01
                ),
                None,
            )
            if match is None:
                raise RuntimeError(
                    f"no instrument for {trade.symbol} {leg.option_type} "
                    f"{leg.strike} {leg.expiration}"
                )
            leg_pairs.append((match, _ACTION[leg.action]))

        # entry_credit is total dollars; convert to a per-share limit price rounded
        # to the $0.01 tick the exchange requires.
        per_share_credit = (
            Decimal(str(trade.entry_credit)) / Decimal(100 * trade.contracts)
        ).quantize(Decimal("0.01"))
        order = build_credit_order(leg_pairs, trade.contracts, per_share_credit)

        # Preflight: validate buying power / fees without sending.
        await place(account, self.client.session, order, dry_run=True)
        resp = await place(account, self.client.session, order, dry_run=False)
        return str(resp.order.id)
