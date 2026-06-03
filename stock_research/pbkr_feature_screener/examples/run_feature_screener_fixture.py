"""
run_feature_screener_fixture.py — PBKR Quant Feature Screener v1

End-to-end synthetic-fixture runner. Reads the synthetic feature table,
runs screen_candidates, runs backtest_filter_ic, and validates the
emitted packs against their JSON schemas (lightweight in-process check).

This script:
  * does NOT write any output to disk
  * does NOT contact any network resource
  * does NOT touch Drive
  * does NOT promote anything to latest / SuperPack / rolling
  * does NOT emit trade signals

Usage:
    python examples/run_feature_screener_fixture.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Tuple


HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
SCRIPTS_DIR = os.path.join(PKG_ROOT, "scripts")
SCHEMAS_DIR = os.path.join(PKG_ROOT, "schemas")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import build_feature_table  # noqa: E402
import screen_candidates  # noqa: E402
import backtest_filter_ic  # noqa: E402


SYNTHETIC_FWD_RETURNS: Dict[Tuple[str, str], Dict[str, float]] = {
    ("SYN_001", "2026-04-30"): {"fwd_5d": 2.0, "fwd_20d": 8.0, "fwd_60d": 15.0},
    ("SYN_002", "2026-04-30"): {"fwd_5d": 1.0, "fwd_20d": 5.0, "fwd_60d": 10.0},
    ("SYN_003", "2026-04-30"): {"fwd_5d": 0.5, "fwd_20d": 3.0, "fwd_60d": 7.0},
    ("SYN_004", "2026-04-30"): {"fwd_5d": -3.0, "fwd_20d": -10.0, "fwd_60d": -20.0},
    ("SYN_005", "2026-04-30"): {"fwd_5d": 1.5, "fwd_20d": 6.0, "fwd_60d": 12.0},
    ("SYN_006", "2026-04-30"): {"fwd_5d": -0.5, "fwd_20d": -2.0, "fwd_60d": -5.0},
    ("SYN_007", "2026-04-30"): {"fwd_5d": 3.0, "fwd_20d": 10.0, "fwd_60d": 20.0},
    ("SYN_008", "2026-04-30"): {"fwd_5d": -1.0, "fwd_20d": -5.0, "fwd_60d": -10.0},
}


def _validate_required(obj: Dict[str, Any], required: List[str], where: str) -> List[str]:
    issues: List[str] = []
    for k in required:
        if k not in obj:
            issues.append(f"{where}: missing required key {k!r}")
    return issues


def _validate_screened_pack(pack: Dict[str, Any]) -> List[str]:
    schema_path = os.path.join(SCHEMAS_DIR, "screened_candidate_pack.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    issues: List[str] = []
    issues += _validate_required(pack, schema["required"], "pack")
    if pack.get("schema_version") != "screened_candidate_pack_v1":
        issues.append("pack: schema_version mismatch")
    if pack.get("direct_trade_signal") is not False:
        issues.append("pack: direct_trade_signal must be false")
    if pack.get("trade_signal") is not None:
        issues.append("pack: trade_signal must be null")
    for i, c in enumerate(pack.get("candidates", [])):
        for k in ("ticker", "pass_count", "screen_score", "passed_filters", "features"):
            if k not in c:
                issues.append(f"pack.candidates[{i}]: missing {k!r}")
        if c.get("human_review_required") is not True:
            issues.append(f"pack.candidates[{i}]: human_review_required must be true")
    return issues


def _validate_filter_perf(pack: Dict[str, Any]) -> List[str]:
    schema_path = os.path.join(SCHEMAS_DIR, "filter_performance_pack.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    issues: List[str] = []
    issues += _validate_required(pack, schema["required"], "perf")
    if pack.get("schema_version") != "filter_performance_pack_v1":
        issues.append("perf: schema_version mismatch")
    if pack.get("direct_trade_signal") is not False:
        issues.append("perf: direct_trade_signal must be false")
    if pack.get("trade_signal") is not None:
        issues.append("perf: trade_signal must be null")
    for i, f in enumerate(pack.get("filters", [])):
        for k in ("filter_id", "n_obs", "ic"):
            if k not in f:
                issues.append(f"perf.filters[{i}]: missing {k!r}")
    return issues


def _count_forbidden(obj: Any) -> Dict[str, int]:
    direct_count = 0
    truthy_count = 0

    def walk(x: Any) -> None:
        nonlocal direct_count, truthy_count
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "direct_trade_signal" and v is True:
                    direct_count += 1
                if k == "trade_signal" and bool(v):
                    truthy_count += 1
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return {"direct_trade_signal_true": direct_count, "trade_signal_truthy": truthy_count}


def main() -> int:
    csv_path = os.path.join(HERE, "synthetic_feature_table.csv")
    rows = build_feature_table.read_feature_csv(csv_path)
    rows = build_feature_table.merge_shards(rows)

    asof = rows[0]["asof_date"] if rows else "2026-04-30"

    screened = screen_candidates.screen(rows, asof_date=asof)
    perf = backtest_filter_ic.build_pack(
        asof_date=asof,
        feature_rows=rows,
        filters=screen_candidates.DEFAULT_FILTERS,
        fwd_returns=SYNTHETIC_FWD_RETURNS,
        horizons_days=(5, 20, 60),
        hit_rate_horizon_days=20,
    )

    issues: List[str] = []
    issues += _validate_screened_pack(screened)
    issues += _validate_filter_perf(perf)

    forbidden_screened = _count_forbidden(screened)
    forbidden_perf = _count_forbidden(perf)

    print("=== PBKR Quant Feature Screener — Synthetic Fixture ===")
    print(f"feature rows         : {len(rows)}")
    print(f"universe_size        : {screened['universe_size']}")
    print(f"hard_exclude_count   : {screened['hard_exclude_count']}")
    print(f"candidates           : {len(screened['candidates'])}")
    print(f"filter_perf entries  : {len(perf['filters'])}")
    print(f"forbidden(screened)  : {forbidden_screened}")
    print(f"forbidden(perf)      : {forbidden_perf}")

    expect_universe = 8
    expect_hard_excl = 2
    expect_candidates = 5

    if screened["universe_size"] != expect_universe:
        issues.append(f"universe_size {screened['universe_size']} != {expect_universe}")
    if screened["hard_exclude_count"] != expect_hard_excl:
        issues.append(f"hard_exclude_count {screened['hard_exclude_count']} != {expect_hard_excl}")
    if len(screened["candidates"]) != expect_candidates:
        issues.append(
            f"candidates {len(screened['candidates'])} != {expect_candidates}"
        )
    if forbidden_screened["direct_trade_signal_true"] != 0:
        issues.append("forbidden direct_trade_signal=true detected in screened pack")
    if forbidden_screened["trade_signal_truthy"] != 0:
        issues.append("forbidden trade_signal truthy detected in screened pack")
    if forbidden_perf["direct_trade_signal_true"] != 0:
        issues.append("forbidden direct_trade_signal=true detected in filter perf pack")
    if forbidden_perf["trade_signal_truthy"] != 0:
        issues.append("forbidden trade_signal truthy detected in filter perf pack")

    if issues:
        print("RESULT: FAIL")
        for it in issues:
            print(f"  - {it}")
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
