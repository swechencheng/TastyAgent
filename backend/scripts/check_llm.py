"""Verify the adaptive LLM layer: structured selection via OpenRouter.

Builds synthetic guardrail-passing candidates and asks OpenRouter LLM to choose.
Default model is deepseek/deepseek-v4.1-flash, or whatever is specified in OPENROUTER_MODEL.

Run:  ./.venv/Scripts/python.exe scripts/check_llm.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.decision.llm import (
    DEFAULT_MODEL,
    select_trades,
)
from tastyagent.models import (
    Action,
    CandidateTrade,
    Leg,
    Liquidity,
    OptionType,
    Strategy,
)

EXP = dt.date.today() + dt.timedelta(days=45)


def leg(ot, strike, delta):
    return Leg(option_type=ot, strike=strike, expiration=EXP, action=Action.SELL_TO_OPEN, delta=delta)


CANDIDATES = [
    CandidateTrade(
        symbol="SPY", strategy=Strategy.SHORT_STRANGLE,
        legs=(leg(OptionType.PUT, 710, -0.16), leg(OptionType.CALL, 800, 0.15)),
        dte=45, net_credit=6.40, max_profit=640, max_loss=float("inf"),
        buying_power_reduction=18000, underlying_price=757,
        iv_rank=0.34, liquidity=Liquidity(0.03, 12000, 5000), earnings_in_days=None,
    ),
    CandidateTrade(
        symbol="XLE", strategy=Strategy.NAKED_PUT,
        legs=(leg(OptionType.PUT, 85, -0.18),),
        dte=46, net_credit=1.30, max_profit=130, max_loss=float("inf"),
        buying_power_reduction=1700, underlying_price=92,
        iv_rank=0.61, liquidity=Liquidity(0.05, 6000, 1500), earnings_in_days=None,
    ),
    CandidateTrade(
        symbol="AMD", strategy=Strategy.PUT_CREDIT_SPREAD,
        legs=(leg(OptionType.PUT, 150, -0.20),
              Leg(OptionType.PUT, 140, EXP, Action.BUY_TO_OPEN, -0.12)),
        dte=44, net_credit=2.10, max_profit=210, max_loss=790,
        buying_power_reduction=790, underlying_price=178,
        iv_rank=0.48, liquidity=Liquidity(0.04, 9000, 4000), earnings_in_days=None,
    ),
]

PORTFOLIO = {
    "net_liq": 1_100_000.0,
    "buying_power_used": 22_000.0,
    "buying_power_used_pct": 0.02,
    "open_positions": 1,
    "open_symbols": ["IWM"],
}
REGIME = {"vix": 17.5, "trend": "range-bound", "note": "moderate IV across indices"}


async def main() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
    print(f"Connecting to OpenRouter with model: {model}")

    if not api_key:
        print("WARNING: OPENROUTER_API_KEY is not set in environment or backend/.env.")
        print("Set OPENROUTER_API_KEY to test actual live API inference.")
        return

    decision, id_map = await select_trades(CANDIDATES, PORTFOLIO, REGIME)

    print(f"\nCommentary: {decision.commentary}\n")
    print(f"Selections ({len(decision.selections)}):")
    for s in decision.selections:
        c = id_map.get(s.candidate_id)
        ivr_str = f"{c.iv_rank:.0%}" if c else "?"
        print(f"  - {s.candidate_id}: {s.contracts}x  (IVR {ivr_str})")
        print(f"      {s.rationale}")

    print(f"\nSuccessfully returned {len(decision.selections)} valid selection(s).")


if __name__ == "__main__":
    asyncio.run(main())
