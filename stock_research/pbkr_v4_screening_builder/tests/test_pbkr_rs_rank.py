"""PBKR_RS_RANK behavioural tests."""
from __future__ import annotations

from stock_research.pbkr_v4_screening_builder.pbkr_rs_rank import (
    compute_pbkr_rs_rank,
    summarize_rs_rank,
)


def _flat(value: float, length: int = 280) -> list[float]:
    return [value] * length


def _ramp(start: float, daily_growth: float, length: int = 280) -> list[float]:
    closes: list[float] = [start]
    for _ in range(1, length):
        closes.append(closes[-1] * (1 + daily_growth))
    return closes


def test_strong_uptrend_outranks_flat():
    universe = {
        "STRONG": _ramp(100.0, 0.001),
        "FLAT": _flat(100.0),
    }
    ranks = compute_pbkr_rs_rank(universe)
    assert ranks["STRONG"] > ranks["FLAT"]
    assert 0 <= ranks["FLAT"] <= 100
    assert 0 <= ranks["STRONG"] <= 100


def test_short_history_returns_none():
    universe = {
        "SHORT": [100.0, 101.0, 102.0],  # too short for any horizon
    }
    ranks = compute_pbkr_rs_rank(universe)
    assert ranks["SHORT"] is None


def test_weights_sum_to_one_in_summary():
    universe = {"A": _ramp(100.0, 0.001), "B": _ramp(100.0, 0.0005)}
    ranks = compute_pbkr_rs_rank(universe)
    s = summarize_rs_rank(
        rs_ranks=ranks,
        threshold=80.0,
        weights={"m1": 0.20, "m3": 0.30, "m6": 0.30, "m12": 0.20},
        benchmark_used=False,
    )
    assert sum(s["weights"].values()) == 1.0
    assert s["universe_size"] == 2


def test_threshold_pass_count():
    universe = {
        "TOP1": _ramp(100.0, 0.0020),
        "TOP2": _ramp(100.0, 0.0015),
        "MID":  _ramp(100.0, 0.0005),
        "WEAK": _flat(100.0),
        "DOWN": _ramp(100.0, -0.0005),
    }
    ranks = compute_pbkr_rs_rank(universe)
    s = summarize_rs_rank(ranks, threshold=80.0, weights=None, benchmark_used=False)
    # With 5 names, percentile ranks are 0, 25, 50, 75, 100 -> only the
    # very top should clear 80. (TOP1 may share rank with TOP2 if ties
    # arise, but for distinct ramps the top-1 is unique.)
    assert s["passed_threshold_count"] >= 1
    assert s["passed_threshold_count"] <= 2


def test_benchmark_relative_does_not_change_ordering_when_universe_uniform():
    universe = {
        "A": _ramp(100.0, 0.0010),
        "B": _ramp(100.0, 0.0005),
    }
    benchmark = _ramp(100.0, 0.0007)
    ranks = compute_pbkr_rs_rank(universe, benchmark=benchmark)
    assert ranks["A"] >= ranks["B"]
