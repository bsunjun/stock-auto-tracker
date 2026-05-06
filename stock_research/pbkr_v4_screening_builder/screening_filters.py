"""Screening filter rules and per-candidate label generators.

Filter contract (every candidate carries a per-rule boolean):

  rs_pass            pbkr_rs_rank is not None and >= rs_threshold
  trading_value_pass trading_value >= min_trading_value
  ema_pass           close >= ma21 OR ma9 >= ma21 >= ma50
  trend_pass         ma50 >= ma120 (long-trend up)
  structure_pass     close near 20d/60d high OR a non-empty
                     pullback / price_action label is present

A candidate enters ``WATCH_CANDIDATE`` only when **all** boolean
filters pass. Partial pass yields ``WATCH_ONLY`` (subject to risk
overrides).
"""
from __future__ import annotations

from typing import Any


def _bool(x: Any) -> bool:
    return bool(x) if x is not None else False


def evaluate_filters(
    feature: dict[str, Any],
    pbkr_rs_rank: float | None,
    rs_threshold: float,
    min_trading_value: float,
    tv_row: dict[str, Any] | None,
) -> dict[str, bool]:
    close = feature.get("close") or 0.0
    ma9, ma21, ma50, ma120 = (
        feature.get("ma9"),
        feature.get("ma21"),
        feature.get("ma50"),
        feature.get("ma120"),
    )
    high_20d = feature.get("high_20d")
    high_60d = feature.get("high_60d")

    rs_pass = pbkr_rs_rank is not None and pbkr_rs_rank >= rs_threshold

    trading_value = feature.get("trading_value") or 0.0
    trading_value_pass = trading_value >= min_trading_value

    ema_pass = False
    if ma21 is not None and close >= ma21:
        ema_pass = True
    elif ma9 is not None and ma21 is not None and ma50 is not None:
        if ma9 >= ma21 >= ma50:
            ema_pass = True

    if ma50 is not None and ma120 is not None:
        trend_pass = ma50 >= ma120
    else:
        trend_pass = False

    near_high = False
    if high_20d and close >= 0.97 * high_20d:
        near_high = True
    elif high_60d and close >= 0.92 * high_60d:
        near_high = True

    label_evidence = False
    if tv_row:
        if (tv_row.get("tv_price_action_label") or "").strip():
            label_evidence = True
        pullback = (tv_row.get("tv_pullback_state") or "").strip().lower()
        # any non-empty, non-"none" pullback label is evidence
        if pullback and pullback != "none":
            label_evidence = True

    structure_pass = bool(near_high or label_evidence)

    return {
        "rs_pass": _bool(rs_pass),
        "trading_value_pass": _bool(trading_value_pass),
        "ema_pass": _bool(ema_pass),
        "trend_pass": _bool(trend_pass),
        "structure_pass": _bool(structure_pass),
    }


def label_volume(feature: dict[str, Any]) -> str:
    vr = feature.get("volume_ratio")
    if vr is None:
        return "n_a"
    if vr < 0.6:
        return "dry"
    if vr < 1.5:
        return "normal"
    if vr < 3.0:
        return "expansion"
    return "climax"


def label_pullback(feature: dict[str, Any], tv_row: dict[str, Any] | None) -> str:
    """Combine TradingView's pullback hint with MA-based fallback."""
    if tv_row:
        raw = (tv_row.get("tv_pullback_state") or "").strip().lower()
        if raw in ("none", "shallow", "deep", "broken"):
            return raw

    close, ma21, ma50 = feature.get("close"), feature.get("ma21"), feature.get("ma50")
    if close is None or ma21 is None or ma50 is None:
        return "n_a"
    if close >= ma21:
        return "none"
    if close >= ma50:
        return "shallow"
    if close >= 0.95 * ma50:
        return "deep"
    return "broken"


def label_stop_distance(feature: dict[str, Any]) -> str:
    sd = feature.get("stop_distance")
    atr = feature.get("atr14")
    close = feature.get("close")

    # Prefer stop_distance / close if both available; else stop_distance / atr.
    if sd is None:
        return "n_a"
    if close and close > 0:
        ratio = sd / close
        if ratio <= 0.04:
            return "tight"
        if ratio <= 0.08:
            return "normal"
        return "wide"
    if atr and atr > 0:
        atr_mult = sd / atr
        if atr_mult <= 1.0:
            return "tight"
        if atr_mult <= 2.0:
            return "normal"
        return "wide"
    return "n_a"
