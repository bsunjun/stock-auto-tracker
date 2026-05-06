"""Doctrinal invariants for the five-state classifier."""
from __future__ import annotations

from stock_research.pbkr_v4_screening_builder.state_classifier import (
    classify_state,
    market_structure_blocks,
)


ALL_PASS = {
    "rs_pass": True,
    "trading_value_pass": True,
    "ema_pass": True,
    "trend_pass": True,
    "structure_pass": True,
}


def test_hard_designation_collapses_to_screening_exclude():
    state, reason = classify_state(
        risk_buckets=["HARD_EXCLUDE", "EXTREME_RISK_FLAG_WATCH"],
        market_structure_active=True,
        filters=ALL_PASS,
    )
    assert state == "SCREENING_EXCLUDE"
    assert reason == "hard_designation"


def test_market_structure_collapses_to_screening_exclude():
    state, reason = classify_state(
        risk_buckets=["EXTREME_RISK_FLAG_WATCH"],
        market_structure_active=True,
        filters=ALL_PASS,
    )
    assert state == "SCREENING_EXCLUDE"
    assert reason == "market_structure"


def test_extreme_risk_collapses_to_screening_exclude():
    state, reason = classify_state(
        risk_buckets=["EXTREME_RISK_FLAG_WATCH"],
        market_structure_active=False,
        filters=ALL_PASS,
    )
    assert state == "SCREENING_EXCLUDE"
    assert reason == "extreme_risk_flag"


def test_regular_pb_excluded_when_tape_weak():
    state, reason = classify_state(
        risk_buckets=["REGULAR_PB_EXCLUDE"],
        market_structure_active=False,
        filters={**ALL_PASS, "rs_pass": False},
    )
    assert state == "REGULAR_PB_EXCLUDE"
    assert reason == "regular_pb_designation"


def test_risk_flag_pullback_watch_when_tape_constructive():
    state, reason = classify_state(
        risk_buckets=["REGULAR_PB_EXCLUDE"],
        market_structure_active=False,
        filters=ALL_PASS,
    )
    # Watch-only label. Doctrine: NEVER promotes to PB_TRIGGER.
    assert state == "RISK_FLAG_PULLBACK_WATCH"
    assert reason == "regular_pb_designation_watch"


def test_clean_all_filters_pass_yields_watch_candidate():
    state, reason = classify_state(
        risk_buckets=[],
        market_structure_active=False,
        filters=ALL_PASS,
    )
    assert state == "WATCH_CANDIDATE"
    assert reason == "all_filters_pass"


def test_partial_filters_yield_watch_only():
    state, reason = classify_state(
        risk_buckets=[],
        market_structure_active=False,
        filters={**ALL_PASS, "trend_pass": False},
    )
    assert state == "WATCH_ONLY"
    assert reason == "partial_filters"


def test_classifier_only_emits_allowed_states():
    """Defensive: every output must be in the 5-state allowed set."""
    from stock_research.pbkr_v4_screening_builder.constants import ALLOWED_SCREENING_STATES

    bool_grid = [
        {"rs_pass": rs, "trading_value_pass": tv, "ema_pass": e,
         "trend_pass": t, "structure_pass": s}
        for rs in (True, False)
        for tv in (True, False)
        for e in (True, False)
        for t in (True, False)
        for s in (True, False)
    ]
    bucket_combos = (
        [],
        ["HARD_EXCLUDE"],
        ["EXTREME_RISK_FLAG_WATCH"],
        ["REGULAR_PB_EXCLUDE"],
        ["HARD_EXCLUDE", "REGULAR_PB_EXCLUDE"],
    )
    for buckets in bucket_combos:
        for ms in (True, False):
            for filters in bool_grid:
                state, _ = classify_state(buckets, ms, filters)
                assert state in ALLOWED_SCREENING_STATES, (state, buckets, ms, filters)


def test_market_structure_blocks_circuit_breaker():
    assert market_structure_blocks({"circuit_breaker_active": True, "sidecar_active": False, "auction_window": "none"})


def test_market_structure_blocks_sidecar():
    assert market_structure_blocks({"circuit_breaker_active": False, "sidecar_active": True, "auction_window": "none"})


def test_market_structure_blocks_opening_auction():
    assert market_structure_blocks({"circuit_breaker_active": False, "sidecar_active": False, "auction_window": "opening"})


def test_market_structure_clean_does_not_block():
    assert not market_structure_blocks({"circuit_breaker_active": False, "sidecar_active": False, "auction_window": "none"})
