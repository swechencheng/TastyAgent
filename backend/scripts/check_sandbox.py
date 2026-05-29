"""Sandbox connectivity check: verify OAuth login and inspect response shapes.

Run:  ./.venv/Scripts/python.exe scripts/check_sandbox.py
Reads credentials from backend/.env. Sandbox quotes are 15-min delayed and the
environment resets every 24h.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from tastytrade import Account, Session  # noqa: E402


async def main() -> None:
    client_secret = os.environ["TASTYTRADE_CLIENT_SECRET"]
    refresh_token = os.environ["TASTYTRADE_OAUTH_REFRESH_TOKEN"]

    print("Creating sandbox OAuth session...")
    session = Session(client_secret, refresh_token, is_test=True)
    print("  OK. OAuth session established (sandbox/cert).")

    accounts = await Account.get(session)
    print(f"\nAccounts ({len(accounts)}):")
    for acct in accounts:
        print(f"  - {acct.account_number}  nickname={getattr(acct, 'nickname', None)!r}")

    if accounts:
        acct = accounts[0]
        bal = await acct.get_balances(session)
        print(f"\nBalances for {acct.account_number}:")
        print(f"  net liquidating value : {bal.net_liquidating_value}")
        print(f"  cash balance          : {bal.cash_balance}")
        print(f"  maintenance excess    : {getattr(bal, 'maintenance_excess', None)}")

        positions = await acct.get_positions(session)
        print(f"\nOpen positions: {len(positions)}")
        for p in positions[:5]:
            print(f"  - {p.symbol} qty={p.quantity} {p.instrument_type}")


if __name__ == "__main__":
    asyncio.run(main())
