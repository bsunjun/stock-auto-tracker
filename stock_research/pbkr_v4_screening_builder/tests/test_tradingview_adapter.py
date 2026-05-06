"""TradingView adapter normalization tests.

Confirms the adapter is auxiliary-only: RS_SCORE / RS_PROXY is never
required, numeric inputs are bucketed into a categorical label, and
the legacy unprefixed input names are still accepted for back-compat.
"""
from __future__ import annotations

from stock_research.pbkr_v4_screening_builder.adapters.tradingview_mcp import (
    _bucket_rs_proxy,
    _normalize_row,
)


def test_rs_proxy_high_label_for_high_numeric():
    assert _bucket_rs_proxy(95) == "high"
    assert _bucket_rs_proxy(80) == "high"


def test_rs_proxy_mid_for_middle_numeric():
    assert _bucket_rs_proxy(65) == "mid"
    assert _bucket_rs_proxy(50) == "mid"


def test_rs_proxy_low_for_low_numeric():
    assert _bucket_rs_proxy(20) == "low"


def test_rs_proxy_absent_for_missing_or_invalid():
    assert _bucket_rs_proxy(None) == "absent"
    assert _bucket_rs_proxy("not_a_number") == "absent"


def test_rs_proxy_passthrough_for_valid_label():
    assert _bucket_rs_proxy("high") == "high"
    assert _bucket_rs_proxy("absent") == "absent"


def test_normalize_row_legacy_inputs_still_accepted():
    """Legacy field names map to the new tv_* outputs."""
    row = _normalize_row({
        "ticker": "AAA.KS",
        "name": "Synthetic Alpha",
        "ema_state": "above_21ema",
        "price_action_label": "post_breakout",
        "pullback_label": "shallow",
        "rs_proxy": 92.0,
    })
    assert row["tv_ema_state"] == "above_21ema"
    assert row["tv_price_action_label"] == "post_breakout"
    assert row["tv_pullback_state"] == "shallow"
    assert row["tv_rs_proxy_label"] == "high"
    # The output never carries a numeric rs_proxy field.
    assert "rs_proxy" not in row
    assert "ema_state" not in row


def test_normalize_row_new_tv_inputs_passed_through():
    row = _normalize_row({
        "ticker": "DDD.KQ",
        "name": "Synthetic Delta",
        "tv_ema_state": "alignment_up",
        "tv_price_action_label": "first_pullback",
        "tv_pullback_state": "shallow",
        "tv_rs_proxy_label": "high",
    })
    assert row["tv_ema_state"] == "alignment_up"
    assert row["tv_rs_proxy_label"] == "high"


def test_normalize_row_invalid_ema_state_falls_to_mixed():
    row = _normalize_row({"ticker": "X.KS", "tv_ema_state": "weird_value"})
    assert row["tv_ema_state"] == "mixed"
