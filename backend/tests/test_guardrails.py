from tastyagent.config import StrategyParams
from tastyagent.models import Liquidity
from tastyagent.strategy.guardrails import filter_candidates, validate_candidate

from .conftest import make_candidate

PARAMS = StrategyParams()


def test_healthy_candidate_passes():
    assert validate_candidate(make_candidate(), PARAMS).ok


def test_low_iv_rank_rejected():
    res = validate_candidate(make_candidate(iv_rank=0.10), PARAMS)
    assert not res.ok
    assert any("iv_rank" in v for v in res.violations)


def test_dte_out_of_window_rejected():
    assert not validate_candidate(make_candidate(dte=7), PARAMS).ok
    assert not validate_candidate(make_candidate(dte=90), PARAMS).ok


def test_excess_short_delta_rejected():
    from tastyagent.models import Action, OptionType
    from .conftest import make_leg

    fat = make_candidate(
        legs=(make_leg(OptionType.PUT, 95.0, Action.SELL_TO_OPEN, -0.45),),
    )
    res = validate_candidate(fat, PARAMS)
    assert not res.ok
    assert any("delta" in v for v in res.violations)


def test_non_credit_rejected():
    assert not validate_candidate(make_candidate(net_credit=0.0), PARAMS).ok


def test_illiquid_rejected():
    illiquid = make_candidate(
        liquidity=Liquidity(bid_ask_width_pct=0.30, open_interest=10, daily_volume=5)
    )
    res = validate_candidate(illiquid, PARAMS)
    assert not res.ok
    assert len(res.violations) >= 3


def test_earnings_blackout_rejected():
    assert not validate_candidate(make_candidate(earnings_in_days=2), PARAMS).ok
    assert validate_candidate(make_candidate(earnings_in_days=30), PARAMS).ok


def test_filter_keeps_only_passing():
    good = make_candidate()
    bad = make_candidate(iv_rank=0.05)
    assert filter_candidates([good, bad], PARAMS) == [good]
