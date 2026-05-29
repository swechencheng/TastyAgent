from datetime import date

from tastyagent.portfolio.benchmark import compare


def test_compare_rebases_sp_and_computes_returns():
    eq = [(date(2026, 1, 1), 100_000.0), (date(2026, 2, 1), 110_000.0)]  # +10%
    sp = [(date(2026, 1, 1), 5000.0), (date(2026, 2, 1), 5250.0)]  # +5%
    c = compare(eq, sp)
    assert round(c.strategy_return_pct, 4) == 0.10
    assert round(c.sp500_return_pct, 4) == 0.05
    assert round(c.outperformance_pct, 4) == 0.05
    # S&P series rebased to the strategy's starting capital
    assert c.sp500_curve[0][1] == 100_000.0
    assert round(c.sp500_curve[1][1], 2) == 105_000.0


def test_compare_handles_empty():
    c = compare([], [])
    assert c.strategy_return_pct == 0.0
    assert c.sp500_return_pct == 0.0
