"""Run ONE full decision cycle against IBKR Gateway and print the result.

Persists to the default DB (backend/data/tastyagent.db) so the dashboard reflects it.
In sandbox mode this will place a paper order with an attached 50% Take Profit limit order.

Run:
    python scripts/run_cycle.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.api.runtime import Runtime  # noqa: E402
from tastyagent.db.session import init_db, make_engine, session_factory  # noqa: E402
from tastyagent.ibkr.client import IBKRClient  # noqa: E402
from tastyagent.runner import run_one_cycle  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402

WATCHLIST = ["TLT", "XLE"]


async def main() -> None:
    settings = load_settings()
    client = IBKRClient(settings)
    await client.connect()

    engine = make_engine()
    init_db(engine)
    session = session_factory(engine)()

    runtime = Runtime(
        mode=settings.mode,
        strategy=settings.strategy_params(),
        ibkr_walk_step=settings.ibkr_walk_step,
        ibkr_walk_interval=settings.ibkr_walk_interval,
        ibkr_attach_tp=settings.ibkr_attach_tp,
        ibkr_tp_pct=settings.ibkr_tp_pct,
    )
    print(f"Running one cycle in {runtime.mode.value} mode over {WATCHLIST}...\n")

    try:
        result = await run_one_cycle(
            client=client,
            metrics_session=None,
            session=session,
            runtime=runtime,
            watchlist=WATCHLIST,
        )
        print(json.dumps(result, indent=2, default=str))
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
