"""Verify market context and candidate generation using IBKR option chains and Greeks.

Run:
    python scripts/check_candidates.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.decision.context import gather_context  # noqa: E402
from tastyagent.ibkr.client import IBKRClient  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402
from tastyagent.strategy.candidates import generate_candidates  # noqa: E402
from tastyagent.strategy.guardrails import validate_candidate  # noqa: E402

WATCHLIST = ["SPY", "XLE", "TLT"]


async def main() -> None:
    settings = load_settings()
    params = settings.strategy_params()
    client = IBKRClient(settings)
    await client.connect()

    try:
        print(f"Gathering market context for {WATCHLIST}...")
        _metrics, regime = await gather_context(client.data_ib, params, WATCHLIST)
        print("REGIME:\n" + json.dumps(regime, indent=2))

        print("\nGenerating candidates (IBKR chains + Greeks streaming)...")
        candidates = await generate_candidates(client, None, params, WATCHLIST)
        print(f"\nGenerated {len(candidates)} candidate(s):")
        for c in candidates:
            gr = validate_candidate(c, params)
            strikes = "/".join(f"{leg.option_type.value}{leg.strike:g}" for leg in c.legs)
            print(
                f"  {c.symbol} {c.strategy.value} {strikes} dte={c.dte} "
                f"IVR={c.iv_rank:.0%} credit=${c.net_credit:,.0f} "
                f"bp=${c.buying_power_reduction:,.0f} width={c.liquidity.bid_ask_width_pct:.1%} "
                f"delta={c.max_short_leg_delta:.2f} -> {'PASS' if gr.ok else 'FAIL: ' + '; '.join(gr.violations)}"
            )

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
