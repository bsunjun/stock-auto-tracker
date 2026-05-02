"""
build_price_features.py — PBKR Quant Feature Screener v1

Build per-(ticker, asof_date) price-domain features for the screener.

This is a research / candidate-compression utility. It does NOT emit
trade signals. It NEVER sets direct_trade_signal=true. It NEVER writes
to Drive. It NEVER promotes outputs to latest / SuperPack / rolling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


DOMAIN = "price"
SCHEMA_VERSION = "feature_table_v1"
DIRECT_TRADE_SIGNAL = False
TRADE_SIGNAL = None


@dataclass
class PriceBar:
    ticker: str
    asof_date: str
    close: float
    sector: Optional[str] = None


def ema(values: Sequence[float], span: int) -> Optional[float]:
    if not values or span <= 0:
        return None
    k = 2.0 / (span + 1.0)
    out = float(values[0])
    for v in values[1:]:
        out = float(v) * k + out * (1.0 - k)
    return out


def pct_diff(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return (a / b - 1.0) * 100.0


def relative_strength(
    asset_closes: Sequence[float],
    bench_closes: Sequence[float],
    window: int,
) -> Optional[float]:
    if len(asset_closes) < window + 1 or len(bench_closes) < window + 1:
        return None
    a_ret = asset_closes[-1] / asset_closes[-window - 1] - 1.0
    b_ret = bench_closes[-1] / bench_closes[-window - 1] - 1.0
    return (a_ret - b_ret) * 100.0


def percentile_rank(value: Optional[float], universe: Iterable[float]) -> Optional[float]:
    if value is None:
        return None
    pool = [v for v in universe if v is not None]
    if not pool:
        return None
    n_le = sum(1 for v in pool if v <= value)
    return 100.0 * n_le / len(pool)


def ibdrs_approx_from_rs(
    rs_20d: Optional[float],
    rs_60d: Optional[float],
    rs_120d: Optional[float],
    rs_252d: Optional[float],
    universe_blend: Iterable[float],
) -> Optional[float]:
    parts = [
        (0.40, rs_252d),
        (0.20, rs_120d),
        (0.20, rs_60d),
        (0.20, rs_20d),
    ]
    have = [(w, v) for w, v in parts if v is not None]
    if not have:
        return None
    s_w = sum(w for w, _ in have)
    blended = sum(w * v for w, v in have) / s_w
    p = percentile_rank(blended, universe_blend)
    if p is None:
        return None
    return min(99.0, max(0.0, p))


def stop_distance_pct(close: float, support: Optional[float]) -> Optional[float]:
    if support is None or close <= 0:
        return None
    return max(0.0, (close - support) / close * 100.0)


def build_price_features_row(
    bar: PriceBar,
    asset_close_history: Sequence[float],
    bench_close_history: Sequence[float],
    sector_close_history: Sequence[float],
    blended_universe_rs: Iterable[float],
    support_level: Optional[float],
) -> dict:
    rs_20 = relative_strength(asset_close_history, bench_close_history, 20)
    rs_60 = relative_strength(asset_close_history, bench_close_history, 60)
    rs_120 = relative_strength(asset_close_history, bench_close_history, 120)
    rs_252 = relative_strength(asset_close_history, bench_close_history, 252)
    sector_rs_20 = relative_strength(asset_close_history, sector_close_history, 20)
    sector_rs_60 = relative_strength(asset_close_history, sector_close_history, 60)

    ema20 = ema(asset_close_history[-60:], 20) if asset_close_history else None
    ema50 = ema(asset_close_history[-150:], 50) if asset_close_history else None
    ema150 = ema(asset_close_history[-450:], 150) if asset_close_history else None

    ibdrs = ibdrs_approx_from_rs(rs_20, rs_60, rs_120, rs_252, blended_universe_rs)

    return {
        "schema_version": SCHEMA_VERSION,
        "ticker": bar.ticker,
        "asof_date": bar.asof_date,
        "sector": bar.sector,
        "direct_trade_signal": DIRECT_TRADE_SIGNAL,
        "trade_signal": TRADE_SIGNAL,
        "close": bar.close,
        "ema20": ema20,
        "ema50": ema50,
        "ema150": ema150,
        "close_vs_ema20_pct": pct_diff(bar.close, ema20),
        "close_vs_ema50_pct": pct_diff(bar.close, ema50),
        "rs_20d": rs_20,
        "rs_60d": rs_60,
        "rs_120d": rs_120,
        "rs_252d": rs_252,
        "sector_rs_20d": sector_rs_20,
        "sector_rs_60d": sector_rs_60,
        "ibdrs_approx": ibdrs,
        "stop_distance_pct": stop_distance_pct(bar.close, support_level),
    }


def build_price_features(rows: List[dict]) -> List[dict]:
    """Pure pass-through hook for orchestrators; rows are pre-computed
    in fixture environments. Real-data ingestion is intentionally NOT
    implemented in this skeleton."""
    return [dict(r) for r in rows]


if __name__ == "__main__":
    raise SystemExit(
        "build_price_features is a library; run examples/run_feature_screener_fixture.py instead."
    )
