"""Verify 1-year historical IV Rank & Percentile computation with SQLite caching via IBKR.

Run:
    python scripts/check_metrics.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import time

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.ibkr.client import IBKRClient  # noqa: E402
from tastyagent.ibkr.metrics import get_iv_metrics  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402

SYMBOLS = ["SPY", "QQQ", "AAPL", "NVDA"]


async def main() -> None:
    settings = load_settings()
    client = IBKRClient(settings)
    await client.connect()

    try:
        print(f"Fetching 1-year historical IV and calculating IV Rank for {SYMBOLS}...")
        t0 = time.time()
        metrics = await get_iv_metrics(client.data_ib, SYMBOLS)
        elapsed = time.time() - t0
        print(f"Initial fetch completed in {elapsed:.2f}s\n")

        print(f"{'symbol':<8}{'IV Rank':>10}{'IV %ile':>10}{'Current IV':>12}{'52w Range (Min-Max)':>24}")
        print("-" * 66)
        for sym in SYMBOLS:
            m = metrics.get(sym)
            if not m or m.iv_rank is None:
                print(f"{sym:<8}{'(no data)':>10}")
                continue
            ivr_str = f"{m.iv_rank:.1%}"
            ivp_str = f"{m.iv_percentile:.1%}" if m.iv_percentile is not None else "N/A"
            cur_iv = f"{m.current_iv:.1%}" if m.current_iv is not None else "N/A"
            rng = f"{m.min_iv:.1%} - {m.max_iv:.1%}" if m.min_iv is not None and m.max_iv is not None else "N/A"
            print(f"{sym:<8}{ivr_str:>10}{ivp_str:>10}{cur_iv:>12}{rng:>24}")

        # Test cache hit speed
        print("\nTesting daily SQLite cache hit...")
        t1 = time.time()
        cached_metrics = await get_iv_metrics(client.data_ib, SYMBOLS)
        cached_elapsed = time.time() - t1
        print(f"Cached retrieval completed in {cached_elapsed * 1000:.2f} ms (instant!)")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
