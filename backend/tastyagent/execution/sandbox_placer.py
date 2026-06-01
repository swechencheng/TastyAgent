"""Broker placer: turn a recorded Trade into a real (sandbox/live) order.

Implements the ``Placer`` seam the Executor depends on. Given a persisted Trade
(with its legs), it reconstructs the option instruments from the live chain, builds
a multi-leg order, runs a dry-run preflight, then submits for real. Returns the
broker order id.

- ``__call__`` opens the position (credit order, stored leg actions).
- ``close`` buys it back (debit order, inverted actions) for exit management.

Used for SANDBOX and LIVE_AUTO. In LIVE_APPROVAL the opening placer is invoked only
after the user approves via the dashboard.
"""

from __future__ import annotations

from decimal import Decimal

from tastytrade.instruments import Option, OptionType as TTOptionType, get_option_chain
from tastytrade.order import OrderAction

from ..db.models import Trade, TradeLeg
from ..tt.client import TastytradeClient
from ..tt.orders import build_credit_order, build_debit_order, place

_ACTION = {
    "sell_to_open": OrderAction.SELL_TO_OPEN,
    "buy_to_open": OrderAction.BUY_TO_OPEN,
    "sell_to_close": OrderAction.SELL_TO_CLOSE,
    "buy_to_close": OrderAction.BUY_TO_CLOSE,
}
# Opening action -> the action that closes it.
_CLOSE_ACTION = {
    "sell_to_open": OrderAction.BUY_TO_CLOSE,
    "buy_to_open": OrderAction.SELL_TO_CLOSE,
}
_TYPE = {"put": TTOptionType.PUT, "call": TTOptionType.CALL}


def match_option(chain: dict, leg: TradeLeg) -> Option:
    """Find the Option instrument matching a stored trade leg."""
    for o in chain.get(leg.expiration, []):
        if o.option_type == _TYPE[leg.option_type] and abs(float(o.strike_price) - leg.strike) < 0.01:
            return o
    raise RuntimeError(
        f"no instrument for {leg.option_type} {leg.strike} exp {leg.expiration}"
    )


def _tick(price: Decimal) -> Decimal:
    return price.quantize(Decimal("0.01"))


class SandboxPlacer:
    def __init__(self, client: TastytradeClient) -> None:
        self.client = client

    async def __call__(self, trade: Trade) -> str:
        """Open the position for a net credit."""
        account = await self.client.primary_account()
        chain = await get_option_chain(self.client.session, trade.symbol)
        leg_pairs = [(match_option(chain, leg), _ACTION[leg.action]) for leg in trade.legs]

        per_share_credit = _tick(Decimal(str(trade.entry_credit)) / Decimal(100 * trade.contracts))
        order = build_credit_order(leg_pairs, trade.contracts, per_share_credit)

        await place(account, self.client.session, order, dry_run=True)  # preflight
        resp = await place(account, self.client.session, order, dry_run=False)
        return str(resp.order.id)

    async def open_candidate(self, candidate, contracts: int) -> str:
        """Open a position directly from a CandidateTrade (used when rolling)."""
        account = await self.client.primary_account()
        chain = await get_option_chain(self.client.session, candidate.symbol)
        leg_pairs = [(match_option(chain, leg), _ACTION[leg.action]) for leg in candidate.legs]

        per_share_credit = _tick(Decimal(str(candidate.max_profit)) / Decimal(100))
        order = build_credit_order(leg_pairs, contracts, per_share_credit)

        await place(account, self.client.session, order, dry_run=True)
        resp = await place(account, self.client.session, order, dry_run=False)
        return str(resp.order.id)

    async def close(self, trade: Trade, debit_total: float) -> str:
        """Buy the position back to close, paying ``debit_total`` dollars."""
        account = await self.client.primary_account()
        chain = await get_option_chain(self.client.session, trade.symbol)
        leg_pairs = [(match_option(chain, leg), _CLOSE_ACTION[leg.action]) for leg in trade.legs]

        per_share_debit = _tick(Decimal(str(debit_total)) / Decimal(100 * trade.contracts))
        order = build_debit_order(leg_pairs, trade.contracts, per_share_debit)

        await place(account, self.client.session, order, dry_run=True)  # preflight
        resp = await place(account, self.client.session, order, dry_run=False)
        return str(resp.order.id)
