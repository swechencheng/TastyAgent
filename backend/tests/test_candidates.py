from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from tastyagent.config import StrategyParams
from tastyagent.models import Action, Strategy
from tastyagent.strategy.candidates import (
    build_strangle_candidate,
    estimate_undefined_bp,
    pick_expiration,
)
from tastyagent.strategy.guardrails import validate_candidate
from tastyagent.tt.marketdata import OptionSnapshot

PARAMS = StrategyParams()
TODAY = date(2026, 1, 1)


def test_pick_expiration_nearest_in_window():
    exps = [TODAY + timedelta(days=d) for d in (10, 40, 45, 50, 90)]
    assert pick_expiration(exps, PARAMS, TODAY) == TODAY + timedelta(days=45)


def test_pick_expiration_none_when_all_outside_window():
    exps = [TODAY + timedelta(days=d) for d in (5, 10, 120)]
    assert pick_expiration(exps, PARAMS, TODAY) is None


def test_estimate_undefined_bp():
    assert estimate_undefined_bp(100.0) == 2000.0


def _opt(strike):
    return SimpleNamespace(
        strike_price=Decimal(str(strike)),
        expiration_date=TODAY + timedelta(days=45),
        streamer_symbol=f"x{strike}",
    )


def _snap(sym, bid, ask, delta):
    return OptionSnapshot(streamer_symbol=sym, bid=Decimal(str(bid)), ask=Decimal(str(ask)), delta=delta)


def test_build_strangle_candidate_passes_guardrails():
    c = build_strangle_candidate(
        "SPY", 100.0, 0.45, 45,
        _opt(90), _opt(110),
        _snap("xp", 1.0, 1.1, -0.16), _snap("xc", 1.2, 1.3, 0.15),
    )
    assert c is not None
    assert c.strategy is Strategy.SHORT_STRANGLE
    assert round(c.net_credit, 2) == 230.0  # (1.05 + 1.25) * 100
    assert c.max_loss == float("inf")
    assert c.legs[0].action is Action.SELL_TO_OPEN
    assert c.max_short_leg_delta == 0.16
    assert validate_candidate(c, PARAMS).ok


def test_build_returns_none_without_quotes():
    c = build_strangle_candidate(
        "SPY", 100.0, 0.45, 45,
        _opt(90), _opt(110),
        OptionSnapshot("xp", None, None, -0.16), _snap("xc", 1.2, 1.3, 0.15),
    )
    assert c is None
