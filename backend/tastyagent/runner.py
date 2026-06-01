"""The cycle tick: one full pass of the agent.

gather account state -> build market context -> generate candidates ->
orchestrator.run_cycle (pre-guardrail / LLM / post-LLM re-validation) ->
executor (mode-routed placement / approval queue) -> reconcile fills ->
persist an equity snapshot.

This is the single function the scheduler (or the API trigger) calls each interval.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import date

from sqlalchemy.orm import Session

from tastytrade.instruments import OptionType as TTOptionType, get_option_chain

from .config import TradingMode
from .db.models import EquitySnapshot
from .decision.context import DEFAULT_WATCHLIST, gather_context, rank_universe
from .decision.orchestrator import PortfolioInput, run_cycle
from .execution.executor import Executor
from .execution.exit_manager import PositionMark, RollResult, manage_exits
from .execution.sandbox_placer import SandboxPlacer, match_option
from .execution.tracker import reconcile_fills
from .models import OptionType
from .portfolio.benchmark import latest_sp500_close
from .portfolio.ledger import Ledger
from .portfolio.pnl import summarize
from .portfolio.watchlist import WatchlistRepo
from .strategy.candidates import build_strangle_candidate, generate_candidates, pick_expiration
from .strategy.exits import RollKind
from .tt.marketdata import get_underlying_price, select_by_delta, snapshot_options


async def _live_mark(client, trade) -> PositionMark:
    """Mark a position: total cost-to-close (sum of leg mids) + the tested short leg."""
    chain = await get_option_chain(client.session, trade.symbol)
    matched = [(leg, match_option(chain, leg)) for leg in trade.legs]
    snaps = await snapshot_options(
        client.session, [opt.streamer_symbol for _, opt in matched], timeout=8.0
    )
    total = 0.0
    short_deltas: list[tuple[OptionType, float]] = []
    for leg, opt in matched:
        snap = snaps.get(opt.streamer_symbol)
        if snap is None or snap.mid is None:
            raise RuntimeError("incomplete mark")
        total += float(snap.mid)
        if str(leg.action).startswith("sell") and snap.delta is not None:
            short_deltas.append((OptionType(leg.option_type), abs(snap.delta)))

    tested_side = max_short_delta = None
    if short_deltas:
        tested_side, max_short_delta = max(short_deltas, key=lambda x: x[1])
    return PositionMark(
        cost_to_close=total * 100 * trade.contracts,
        max_short_delta=max_short_delta,
        tested_side=tested_side,
    )


async def _build_roll_candidate(client, trade, roll_kind, mark, params):
    """Build the replacement strangle for a roll, or None if no good roll exists."""
    sym = trade.symbol
    today = date.today()
    chain = await get_option_chain(client.session, sym)
    underlying = float(await get_underlying_price(client.session, sym))
    lo, hi = underlying * 0.55, underlying * 1.45

    if roll_kind is RollKind.OUT:
        exp = pick_expiration(sorted(chain), params, today)  # next ~45 DTE cycle
        if exp is None:
            return None
        opts = [o for o in chain[exp] if lo <= float(o.strike_price) <= hi]
        snaps = await snapshot_options(
            client.session, [o.streamer_symbol for o in opts], timeout=8.0
        )
        put = select_by_delta(
            [o for o in opts if o.option_type == TTOptionType.PUT], snaps, params.target_short_delta
        )
        call = select_by_delta(
            [o for o in opts if o.option_type == TTOptionType.CALL], snaps, params.target_short_delta
        )
        if put is None or call is None:
            return None
        return build_strangle_candidate(
            sym, underlying, 1.0, (exp - today).days, put, call,
            snaps[put.streamer_symbol], snaps[call.streamer_symbol],
        )

    # ROLL UNTESTED: keep the current expiration and the tested strike, pull the
    # untested short leg toward the money for extra credit.
    tested_side = mark.tested_side
    exp = min((leg.expiration for leg in trade.legs), default=None)
    if tested_side is None or exp is None or exp not in chain:
        return None
    tested_leg = next((leg for leg in trade.legs if OptionType(leg.option_type) is tested_side), None)
    if tested_leg is None:
        return None
    opts = [o for o in chain[exp] if lo <= float(o.strike_price) <= hi]
    snaps = await snapshot_options(client.session, [o.streamer_symbol for o in opts], timeout=8.0)

    tt_tested = TTOptionType.PUT if tested_side is OptionType.PUT else TTOptionType.CALL
    tested_opt = next(
        (o for o in opts if o.option_type == tt_tested and abs(float(o.strike_price) - tested_leg.strike) < 0.01),
        None,
    )
    if tested_opt is None or tested_opt.streamer_symbol not in snaps:
        return None
    untested_tt = TTOptionType.CALL if tested_side is OptionType.PUT else TTOptionType.PUT
    untested_opt = select_by_delta(
        [o for o in opts if o.option_type == untested_tt], snaps, params.target_short_delta
    )
    if untested_opt is None:
        return None

    put, call = (
        (tested_opt, untested_opt) if tested_side is OptionType.PUT else (untested_opt, tested_opt)
    )
    return build_strangle_candidate(
        sym, underlying, 1.0, (exp - today).days, put, call,
        snaps[put.streamer_symbol], snaps[call.streamer_symbol],
    )


async def run_one_cycle(
    *,
    client,
    metrics_session,
    session: Session,
    runtime,
    watchlist: list[str] | None = None,
) -> dict:
    params = runtime.strategy
    # Sandbox quotes are 15-min delayed and artificially wide — relax the (only)
    # unreliable liquidity signal so forward-testing can place. Strict in live.
    if runtime.mode is TradingMode.SANDBOX:
        params = replace(params, max_bid_ask_width_pct=0.50)
    limits = runtime.risk_limits()
    ledger = Ledger(session)

    # Universe = the editable watchlist (seeded with the curated default on first run);
    # an explicit watchlist arg overrides it (used by scripts/tests).
    repo = WatchlistRepo(session)
    if not repo.all() and metrics_session is not None:
        from .tt.watchlists import seed_universe_from_tastytrade

        try:
            await seed_universe_from_tastytrade(repo, metrics_session)
        except Exception:  # noqa: BLE001 - fall back to the static default
            pass
    repo.seed_default_if_empty(DEFAULT_WATCHLIST)
    universe = watchlist or repo.symbols() or DEFAULT_WATCHLIST

    # 1. working capital. The sandbox seeds ~$1M with no withdrawal endpoint, so the
    # agent sizes/accounts against a configured working capital, not the broker balance.
    account = await client.primary_account()
    net_liq = runtime.starting_capital

    # 2. manage existing positions FIRST — close winners per the profit schedule so
    # freed buying power is available to the entry stage. Only in auto-placing modes;
    # taking profit shouldn't wait behind the approval queue's open gate.
    exit_outcomes = []
    placer = (
        SandboxPlacer(client)
        if runtime.mode in (TradingMode.SANDBOX, TradingMode.LIVE_AUTO)
        else runtime.placer
    )
    if isinstance(placer, SandboxPlacer):

        async def _roll(trade, roll_kind, mark):
            new_cand = await _build_roll_candidate(client, trade, roll_kind, mark, params)
            if new_cand is None or new_cand.net_credit <= 0:
                return None  # no credit roll -> exit_manager falls back to close
            await placer.close(trade, mark.cost_to_close)
            new_order_id = await placer.open_candidate(new_cand, trade.contracts)
            return RollResult(
                new_candidate=new_cand,
                contracts=trade.contracts,
                exit_debit=mark.cost_to_close,
                new_order_id=new_order_id,
            )

        exit_outcomes = await manage_exits(
            ledger,
            params,
            mark_fn=lambda t: _live_mark(client, t),
            close_fn=placer.close,
            roll_fn=_roll,
        )

    bp_used = sum(t.buying_power for t in ledger.open_trades())
    portfolio = PortfolioInput(
        net_liq=net_liq, bp_used=bp_used, positions_by_symbol=ledger.positions_by_symbol()
    )

    # 3. market context (IV rank for the WHOLE universe, one batched call) then do the
    # expensive chain/greeks work only on the top-N highest-IVR liquid names.
    metrics, regime = await gather_context(metrics_session, params, universe)
    top_symbols = rank_universe(metrics, params.universe_top_n)
    candidates = await generate_candidates(
        client, metrics_session, params, top_symbols, metrics=metrics
    )

    # 4. decide
    result = await run_cycle(candidates, portfolio, regime, params, limits)
    decision = ledger.record_decision(runtime.mode, result.commentary, result.considered)

    # 5. execute new entries (mode-routed; reuses the placer from the exit step)
    outcomes = await Executor(ledger, runtime.mode, placer).execute_cycle(result, decision)

    # 6. reconcile fills against live broker orders
    try:
        live = await account.get_live_orders(client.session)
        status_map = {str(o.id): getattr(o.status, "value", str(o.status)) for o in live}
        reconcile_fills(ledger, status_map)
    except Exception:  # noqa: BLE001 - reconciliation is best-effort
        pass

    # 7. equity snapshot (+ S&P close) for the dashboard's equity-vs-S&P curve
    summary = summarize(ledger.all_trades())
    sp_close = await asyncio.to_thread(latest_sp500_close)  # best-effort, off the event loop
    session.add(
        EquitySnapshot(
            net_liq=runtime.starting_capital + summary.realized_pnl + summary.unrealized_pnl,
            realized_pnl_cum=summary.realized_pnl,
            unrealized_pnl=summary.unrealized_pnl,
            sp500_close=sp_close,
        )
    )
    session.commit()

    return {
        "considered": result.considered,
        "planned": len(result.planned),
        "rejected": len(result.rejected),
        "exits": [o.__dict__ for o in exit_outcomes],
        "closed": sum(1 for o in exit_outcomes if o.action == "closed"),
        "outcomes": [o.__dict__ for o in outcomes],
        "commentary": result.commentary,
        "net_liq": net_liq,
        "open_positions": len(ledger.open_trades()),
        "universe_size": len(universe),
        "analyzed": top_symbols,
    }
