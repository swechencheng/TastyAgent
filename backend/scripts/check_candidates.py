"""Live check: market context + candidate generation against sandbox + prod metrics.

Run:  ./.venv/Scripts/python.exe scripts/check_candidates.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.decision.context import gather_context  # noqa: E402
from tastyagent.strategy.candidates import generate_candidates  # noqa: E402
from tastyagent.strategy.guardrails import validate_candidate  # noqa: E402
from tastyagent.tt.client import from_settings, metrics_session_from_env  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402

WATCHLIST = ["SPY", "XLE", "TLT"]


async def main() -> None:
    settings = load_settings()
    params = settings.strategy_params()
    client = from_settings(settings)
    metrics_session = metrics_session_from_env()
    if metrics_session is None:
        raise SystemExit("No prod metrics grant configured.")

    print("Gathering market context...")
    _metrics, regime = await gather_context(metrics_session, params, WATCHLIST)
    print("REGIME:\n" + json.dumps(regime, indent=2))

    print("\nGenerating candidates (sandbox chains + greeks)...")
    candidates = await generate_candidates(client, metrics_session, params, WATCHLIST)
    print(f"\n{len(candidates)} candidate(s):")
    for c in candidates:
        gr = validate_candidate(c, params)
        strikes = "/".join(f"{leg.option_type.value}{leg.strike:g}" for leg in c.legs)
        print(
            f"  {c.symbol} {c.strategy.value} {strikes} dte={c.dte} "
            f"IVR={c.iv_rank:.0%} credit=${c.net_credit:,.0f} "
            f"bp=${c.buying_power_reduction:,.0f} width={c.liquidity.bid_ask_width_pct:.1%} "
            f"delta={c.max_short_leg_delta:.2f} -> {'PASS' if gr.ok else 'FAIL: ' + '; '.join(gr.violations)}"
        )


if __name__ == "__main__":
    asyncio.run(main())
