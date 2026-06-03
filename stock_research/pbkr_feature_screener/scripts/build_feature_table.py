"""
build_feature_table.py — PBKR Quant Feature Screener v1

Merge per-domain feature shards into a wide feature table keyed by
(ticker, asof_date). Optional CSV reader for the synthetic fixture.

Research-only; does NOT emit trade signals.
"""

from __future__ import annotations

import csv
from typing import Dict, Iterable, List, Optional, Tuple


SCHEMA_VERSION = "feature_table_v1"

# Columns interpreted as numeric when reading CSV fixtures.
NUMERIC_COLUMNS = {
    "close",
    "ema20",
    "ema50",
    "ema150",
    "close_vs_ema20_pct",
    "close_vs_ema50_pct",
    "rs_20d",
    "rs_60d",
    "rs_120d",
    "rs_252d",
    "rs_60d_percentile",
    "sector_rs_20d",
    "sector_rs_60d",
    "ibdrs_approx",
    "weekly_return_13w",
    "weekly_ma10",
    "weekly_ma30",
    "weekly_ma10_slope",
    "latest_sales",
    "latest_op",
    "latest_eps",
    "op_revision_pct",
    "eps_revision_pct",
    "latest_op_surprise_pct",
    "sales_guidance_delta",
    "op_guidance_delta",
    "institution_flow_score",
    "private_fund_flow_strength",
    "stop_distance_pct",
}
INTEGER_COLUMNS = {
    "financial_investment_consecutive_days",
}
BOOLEAN_COLUMNS = {
    "official_risk_hard_exclude",
}


def _parse_value(col: str, raw: str):
    if raw is None or raw == "":
        if col in BOOLEAN_COLUMNS:
            return False
        return None
    if col in BOOLEAN_COLUMNS:
        return raw.strip().lower() in {"1", "true", "t", "yes", "y"}
    if col in INTEGER_COLUMNS:
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None
    if col in NUMERIC_COLUMNS:
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    return raw


def read_feature_csv(path: str) -> List[dict]:
    rows: List[dict] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row = {k: _parse_value(k, v) for k, v in r.items()}
            row.setdefault("schema_version", SCHEMA_VERSION)
            row.setdefault("direct_trade_signal", False)
            row.setdefault("trade_signal", None)
            rows.append(row)
    return rows


def merge_shards(
    *shards: Iterable[dict],
    key: Tuple[str, str] = ("ticker", "asof_date"),
) -> List[dict]:
    out: Dict[Tuple, dict] = {}
    for shard in shards:
        for r in shard:
            k = tuple(r.get(c) for c in key)
            if k not in out:
                out[k] = {}
            for col, val in r.items():
                if val is None and col in out[k] and out[k][col] is not None:
                    continue
                out[k][col] = val
    merged = list(out.values())
    for r in merged:
        r.setdefault("schema_version", SCHEMA_VERSION)
        r.setdefault("direct_trade_signal", False)
        r.setdefault("trade_signal", None)
        r.setdefault("official_risk_hard_exclude", False)
    return merged


def attach_rs_percentile(
    rows: List[dict], src_col: str = "rs_60d", dst_col: str = "rs_60d_percentile"
) -> List[dict]:
    pool: List[Optional[float]] = [r.get(src_col) for r in rows]
    valid = sorted(v for v in pool if v is not None)
    if not valid:
        for r in rows:
            r[dst_col] = None
        return rows
    n = len(valid)
    for r in rows:
        v = r.get(src_col)
        if v is None:
            r[dst_col] = None
            continue
        rank = sum(1 for x in valid if x <= v)
        r[dst_col] = 100.0 * rank / n
    return rows


if __name__ == "__main__":
    raise SystemExit(
        "build_feature_table is a library; run examples/run_feature_screener_fixture.py instead."
    )
