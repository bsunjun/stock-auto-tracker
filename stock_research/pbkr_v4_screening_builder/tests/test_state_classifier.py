"""Doctrinal invariants for the seven-state classifier."""
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


def test_hard_exclude_short_circuits_everything():
    state = classify_state(
        risk_buckets=["HARD_EXCLUDE", "EXTREME_RISK_FLAG_WATCH"],
        market_structure_active=True,
        filters=ALL_PASS,
    )
    assert state == "HARD_EXCLUDE"


def test_market_structure_short_circuits_when_no_hard_flag():
    state = classify_state(
        risk_buckets=["EXTREME_RISK_FLAG_WATCH"],
        market_structure_active=True,
        filters=ALL_PASS,
    )
    assert state == "NO_ENTRY_MARKET_STRUCTURE_ACTIVE"


def test_extreme_risk_blocks_entry_even_with_clean_tape():
    state = classify_state(
        risk_buckets=["EXTREME_RISK_FLAG_WATCH"],
        market_structure_active=False,
        filters=ALL_PASS,
    )
    assert state == "EXTREME_RISK_FLAG_WATCH"


def test_regular_pb_excluded_when_tape_weak():
    state = classify_state(
        risk_buckets=["REGULAR_PB_EXCLUDE"],
        market_structure_active=False,
        filters={**ALL_PASS, "rs_pass": False},
    )
    assert state == "REGULAR_PB_EXCLUDE"


def test_risk_flag_pullback_watch_when_tape_constructive():
    state = classify_state(
        risk_buckets=["REGULAR_PB_EXCLUDE"],
        market_structure_active=False,
        filters=ALL_PASS,
    )
    # Watch-only label. Doctrine: this is NOT a PB_TRIGGER.
    assert state == "RISK_FLAG_PULLBACK_WATCH"


def test_clean_all_filters_pass_yields_watch_candidate():
    state = classify_state(
        risk_buckets=[],
        market_structure_active=False,
        filters=ALL_PASS,
    )
    assert state == "WATCH_CANDIDATE"


def test_partial_filters_yield_watch_only():
    state = classify_state(
        risk_buckets=[],
        market_structure_active=False,
        filters={**ALL_PASS, "trend_pass": False},
    )
    assert state == "WATCH_ONLY"


def test_market_structure_blocks_circuit_breaker():
    assert market_structure_blocks({"circuit_breaker_active": True, "sidecar_active": False, "auction_window": "none"})


def test_market_structure_blocks_sidecar():
    assert market_structure_blocks({"circuit_breaker_active": False, "sidecar_active": True, "auction_window": "none"})


def test_market_structure_blocks_opening_auction():
    assert market_structure_blocks({"circuit_breaker_active": False, "sidecar_active": False, "auction_window": "opening"})


def test_market_structure_clean_does_not_block():
    assert not market_structure_blocks({"circuit_breaker_active": False, "sidecar_active": False, "auction_window": "none"})
