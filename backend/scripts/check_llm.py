"""Verify the adaptive LLM layer: structured selection + prompt caching.

Builds synthetic guardrail-passing candidates and asks Claude to choose. Runs the
selection twice with a shared client so the second call should hit the cached system
prompt (cache_read_input_tokens > 0).

Run:  ./.venv/Scripts/python.exe scripts/check_llm.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from anthropic import AsyncAnthropic  # noqa: E402

from tastyagent.decision.llm import (  # noqa: E402
    SYSTEM_PROMPT,
    LLMDecision,
    build_user_message,
    select_trades,
)
from tastyagent.models import (  # noqa: E402
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
    client = AsyncAnthropic()

    # Direct call to inspect usage (caching) + parsed output.
    user_text, id_map = build_user_message(CANDIDATES, PORTFOLIO, REGIME)
    for i in (1, 2):
        resp = await client.messages.parse(
            model="claude-opus-4-8",
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_text}],
            output_format=LLMDecision,
        )
        u = resp.usage
        print(f"--- call {i}: cache_write={u.cache_creation_input_tokens} "
              f"cache_read={u.cache_read_input_tokens} input={u.input_tokens} "
              f"output={u.output_tokens}")

    decision: LLMDecision = resp.parsed_output
    print(f"\nCommentary: {decision.commentary}\n")
    print(f"Selections ({len(decision.selections)}):")
    for s in decision.selections:
        c = id_map[s.candidate_id]
        print(f"  - {s.candidate_id}: {s.contracts}x  (IVR {c.iv_rank:.0%})")
        print(f"      {s.rationale}")

    # Confirm the wrapper also works and filters hallucinations.
    d2, _ = await select_trades(CANDIDATES, PORTFOLIO, REGIME, client=client)
    print(f"\nWrapper select_trades returned {len(d2.selections)} valid selection(s).")


if __name__ == "__main__":
    asyncio.run(main())
