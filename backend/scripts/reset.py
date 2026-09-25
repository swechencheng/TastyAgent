"""Clean slate: cancel IBTastyAgent working orders and wipe the local SQLite ledger.

IMPORTANT: This script strictly respects position isolation.
It ONLY cancels orders where orderRef starts with 'TastyAgent_'.
Any manual orders or orders from other bots/strategies on the account are untouched.

Run:
    python scripts/reset.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.db.session import DEFAULT_DB_PATH  # noqa: E402
from tastyagent.ibkr.client import IBKRClient  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402


async def main() -> None:
    settings = load_settings()
    client = IBKRClient(settings)
    await client.connect()

    try:
        print(f"Connected to IBKR account {client.account}")
        open_trades = client.trading_ib.openTrades()
        ta_trades = []
        other_trades = []

        for t in open_trades:
            ref = getattr(t.order, "orderRef", "")
            if ref.startswith("TastyAgent_"):
                ta_trades.append(t)
            else:
                other_trades.append(t)

        print(f"Found {len(open_trades)} total open orders:")
        print(f"  - IBTastyAgent orders: {len(ta_trades)}")
        print(f"  - Other account orders (protected): {len(other_trades)}")

        for t in ta_trades:
            print(
                f"  Cancelling IBTastyAgent order {t.order.orderId} ({t.contract.symbol}, ref={t.order.orderRef})..."
            )
            client.trading_ib.cancelOrder(t.order)

        if other_trades:
            print(
                f"\n  [PROTECTION] Preserving {len(other_trades)} non-IBTastyAgent open orders."
            )

    finally:
        await client.disconnect()

    if DEFAULT_DB_PATH.exists():
        DEFAULT_DB_PATH.unlink()
        print(f"\nDeleted local SQLite ledger: {DEFAULT_DB_PATH}")
    else:
        print("\nNo local SQLite ledger found to delete.")

    print("Reset completed safely.")


if __name__ == "__main__":
    asyncio.run(main())
