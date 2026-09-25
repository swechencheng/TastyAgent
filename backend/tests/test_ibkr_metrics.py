import os
import sqlite3
import tempfile
import pytest

from tastyagent.ibkr.metrics import (
    IVMetrics,
    _get_cached_metric,
    _init_cache_table,
    _save_cached_metric,
)


def test_iv_metrics_cache_save_and_retrieve():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        _init_cache_table(db_path)
        metric = IVMetrics(
            symbol="TEST",
            iv_rank=0.45,
            iv_percentile=0.55,
            current_iv=0.35,
            min_iv=0.20,
            max_iv=0.50,
        )
        today_str = "2026-09-25"
        _save_cached_metric(metric, today_str, db_path)

        cached = _get_cached_metric("TEST", today_str, db_path)
        assert cached is not None
        assert cached.symbol == "TEST"
        assert cached.iv_rank == 0.45
        assert cached.iv_percentile == 0.55
        assert cached.current_iv == 0.35
        assert cached.min_iv == 0.20
        assert cached.max_iv == 0.50

        # Different date should return None
        assert _get_cached_metric("TEST", "2026-09-24", db_path) is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_iv_rank_math_formula():
    cur_iv = 0.40
    min_iv = 0.20
    max_iv = 0.60
    ivr = (cur_iv - min_iv) / (max_iv - min_iv)
    assert ivr == pytest.approx(0.50)  # Exactly 50% IV rank
