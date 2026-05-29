"""Verify IV rank via the PRODUCTION read-only grant.

Run this once you've added TASTYTRADE_PROD_CLIENT_SECRET and
TASTYTRADE_PROD_OAUTH_REFRESH_TOKEN to backend/.env (a read-scope prod grant).

Run:  ./.venv/Scripts/python.exe scripts/check_metrics.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from tastyagent.tt.client import metrics_session_from_env  # noqa: E402
from tastyagent.tt.metrics import MarketMetricsUnavailable, get_iv_metrics  # noqa: E402

SYMBOLS = ["SPY", "QQQ", "AAPL", "TSLA"]


async def main() -> None:
    session = metrics_session_from_env()
    if session is None:
        raise SystemExit(
            "No prod read-only credentials in .env "
            "(TASTYTRADE_PROD_CLIENT_SECRET / TASTYTRADE_PROD_OAUTH_REFRESH_TOKEN)."
        )

    print("Production read-only session established. Fetching market metrics...")
    try:
        metrics = await get_iv_metrics(session, SYMBOLS)
    except MarketMetricsUnavailable as e:
        raise SystemExit(f"Still unavailable: {e}")

    print(f"\n{'symbol':<8}{'IV rank':>10}{'IV %ile':>10}{'liq':>6}  next earnings")
    for sym in SYMBOLS:
        m = metrics.get(sym)
        if not m:
            print(f"{sym:<8}{'(no data)':>10}")
            continue
        ivr = f"{m.iv_rank:.1%}" if m.iv_rank is not None else "n/a"
        ivp = f"{m.iv_percentile:.1%}" if m.iv_percentile is not None else "n/a"
        print(f"{sym:<8}{ivr:>10}{ivp:>10}{str(m.liquidity_rating):>6}  {m.next_earnings}")


if __name__ == "__main__":
    asyncio.run(main())
