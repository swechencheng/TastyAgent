from tastyagent.config import TradingMode
from tastyagent.db.models import TradeStatus
from tastyagent.db.session import in_memory_session
from tastyagent.portfolio.ledger import Ledger
from tastyagent.portfolio.pnl import summarize

from .conftest import make_candidate


def ledger() -> Ledger:
    return Ledger(in_memory_session())


def test_record_planned_sandbox_is_working_with_legs():
    lg = ledger()
    d = lg.record_decision(TradingMode.SANDBOX, "commentary", 3)
    c = make_candidate(max_profit=250.0, buying_power_reduction=2000.0)
    t = lg.record_planned(c, 2, "rationale", TradingMode.SANDBOX, d)
    assert t.status is TradeStatus.WORKING
    assert t.entry_credit == 500.0  # 250 * 2 contracts
    assert t.buying_power == 4000.0
    assert len(t.legs) == 2  # strangle
    assert t.legs[0].quantity == 2  # scaled by contracts


def test_mark_open_then_close_computes_realized():
    lg = ledger()
    d = lg.record_decision(TradingMode.SANDBOX, "", 0)
    c = make_candidate(max_profit=250.0)
    t = lg.record_planned(c, 1, "r", TradingMode.SANDBOX, d)
    lg.mark_open(t)
    assert t.status is TradeStatus.OPEN and t.entry_date is not None
    lg.close_trade(t, exit_debit=125.0, exit_reason="50% target")
    assert t.status is TradeStatus.CLOSED
    assert t.realized_pnl == 125.0  # 250 credit - 125 to close
    assert t.is_win is True


def test_positions_by_symbol():
    lg = ledger()
    d = lg.record_decision(TradingMode.SANDBOX, "", 0)
    for sym in ["SPY", "SPY", "QQQ"]:
        t = lg.record_planned(make_candidate(symbol=sym), 1, "r", TradingMode.SANDBOX, d)
        lg.mark_open(t)
    assert lg.positions_by_symbol() == {"SPY": 2, "QQQ": 1}
    assert len(lg.open_trades()) == 3


def test_pnl_summary_mixed_book():
    lg = ledger()
    d = lg.record_decision(TradingMode.SANDBOX, "", 0)
    c = make_candidate(max_profit=250.0)

    t_open = lg.record_planned(c, 1, "r", TradingMode.SANDBOX, d)
    lg.mark_open(t_open)
    lg.update_mark(t_open, 150.0)  # unrealized = 250 - 150 = 100

    t_win = lg.record_planned(c, 1, "r", TradingMode.SANDBOX, d)
    lg.mark_open(t_win)
    lg.close_trade(t_win, 100.0, "win")  # +150

    t_loss = lg.record_planned(c, 1, "r", TradingMode.SANDBOX, d)
    lg.mark_open(t_loss)
    lg.close_trade(t_loss, 500.0, "loss")  # -250

    s = summarize(lg.all_trades())
    assert s.unrealized_pnl == 100.0
    assert s.realized_pnl == -100.0  # 150 - 250
    assert s.total_pnl == 0.0
    assert (s.wins, s.losses) == (1, 1)
    assert s.win_rate == 0.5
    assert s.profit_pct(1_000_000) == 0.0
