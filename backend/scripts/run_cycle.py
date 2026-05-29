"""Run ONE full decision cycle against the sandbox and print the result.

Persists to the default DB (backend/data/tastyagent.db) so the dashboard reflects it.
In sandbox mode this will place a real *paper* order for any surviving candidate.

Run:  ./.venv/Scripts/python.exe scripts/run_cycle.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from tastyagent.api.runtime import Runtime  # noqa: E402
from tastyagent.db.session import init_db, make_engine, session_factory  # noqa: E402
from tastyagent.runner import run_one_cycle  # noqa: E402
from tastyagent.settings import load_settings  # noqa: E402
from tastyagent.tt.client import from_settings, metrics_session_from_env  # noqa: E402

WATCHLIST = ["SPY", "XLE", "TLT"]


async def main() -> None:
    settings = load_settings()
    client = from_settings(settings)
    metrics_session = metrics_session_from_env()

    engine = make_engine()
    init_db(engine)
    session = session_factory(engine)()

    runtime = Runtime(mode=settings.mode, strategy=settings.strategy_params())
    print(f"Running one cycle in {runtime.mode.value} mode over {WATCHLIST}...\n")
    result = await run_one_cycle(
        client=client,
        metrics_session=metrics_session,
        session=session,
        runtime=runtime,
        watchlist=WATCHLIST,
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
