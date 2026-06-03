"""
build_weekly_features.py — PBKR Quant Feature Screener v1

Weekly-bar features. Research-only; does NOT emit trade signals.
"""

from __future__ import annotations

from typing import List, Optional, Sequence


DOMAIN = "weekly"


def weekly_return_13w(weekly_closes: Sequence[float]) -> Optional[float]:
    if len(weekly_closes) < 14 or weekly_closes[-14] <= 0:
        return None
    return (weekly_closes[-1] / weekly_closes[-14] - 1.0) * 100.0


def sma(values: Sequence[float], window: int) -> Optional[float]:
    if len(values) < window or window <= 0:
        return None
    return sum(values[-window:]) / window


def slope(values: Sequence[float], window: int) -> Optional[float]:
    if len(values) < window + 1 or window <= 0:
        return None
    return values[-1] - values[-window - 1]


def build_weekly_row(
    ticker: str,
    asof_date: str,
    weekly_closes: Sequence[float],
) -> dict:
    ma10 = sma(weekly_closes, 10)
    ma30 = sma(weekly_closes, 30)
    ma10_history: List[float] = []
    for i in range(len(weekly_closes)):
        win = weekly_closes[max(0, i - 9): i + 1]
        if len(win) == 10:
            ma10_history.append(sum(win) / 10.0)
    ma10_slope = slope(ma10_history, 4) if ma10_history else None

    return {
        "ticker": ticker,
        "asof_date": asof_date,
        "weekly_return_13w": weekly_return_13w(weekly_closes),
        "weekly_ma10": ma10,
        "weekly_ma30": ma30,
        "weekly_ma10_slope": ma10_slope,
    }


def build_weekly_features(rows: List[dict]) -> List[dict]:
    return [dict(r) for r in rows]


if __name__ == "__main__":
    raise SystemExit(
        "build_weekly_features is a library; run examples/run_feature_screener_fixture.py instead."
    )
