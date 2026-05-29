"""Provision / re-fund the sandbox (cert) paper account.

The sandbox resets every 24h: trades, positions, and **balances** are cleared
(customers and accounts persist). So this is safe to re-run — and in fact must
be re-run after each reset to restore paper buying power.

What it does:
  1. Logs in with the sandbox user (username/password) to get a session token
     that has account-management scope (the OAuth grant does NOT).
  2. Ensures at least one account exists (creates one if none).
  3. Deposits up to TARGET_FUNDS so net liq is at least that amount.

Run:  ./.venv/Scripts/python.exe scripts/provision_sandbox.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CERT = "https://api.cert.tastyworks.com"
TARGET_FUNDS = 1_000_000.0


async def _session_token(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        "/sessions",
        json={
            "login": os.environ["TASTYTRADE_USERNAME"],
            "password": os.environ["TASTYTRADE_PASSWORD"],
        },
    )
    resp.raise_for_status()
    return resp.json()["data"]["session-token"]


async def main() -> None:
    headers = {"User-Agent": "tastyagent/0.1", "Content-Type": "application/json"}
    async with httpx.AsyncClient(base_url=CERT, headers=headers, timeout=60.0) as c:
        token = await _session_token(c)
        auth = {"Authorization": token}

        accounts = (await c.get("/customers/me/accounts", headers=auth)).json()
        nums = [i["account"]["account-number"] for i in accounts["data"]["items"]]
        if not nums:
            created = await c.post("/sandbox/customers/me/accounts", headers=auth, json={})
            created.raise_for_status()
            nums = [created.json()["data"]["account-number"]]
            print(f"Created account {nums[0]}")

        target = os.environ.get("TASTYTRADE_ACCOUNT") or nums[0]
        print(f"Funding account {target} (available: {nums})")

        # Fetch current net liq via the trade-scoped session token (works fine here).
        bal = (await c.get(f"/accounts/{target}/balances", headers=auth)).json()
        net_liq = float(bal["data"]["net-liquidating-value"])
        print(f"  current net liq: ${net_liq:,.2f}")

        if net_liq < TARGET_FUNDS:
            deposit = TARGET_FUNDS - net_liq
            r = await c.post(
                f"/sandbox/accounts/{target}/deposits",
                headers=auth,
                json={"amount": f"{deposit:.2f}"},
            )
            r.raise_for_status()
            print(f"  deposited ${deposit:,.2f}")
        else:
            print("  already funded; no deposit needed")


if __name__ == "__main__":
    asyncio.run(main())
