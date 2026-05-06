"""Deterministic generator for synthetic PBKR v4 screening fixtures.

Run from the repo root:

    python -m stock_research.pbkr_v4_screening_builder.fixtures.generate_synthetic_fixtures

All output is anonymized (`AAA.KS`, `BBB.KQ`, …) and seeded so the
fixtures are bit-for-bit reproducible. No real ticker, no real OHLCV,
no broker data.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Each profile is shaped to land a synthetic ticker in a specific
# screening state. Drift is the daily mean log-return; vol is the
# log-return stdev; trend tilt is added near the end of the window
# to control 1M/3M ranking.
PROFILES = [
    # (ticker, name, drift, vol, trend_tilt, base_price, designations,
    #  trading_value_krw, ema_state, price_action, pullback, rs_proxy)
    # AAA: dominant momentum, clean — should land WATCH_CANDIDATE (RS top).
    ("AAA.KS", "Synthetic Alpha",  0.0030, 0.010, 0.0020, 25_000.0, [],
     8_000_000_000.0, "above_21ema",  "post_breakout_continuation", "shallow", 92.0),
    # BBB: mid momentum, EMA mixed — control row, falls into WATCH_ONLY.
    ("BBB.KQ", "Synthetic Bravo",  0.0006, 0.018, 0.0004, 12_000.0, [],
     6_500_000_000.0, "mixed",        "consolidation",              "none",    65.0),
    # CCC: weak momentum + 투자주의 — REGULAR_PB_EXCLUDE.
    ("CCC.KS", "Synthetic Charlie", 0.0004, 0.020, 0.0001, 18_000.0, ["투자주의"],
     5_500_000_000.0, "below_21ema",  "rolling_over",               "deep",    None),
    # DDD: strong momentum + 투자경고 — RISK_FLAG_PULLBACK_WATCH (RS top-3 + good trend).
    ("DDD.KQ", "Synthetic Delta",   0.0024, 0.013, 0.0017, 22_000.0, ["투자경고"],
     7_200_000_000.0, "above_21ema",  "first_pullback",             "shallow", 88.0),
    # EEE: middling momentum + 투자위험 — EXTREME_RISK_FLAG_WATCH.
    ("EEE.KS", "Synthetic Echo",    0.0010, 0.022, 0.0006, 30_000.0, ["투자위험"],
     6_800_000_000.0, "above_21ema",  "high_volatility_rally",      "shallow", 81.0),
    # FFF: 관리종목 + 거래정지 — HARD_EXCLUDE.
    ("FFF.KQ", "Synthetic Foxtrot", -0.0030, 0.030, -0.0020, 9_000.0, ["관리종목", "거래정지"],
     4_500_000_000.0, "below_21ema",  "broken",                     "broken",  None),
    # GGG: strong momentum, clean, alignment_up — WATCH_CANDIDATE (RS top-2).
    ("GGG.KS", "Synthetic Golf",    0.0027, 0.010, 0.0019, 35_000.0, [],
     9_500_000_000.0, "alignment_up", "stage2_advance",             "shallow", 95.0),
    # HHH..KKK: low-momentum filler so the universe size lets top-3
    # ranks clear the 80 percentile threshold cleanly.
    ("HHH.KQ", "Synthetic Hotel",   -0.0008, 0.022, -0.0006, 7_500.0, [],
     4_200_000_000.0, "below_21ema",  "downtrend",                  "broken",  None),
    ("III.KS", "Synthetic India",   -0.0006, 0.018, -0.0004, 11_000.0, [],
     3_800_000_000.0, "below_21ema",  "downtrend",                  "broken",  None),
    ("JJJ.KQ", "Synthetic Juliett", -0.0002, 0.016, -0.0001, 14_000.0, [],
     5_000_000_000.0, "mixed",        "range_bound",                "none",    None),
    ("KKK.KS", "Synthetic Kilo",     0.0001, 0.014,  0.0000, 20_000.0, [],
     5_200_000_000.0, "mixed",        "range_bound",                "none",    None),
]

LEN = 280  # > 252 + 1 to support 12M look-back


def _series(rng: random.Random, drift: float, vol: float, tilt: float, base: float) -> list[float]:
    closes: list[float] = [base]
    for i in range(1, LEN):
        # tilt ramps in over the last 60 trading days
        t = max(0, i - (LEN - 60)) / 60.0
        ret = rng.normalvariate(drift + tilt * t, vol)
        closes.append(max(closes[-1] * math.exp(ret), 1.0))
    return [round(c, 2) for c in closes]


def _ma(series: list[float], window: int) -> float | None:
    if len(series) < window:
        return None
    return round(sum(series[-window:]) / window, 4)


def _atr14(closes: list[float]) -> float:
    diffs = [abs(closes[i] - closes[i - 1]) for i in range(1, 15) if i < len(closes)]
    return round(sum(diffs) / max(len(diffs), 1), 4)


def _max_window(series: list[float], window: int) -> float:
    sl = series[-window:]
    return round(max(sl), 2)


def _min_window(series: list[float], window: int) -> float:
    sl = series[-window:]
    return round(min(sl), 2)


def main() -> None:
    rng = random.Random(20260506)

    universe_tickers = {}
    feature_rows = []
    tradingview_rows = []
    risk_rows = []

    benchmark_closes = _series(rng, drift=0.0003, vol=0.009, tilt=0.0, base=2700.0)

    for (
        tkr, name, drift, vol, tilt, base, designations, trading_value,
        ema_state, price_action, pullback, rs_proxy,
    ) in PROFILES:
        closes = _series(rng, drift=drift, vol=vol, tilt=tilt, base=base)
        universe_tickers[tkr] = {"closes": closes}

        last = closes[-1]
        ma9, ma21, ma50, ma120 = (_ma(closes, w) for w in (9, 21, 50, 120))
        atr14 = _atr14(closes)
        recent_low = _min_window(closes, 20)
        # synthetic stop: last - max(2*ATR, 0.5*(last-recent_low))
        stop_distance = round(max(2.0 * atr14, 0.5 * max(last - recent_low, 1.0)), 4)

        feature_rows.append({
            "ticker": tkr,
            "close": last,
            "open": round(closes[-2], 2),
            "high": round(max(closes[-2], last) * 1.005, 2),
            "low": round(min(closes[-2], last) * 0.995, 2),
            "volume": int(rng.uniform(50_000, 600_000)),
            "trading_value": trading_value,
            "volume_ratio": round(rng.uniform(0.7, 3.2), 2),
            "investor_flow": round(rng.uniform(-3.0e9, 3.0e9), 0),
            "foreigner_flow": round(rng.uniform(-2.0e9, 4.0e9), 0),
            "institution_flow": round(rng.uniform(-2.0e9, 2.0e9), 0),
            "financial_investment_flow": round(rng.uniform(-1.0e9, 1.5e9), 0),
            "ma9": ma9,
            "ma21": ma21,
            "ma50": ma50,
            "ma120": ma120,
            "atr14": atr14,
            "recent_low": recent_low,
            "stop_distance": stop_distance,
            "high_20d": _max_window(closes, 20),
            "high_60d": _max_window(closes, 60),
        })

        tradingview_rows.append({
            "ticker": tkr,
            "name": name,
            "target_ema": 21,
            "ema_state": ema_state,
            "price_action_label": price_action,
            "pullback_label": pullback,
            "rs_proxy": rs_proxy,
        })

        risk_rows.append({
            "ticker": tkr,
            "raw_designations": designations,
        })

    universe = {
        "benchmark": {"ticker": "BENCHMARK_KOSPI_PROXY", "closes": benchmark_closes},
        "tickers": universe_tickers,
    }

    risk_pack = {
        "market_structure": {
            "circuit_breaker_active": False,
            "sidecar_active": False,
            "auction_window": "none",
        },
        "rows": risk_rows,
    }

    (HERE / "kiwoom_universe_synthetic.json").write_text(
        json.dumps(universe, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    (HERE / "kiwoom_features_synthetic.json").write_text(
        json.dumps({"rows": feature_rows}, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    (HERE / "tradingview_scan_synthetic.json").write_text(
        json.dumps({"source": "synthetic_tradingview_scan", "rows": tradingview_rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (HERE / "official_risk_synthetic.json").write_text(
        json.dumps(risk_pack, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    print(f"wrote synthetic fixtures to {HERE}")


if __name__ == "__main__":
    main()
