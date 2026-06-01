"""Clean slate: cancel all live sandbox orders, flag open positions, wipe the ledger.

Use to clear out duplicate/working orders left from dev cycles.

Run:  ./.venv/Scripts/python.exe scripts/reset.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.db.session import DEFAULT_DB_PATH  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402
from tastyagent.tt.client import from_settings  # noqa: E402

_DEAD = {"Filled", "Cancelled", "Canceled", "Rejected", "Expired", "Removed"}


async def main() -> None:
    client = from_settings(load_settings())
    account = await client.primary_account()
    print(f"Account {account.account_number}")

    live = await account.get_live_orders(client.session)
    open_orders = [o for o in live if getattr(o.status, "value", str(o.status)) not in _DEAD]
    print(f"  {len(open_orders)} working order(s) to cancel")
    for o in open_orders:
        try:
            await account.delete_order(client.session, o.id)
            print(f"    cancelled order {o.id}")
        except Exception as e:  # noqa: BLE001
            print(f"    could not cancel {o.id}: {e}")

    try:
        complex_orders = await account.get_live_complex_orders(client.session)
        for o in complex_orders:
            try:
                await account.delete_complex_order(client.session, o.id)
                print(f"    cancelled complex order {o.id}")
            except Exception as e:  # noqa: BLE001
                print(f"    could not cancel complex {o.id}: {e}")
    except Exception:  # noqa: BLE001
        pass

    positions = await account.get_positions(client.session)
    if positions:
        print(f"  NOTE: {len(positions)} filled position(s) remain (sandbox clears these on the "
              f"daily reset; or close them manually):")
        for p in positions:
            print(f"    {p.symbol} qty={p.quantity}")
    else:
        print("  no filled positions")

    if DEFAULT_DB_PATH.exists():
        DEFAULT_DB_PATH.unlink()
        print(f"  deleted local ledger {DEFAULT_DB_PATH}")
    else:
        print("  no local ledger to delete")

    print("Done. The ledger will be recreated empty on next API start.")


if __name__ == "__main__":
    asyncio.run(main())
