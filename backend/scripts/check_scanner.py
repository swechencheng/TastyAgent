"""Verify IBKR Market Scanner for high options volume stock discovery.

Run:
    python scripts/check_scanner.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.ibkr.client import IBKRClient  # noqa: E402
from tastyagent.ibkr.scanner import scan_high_options_volume  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402


async def main() -> None:
    settings = load_settings()
    client = IBKRClient(settings)
    await client.connect()

    try:
        print(f"Running IBKR Market Scanner (scanCode={settings.ibkr_scan_code}, rows={settings.ibkr_scan_rows})...")
        symbols = await scan_high_options_volume(
            client.data_ib,
            num_rows=settings.ibkr_scan_rows,
            scan_code=settings.ibkr_scan_code,
        )
        print(f"\nDiscovered {len(symbols)} high option volume symbols:")
        for idx, sym in enumerate(symbols, 1):
            print(f"  {idx:>2}. {sym}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
