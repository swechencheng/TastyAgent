"""Place ONE real short strangle in the sandbox so a trade is visible.

Flow: select ~16-delta SPY strikes ~45 DTE -> dry-run preflight (shows credit,
buying-power effect, fees) -> place the live (paper) order -> print live orders
and positions.

Run:  ./.venv/Scripts/python.exe scripts/demo_trade.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from tastytrade import Account, Session  # noqa: E402
from tastytrade.instruments import OptionType, get_option_chain  # noqa: E402

from tastyagent.tt.marketdata import select_by_delta, snapshot_options  # noqa: E402
from tastyagent.tt.orders import build_short_strangle, place  # noqa: E402

TARGET_DTE = 45
TARGET_DELTA = 0.16
QUANTITY = 1
TICK = Decimal("0.05")


def round_tick(x: Decimal) -> Decimal:
    return (x / TICK).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * TICK


async def main() -> None:
    session = Session(
        os.environ["TASTYTRADE_CLIENT_SECRET"],
        os.environ["TASTYTRADE_OAUTH_REFRESH_TOKEN"],
        is_test=True,
        timeout=30,  # sandbox order endpoints are slow; default httpx timeout is too low
    )
    account = await Account.get(session, os.environ["TASTYTRADE_ACCOUNT"])
    print(f"Account {account.account_number}")

    chain = await get_option_chain(session, "SPY")
    target = dt.date.today() + dt.timedelta(days=TARGET_DTE)
    exp = min(chain.keys(), key=lambda d: abs((d - target).days))
    opts = chain[exp]
    print(f"Expiration {exp} (DTE {opts[0].days_to_expiration}), {len(opts)} options")

    # Narrow to a near-the-money band so the greeks snapshot is fast/reliable.
    strikes = sorted({float(o.strike_price) for o in opts})
    spot = strikes[len(strikes) // 2]
    band = [o for o in opts if 0.80 * spot <= float(o.strike_price) <= 1.20 * spot]
    snaps = await snapshot_options(session, [o.streamer_symbol for o in band], timeout=15)

    puts = [o for o in band if o.option_type == OptionType.PUT]
    calls = [o for o in band if o.option_type == OptionType.CALL]
    put = select_by_delta(puts, snaps, TARGET_DELTA)
    call = select_by_delta(calls, snaps, TARGET_DELTA)
    if not put or not call:
        raise SystemExit("Could not find delta-matched strikes (no greeks).")

    ps, cs = snaps[put.streamer_symbol], snaps[call.streamer_symbol]
    print(f"\nShort put  {put.strike_price}  delta={ps.delta:+.3f}  mid={ps.mid}")
    print(f"Short call {call.strike_price}  delta={cs.delta:+.3f}  mid={cs.mid}")

    credit = round_tick(Decimal(ps.mid) + Decimal(cs.mid))
    print(f"Net credit (limit): ${credit}")

    order = build_short_strangle(put, call, QUANTITY, credit)

    print("\n--- DRY RUN (preflight) ---")
    pre = await place(account, session, order, dry_run=True)
    bpe = pre.buying_power_effect
    print(f"  order price     : {pre.order.price}  (negative = credit)")
    print(f"  buying power eff: {bpe.effect}")
    print(f"  margin req chg  : {bpe.change_in_margin_requirement}")
    print(f"  buying power chg: {bpe.change_in_buying_power}")
    print(f"  fees            : {pre.fee_calculation.total_fees if pre.fee_calculation else 'n/a'}")
    if pre.warnings:
        print(f"  warnings        : {[w.message for w in pre.warnings]}")
    if pre.errors:
        raise SystemExit(f"ABORT: preflight errors: {[e.message for e in pre.errors]}")

    # Safety: never place unless the preflight confirms we receive a credit.
    if pre.order.price is None or pre.order.price >= 0:
        raise SystemExit(f"ABORT: preflight price {pre.order.price} is not a credit")

    print("\n--- PLACING LIVE (paper) ORDER ---")
    placed = await place(account, session, order, dry_run=False)
    po = placed.order
    print(f"  order id : {po.id}")
    print(f"  status   : {po.status}")
    print(f"  legs     : {[(leg.symbol, leg.action, leg.quantity) for leg in po.legs]}")

    live = await account.get_live_orders(session)
    print(f"\nLive orders now: {len(live)}")
    for o in live:
        print(f"  - {o.id} {o.status} {o.underlying_symbol} {o.order_type} price={o.price}")

    positions = await account.get_positions(session)
    print(f"\nOpen positions now: {len(positions)}")
    for p in positions:
        print(f"  - {p.symbol} qty={p.quantity} {p.quantity_direction}")


if __name__ == "__main__":
    asyncio.run(main())
