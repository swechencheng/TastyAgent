from dataclasses import replace

from tastyagent.config import RiskLimits
from tastyagent.risk.limits import PortfolioState, check_new_entry

LIMITS = RiskLimits()


def healthy_state(**overrides) -> PortfolioState:
    defaults = dict(
        net_liq=100_000.0,
        bp_used=10_000.0,
        open_positions=3,
        positions_for_symbol=0,
        realized_pnl_today=0.0,
        consecutive_losses=0,
    )
    defaults.update(overrides)
    return PortfolioState(**defaults)


def test_healthy_entry_allowed():
    assert check_new_entry("SPY", 2000.0, healthy_state(), LIMITS).ok


def test_kill_switch_blocks():
    limits = replace(LIMITS, kill_switch=True)
    res = check_new_entry("SPY", 2000.0, healthy_state(), limits)
    assert not res.ok
    assert any("kill switch" in v for v in res.violations)


def test_max_positions_blocks():
    res = check_new_entry("SPY", 2000.0, healthy_state(open_positions=15), LIMITS)
    assert not res.ok


def test_symbol_concentration_blocks():
    res = check_new_entry("SPY", 2000.0, healthy_state(positions_for_symbol=2), LIMITS)
    assert not res.ok


def test_total_bp_cap_blocks():
    # 39k used + 2k new = 41k > 40% of 100k
    res = check_new_entry("SPY", 2000.0, healthy_state(bp_used=39_000.0), LIMITS)
    assert not res.ok
    assert any("BP" in v for v in res.violations)


def test_daily_loss_halt_blocks():
    res = check_new_entry("SPY", 2000.0, healthy_state(realized_pnl_today=-3_500.0), LIMITS)
    assert not res.ok


def test_consecutive_loss_halt_blocks():
    res = check_new_entry("SPY", 2000.0, healthy_state(consecutive_losses=5), LIMITS)
    assert not res.ok
