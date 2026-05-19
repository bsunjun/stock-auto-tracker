"""Deepvue-style preset screens for Korean equities.

The screenshots supplied by the operator describe four presets:
Stage Analysis Leaders, William O'Neil CANSLIM, Mark Minervini Trend
Template, and Deepvue Leaders.  This module implements those predicates
against normalized Kiwoom daily data plus DART-derived fundamentals.

TradingView MCP can still supply labels for review, but hard numerical gates
come from Kiwoom/DART-compatible fields so Korean-market screens do not depend
on TradingView's delayed fundamentals.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from .constants import RS_WINDOW_DAYS, SIGNAL_SAFETY_BLOCK
from .pbkr_rs_rank import _percentile_rank, _trailing_return


DEFAULT_USD_KRW = 1350.0
COMMON_EQUITY_TYPES = {"common", "common_stock", "common stock", "adr", "depositary_receipt"}
PRESET_NAMES = ("stage_analysis_leaders", "canslim_growth", "minervini_trend_template", "deepvue_leaders")


@dataclass(frozen=True)
class PresetResult:
    name: str
    passed: bool
    predicates: dict[str, bool]


def _f(v: Any) -> float | None:
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def _pct_return(closes: list[float], window: int) -> float | None:
    return _trailing_return(closes, window)


def _value_at_least(v: Any, threshold: float) -> bool:
    x = _f(v)
    return x is not None and x > threshold


def _value_ge(v: Any, threshold: float) -> bool:
    x = _f(v)
    return x is not None and x >= threshold


def _within_pct_of_high(close: float | None, high: float | None, max_off_pct: float) -> bool:
    if close is None or high is None or high <= 0:
        return False
    return ((close / high) - 1.0) * 100.0 > -abs(max_off_pct)


def _above_pct_from_low(close: float | None, low: float | None, min_up_pct: float) -> bool:
    if close is None or low is None or low <= 0:
        return False
    return ((close / low) - 1.0) * 100.0 > min_up_pct


def _ma(row: dict[str, Any], days: int) -> float | None:
    return _f(row.get(f"ma{days}") or row.get(f"sma{days}"))


def _close(row: dict[str, Any]) -> float | None:
    return _f(row.get("close") or row.get("last"))


def _sma(closes: list[float], window: int, end_offset: int = 0) -> float | None:
    end = len(closes) - end_offset
    if end <= 0 or end < window:
        return None
    sl = closes[end - window:end]
    return sum(sl) / len(sl) if sl else None


def _series(row: dict[str, Any], universe_closes: list[float] | None = None) -> list[float]:
    raw = row.get("closes") or universe_closes or []
    return [x for x in (_f(v) for v in raw) if x is not None]


def _avg_volume(row: dict[str, Any], days: int) -> float | None:
    explicit = _f(row.get(f"avg_volume_{days}d") or row.get(f"avg_vol_{days}d"))
    if explicit is not None:
        return explicit
    volumes = row.get("volumes") or []
    vals = [x for x in (_f(v) for v in volumes) if x is not None]
    if not vals:
        return None
    sl = vals[-days:] if len(vals) >= days else vals
    return sum(sl) / len(sl)


def _avg_trading_value(row: dict[str, Any], days: int) -> float | None:
    explicit = _f(
        row.get(f"avg_trading_value_{days}d")
        or row.get(f"avg_dollar_volume_{days}d_krw")
        or row.get(f"avg_value_{days}d")
    )
    if explicit is not None:
        return explicit
    close = _close(row)
    avg_vol = _avg_volume(row, days)
    if close is None or avg_vol is None:
        return _f(row.get("trading_value"))
    return close * avg_vol


def _adr_pct(row: dict[str, Any], days: int) -> float | None:
    for key in (f"adr_pct_{days}d", f"adr_{days}d_pct", f"adr_percent_{days}d"):
        v = _f(row.get(key))
        if v is not None:
            return v
    highs = [_f(v) for v in row.get("highs", [])]
    lows = [_f(v) for v in row.get("lows", [])]
    closes = [_f(v) for v in row.get("closes", [])]
    triples = [(h, l, c) for h, l, c in zip(highs, lows, closes) if h and l and c and c > 0]
    if not triples:
        return None
    sl = triples[-days:] if len(triples) >= days else triples
    return sum(((h - l) / c) * 100.0 for h, l, c in sl) / len(sl)


def _equity_type_pass(row: dict[str, Any]) -> bool:
    raw = str(row.get("security_type") or row.get("include_type") or row.get("type") or "common").strip().lower()
    return raw in COMMON_EQUITY_TYPES


def _ipo_after(row: dict[str, Any], fundamentals: dict[str, Any], cutoff: str) -> bool:
    raw = row.get("ipo_date") or row.get("listing_date") or fundamentals.get("ipo_date")
    if not raw:
        return False
    try:
        return date.fromisoformat(str(raw)[:10]) > date.fromisoformat(cutoff)
    except ValueError:
        return False


def _rs_pctile_by_horizon(universe: dict[str, list[float]], horizon_key: str) -> dict[str, float]:
    window = RS_WINDOW_DAYS[horizon_key]
    returns = {t: r for t, closes in universe.items() if (r := _pct_return(closes, window)) is not None}
    return _percentile_rank(returns)


def compute_absolute_strength_ranks(universe: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    """Return Deepvue-style AS percentiles for 1W/1M/3M/6M/12M returns."""
    windows = {"as_1w": 5, "as_1m": 21, "as_3m": 63, "as_6m": 126, "as_12m": 252}
    out = {ticker: {} for ticker in universe}
    for label, window in windows.items():
        returns = {t: r for t, closes in universe.items() if (r := _pct_return(closes, window)) is not None}
        for ticker, rank in _percentile_rank(returns).items():
            out.setdefault(ticker, {})[label] = rank
    return out


def compute_industry_ranks(
    universe: dict[str, list[float]],
    ticker_to_industry: dict[str, str],
) -> dict[str, dict[str, float]]:
    """Compute 1-based industry rank by median member return for 3M/6M."""
    result = {ticker: {} for ticker in universe}
    for label, window in (("industry_rank_3m", 63), ("industry_rank_6m", 126)):
        by_industry: dict[str, list[float]] = {}
        for ticker, closes in universe.items():
            industry = ticker_to_industry.get(ticker)
            ret = _pct_return(closes, window)
            if industry and ret is not None:
                by_industry.setdefault(industry, []).append(ret)
        medians = {
            industry: sorted(vals)[len(vals) // 2]
            for industry, vals in by_industry.items()
            if vals
        }
        ranked = {industry: i + 1 for i, (industry, _) in enumerate(sorted(medians.items(), key=lambda kv: kv[1], reverse=True))}
        for ticker, industry in ticker_to_industry.items():
            if ticker in result and industry in ranked:
                result[ticker][label] = float(ranked[industry])
    return result


def _stage_analysis_pass(row: dict[str, Any], as_rank: dict[str, float], industry_rank: dict[str, float], usd_krw: float) -> PresetResult:
    stage = str(row.get("weinstein_stage") or row.get("stage") or "").strip().upper()
    predicates = {
        "weinstein_stage_2_or_2a": stage in {"2", "2A"},
        "avg_value_20d_gt_20m_usd": _value_at_least(_avg_trading_value(row, 20), 20_000_000 * usd_krw),
        "common_equity_type": _equity_type_pass(row),
        "as_1m_gt_85_or_as_3m_gt_85": _value_at_least(as_rank.get("as_1m"), 85) or _value_at_least(as_rank.get("as_3m"), 85),
        "top_industry_or_as_1m_gt_90": (
            (_f(industry_rank.get("industry_rank_3m")) is not None and industry_rank["industry_rank_3m"] < 25)
            or (_f(industry_rank.get("industry_rank_6m")) is not None and industry_rank["industry_rank_6m"] < 25)
            or _value_at_least(as_rank.get("as_1m"), 90)
        ),
    }
    return PresetResult("stage_analysis_leaders", all(predicates.values()), predicates)


def _canslim_pass(row: dict[str, Any], fundamentals: dict[str, Any], as_rank: dict[str, float], usd_krw: float) -> PresetResult:
    close = _close(row)
    predicates = {
        "eps_growth_latest_qtr_gt_25pct": _value_at_least(fundamentals.get("eps_growth_latest_qtr_pct"), 25),
        "avg_eps_growth_last_3yrs_gt_25pct": _value_at_least(fundamentals.get("avg_eps_growth_last_3yrs_pct"), 25),
        "sales_growth_latest_qtr_gt_25pct": _value_at_least(fundamentals.get("sales_growth_latest_qtr_pct"), 25),
        "rs_6m_gt_80": _value_at_least(as_rank.get("as_6m"), 80),
        "within_15pct_of_52wk_high": _within_pct_of_high(close, _f(row.get("high_52w")), 15),
        "avg_volume_50d_gt_100k": _value_at_least(_avg_volume(row, 50), 100_000),
        "last_gt_10_usd": _value_at_least(close, 10 * usd_krw),
    }
    return PresetResult("canslim_growth", all(predicates.values()), predicates)


def _minervini_pass(row: dict[str, Any], as_rank: dict[str, float], universe_closes: list[float], usd_krw: float) -> PresetResult:
    closes = _series(row, universe_closes)
    close = _close(row)
    ma50 = _ma(row, 50) or _sma(closes, 50)
    ma150 = _ma(row, 150) or _sma(closes, 150)
    ma200 = _ma(row, 200) or _sma(closes, 200)
    ma30w = _f(row.get("ma30w")) or _sma(closes, 150)
    ma40w = _f(row.get("ma40w")) or _sma(closes, 200)
    ma200_offsets = {m: _sma(closes, 200, 21 * m) for m in range(1, 6)}
    predicates = {
        "50d_gt_150d": ma50 is not None and ma150 is not None and ma50 > ma150,
        "50d_gt_200d": ma50 is not None and ma200 is not None and ma50 > ma200,
        "150d_gt_200d": ma150 is not None and ma200 is not None and ma150 > ma200,
        "200d_gt_200d_5mo_ago": ma200 is not None and ma200_offsets[5] is not None and ma200 > ma200_offsets[5],
        "within_25pct_of_52wk_high": _within_pct_of_high(close, _f(row.get("high_52w")), 25),
        "rs_12m_gt_69": _value_at_least(as_rank.get("as_12m"), 69),
        "200d_gt_each_1_to_4mo_ago": all(ma200 is not None and ma200_offsets[m] is not None and ma200 > ma200_offsets[m] for m in range(1, 5)),
        "common_equity_type": _equity_type_pass(row),
        "more_than_30pct_above_52wk_low": _above_pct_from_low(close, _f(row.get("low_52w")), 30),
        "200d_monthly_slope_positive_1_to_5mo": all(
            ma200_offsets[m] is not None and ma200_offsets[m + 1] is not None and ma200_offsets[m] > ma200_offsets[m + 1]
            for m in range(1, 5)
        ),
        "price_above_50d_150d_200d_30w_40w": all(close is not None and avg is not None and close > avg for avg in (ma50, ma150, ma200, ma30w, ma40w)),
    }
    return PresetResult("minervini_trend_template", all(predicates.values()), predicates)


def _deepvue_leaders_pass(row: dict[str, Any], fundamentals: dict[str, Any], as_rank: dict[str, float], universe_closes: list[float], usd_krw: float) -> PresetResult:
    close = _close(row)
    ma200 = _ma(row, 200) or _sma(_series(row, universe_closes), 200)
    ma200_1mo = _sma(_series(row, universe_closes), 200, 21)
    group1 = {
        "avg_value_20d_gt_20m_usd": _value_at_least(_avg_trading_value(row, 20), 20_000_000 * usd_krw),
        "adr_10d_gt_2pct": _value_at_least(_adr_pct(row, 10), 2),
        "common_equity_type": _equity_type_pass(row),
        "last_gt_12_5_usd": _value_at_least(close, 12.5 * usd_krw),
        "adr_1d_gt_1pct": _value_at_least(_adr_pct(row, 1), 1),
    }
    predicates = {
        **{f"g1_{k}": v for k, v in group1.items()},
        "g2_as_1m_gt_85_or_as_3m_gt_85_or_as_1w_gt_90": _value_at_least(as_rank.get("as_1m"), 85) or _value_at_least(as_rank.get("as_3m"), 85) or _value_at_least(as_rank.get("as_1w"), 90),
        "g3_growth_or_strong_as": any((
            _value_at_least(fundamentals.get("eps_growth_latest_qtr_pct"), 20),
            _value_at_least(fundamentals.get("eps_growth_next_qtr_pct"), 20),
            _value_at_least(fundamentals.get("eps_surprise_latest_qtr_pct"), 40),
            _value_at_least(fundamentals.get("sales_growth_latest_qtr_pct"), 20),
            _value_at_least(fundamentals.get("sales_growth_next_qtr_pct"), 20),
            _value_at_least(as_rank.get("as_1m"), 90),
            _value_at_least(as_rank.get("as_3m"), 95),
            _value_at_least(as_rank.get("as_1w"), 95),
        )),
        "g4_sales_year_gt_100m_usd_or_qtr_gt_25m_usd": _value_at_least(fundamentals.get("sales_latest_rptd_year_krw"), 100_000_000 * usd_krw) or _value_at_least(fundamentals.get("sales_latest_rptd_qtr_krw"), 25_000_000 * usd_krw),
        "g5_recent_ipo_uptrend_or_elite_as": ((ma200 is not None and ma200_1mo is not None and ma200 > ma200_1mo and _ipo_after(row, fundamentals, "2023-07-01")) or _value_at_least(as_rank.get("as_1m"), 95) or _value_at_least(as_rank.get("as_1w"), 96)),
    }
    return PresetResult("deepvue_leaders", all(predicates.values()), predicates)


def evaluate_deepvue_presets(
    *,
    kiwoom_rows: Iterable[dict[str, Any]],
    dart_rows: Iterable[dict[str, Any]],
    universe: dict[str, list[float]],
    ticker_to_industry: dict[str, str] | None = None,
    usd_krw: float = DEFAULT_USD_KRW,
) -> dict[str, Any]:
    """Evaluate all screenshot presets and return candidate-generation results."""
    fundamentals_by_ticker = {r["ticker"]: r for r in dart_rows}
    as_ranks = compute_absolute_strength_ranks(universe)
    industry_ranks = compute_industry_ranks(universe, ticker_to_industry or {})

    results = []
    for row in kiwoom_rows:
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        fundamentals = fundamentals_by_ticker.get(ticker, {})
        as_rank = as_ranks.get(ticker, {})
        industry_rank = industry_ranks.get(ticker, {})
        closes = universe.get(ticker, [])
        preset_results = [
            _stage_analysis_pass(row, as_rank, industry_rank, usd_krw),
            _canslim_pass(row, fundamentals, as_rank, usd_krw),
            _minervini_pass(row, as_rank, closes, usd_krw),
            _deepvue_leaders_pass(row, fundamentals, as_rank, closes, usd_krw),
        ]
        passed_presets = [preset.name for preset in preset_results if preset.passed]
        preset_results_by_name = {
            preset.name: {"passed": preset.passed, "predicates": preset.predicates}
            for preset in preset_results
        }
        passed_predicate_tags = sorted(
            f"{preset.name}:{predicate}"
            for preset in preset_results
            for predicate, passed in preset.predicates.items()
            if passed
        )
        filter_tags = [f"preset:{name}" for name in passed_presets]
        results.append({
            "ticker": ticker,
            "name": row.get("name") or ticker,
            "in_union_universe": bool(passed_presets),
            "passed_presets": passed_presets,
            "filter_tags": filter_tags,
            "passed_predicate_tags": passed_predicate_tags,
            "preset_results": preset_results_by_name,
            "as_ranks": as_rank,
            "industry_ranks": industry_rank,
        })

    universe_rows = [
        {
            "ticker": row["ticker"],
            "name": row["name"],
            "passed_presets": row["passed_presets"],
            "filter_tags": row["filter_tags"],
            "passed_predicate_tags": row["passed_predicate_tags"],
            "as_ranks": row["as_ranks"],
            "industry_ranks": row["industry_ranks"],
        }
        for row in results
        if row["in_union_universe"]
    ]

    summary = {name: 0 for name in PRESET_NAMES}
    for row in universe_rows:
        for name in row["passed_presets"]:
            summary[name] += 1
    summary["union_universe"] = len(universe_rows)
    return {
        "screening_only": True,
        "candidate_generation_only": True,
        "market": "KR",
        "usd_krw": usd_krw,
        "summary": summary,
        "universe": universe_rows,
        "results": results,
        "signal_safety": dict(SIGNAL_SAFETY_BLOCK),
    }
