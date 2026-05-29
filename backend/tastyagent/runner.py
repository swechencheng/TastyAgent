"""The cycle tick: one full pass of the agent.

gather account state -> build market context -> generate candidates ->
orchestrator.run_cycle (pre-guardrail / LLM / post-LLM re-validation) ->
executor (mode-routed placement / approval queue) -> reconcile fills ->
persist an equity snapshot.

This is the single function the scheduler (or the API trigger) calls each interval.
"""

from __future__ import annotations

from dataclasses import replace

from sqlalchemy.orm import Session

from .config import TradingMode
from .db.models import EquitySnapshot
from .decision.context import DEFAULT_WATCHLIST, gather_context
from .decision.orchestrator import PortfolioInput, run_cycle
from .execution.executor import Executor
from .execution.sandbox_placer import SandboxPlacer
from .execution.tracker import reconcile_fills
from .portfolio.ledger import Ledger
from .portfolio.pnl import summarize
from .strategy.candidates import generate_candidates


async def run_one_cycle(
    *,
    client,
    metrics_session,
    session: Session,
    runtime,
    watchlist: list[str] | None = None,
) -> dict:
    watchlist = watchlist or DEFAULT_WATCHLIST
    params = runtime.strategy
    # Sandbox quotes are 15-min delayed and artificially wide — relax the (only)
    # unreliable liquidity signal so forward-testing can place. Strict in live.
    if runtime.mode is TradingMode.SANDBOX:
        params = replace(params, max_bid_ask_width_pct=0.50)
    limits = runtime.risk_limits()
    ledger = Ledger(session)

    # 1. account state
    account = await client.primary_account()
    balances = await account.get_balances(client.session)
    net_liq = float(balances.net_liquidating_value)
    bp_used = sum(t.buying_power for t in ledger.open_trades())
    portfolio = PortfolioInput(
        net_liq=net_liq, bp_used=bp_used, positions_by_symbol=ledger.positions_by_symbol()
    )

    # 2. market context + candidates
    _metrics, regime = await gather_context(metrics_session, params, watchlist)
    candidates = await generate_candidates(client, metrics_session, params, watchlist)

    # 3. decide
    result = await run_cycle(candidates, portfolio, regime, params, limits)
    decision = ledger.record_decision(runtime.mode, result.commentary, result.considered)

    # 4. execute (mode-routed)
    placer = (
        SandboxPlacer(client)
        if runtime.mode in (TradingMode.SANDBOX, TradingMode.LIVE_AUTO)
        else runtime.placer
    )
    outcomes = await Executor(ledger, runtime.mode, placer).execute_cycle(result, decision)

    # 5. reconcile fills against live broker orders
    try:
        live = await account.get_live_orders(client.session)
        status_map = {str(o.id): getattr(o.status, "value", str(o.status)) for o in live}
        reconcile_fills(ledger, status_map)
    except Exception:  # noqa: BLE001 - reconciliation is best-effort
        pass

    # 6. equity snapshot for the dashboard's equity curve
    summary = summarize(ledger.all_trades())
    session.add(
        EquitySnapshot(
            net_liq=net_liq,
            realized_pnl_cum=summary.realized_pnl,
            unrealized_pnl=summary.unrealized_pnl,
        )
    )
    session.commit()

    return {
        "considered": result.considered,
        "planned": len(result.planned),
        "rejected": len(result.rejected),
        "outcomes": [o.__dict__ for o in outcomes],
        "commentary": result.commentary,
        "net_liq": net_liq,
        "open_positions": len(ledger.open_trades()),
    }
