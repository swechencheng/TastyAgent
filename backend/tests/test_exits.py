from tastyagent.config import StrategyParams
from tastyagent.models import Strategy
from tastyagent.strategy.exits import ExitAction, evaluate_exit

from .conftest import make_position

PARAMS = StrategyParams()


def test_hold_when_no_trigger():
    # 20% profit at day 10 (avg for 20% is 6 -> behind pace), far from DTE
    pos = make_position(entry_credit=250.0, current_cost_to_close=200.0, days_held=10)
    d = evaluate_exit(pos, PARAMS)
    assert d.action is ExitAction.HOLD


def test_dte_backstop_fires_first():
    pos = make_position(current_cost_to_close=10.0, dte_remaining=21, days_held=30)
    d = evaluate_exit(pos, PARAMS)
    assert d.action is ExitAction.MANAGE_DTE


def test_fifty_percent_target_closes():
    pos = make_position(entry_credit=250.0, current_cost_to_close=125.0, days_held=30)
    d = evaluate_exit(pos, PARAMS)
    assert d.action is ExitAction.CLOSE
    assert "max-profit" in d.reason


def test_stop_loss_closes():
    # cost to close = 3x credit -> profit_pct = (250-750)/250 = -2.0
    pos = make_position(entry_credit=250.0, current_cost_to_close=750.0, days_held=5)
    d = evaluate_exit(pos, PARAMS)
    assert d.action is ExitAction.CLOSE
    assert "stop" in d.reason


def test_ahead_of_pace_closes_below_fifty():
    # 40% profit at day 8 (avg 10) -> ahead-of-pace closes even though < 50%
    pos = make_position(entry_credit=250.0, current_cost_to_close=150.0, days_held=8)
    d = evaluate_exit(pos, PARAMS)
    assert d.action is ExitAction.CLOSE
    assert "ahead of pace" in d.reason


def test_ahead_of_pace_does_not_fire_when_behind():
    # 40% profit at day 12 (> avg 10), below 50% -> hold
    pos = make_position(entry_credit=250.0, current_cost_to_close=150.0, days_held=12)
    d = evaluate_exit(pos, PARAMS)
    assert d.action is ExitAction.HOLD
