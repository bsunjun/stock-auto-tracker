"""CLI for the PBKR v4 Screening Builder.

Defaults route outputs to ``$PBKR_SCREENING_OUT`` or
``/tmp/pbkr_v4_screening_out`` to keep raw real data out of the repo.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .builder import build_screening_run
from .constants import DEFAULT_MIN_TRADING_VALUE, DEFAULT_RS_THRESHOLD, DEFAULT_RS_WEIGHTS
from .validator import verify_run_directory


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="pbkr_v4_screening_builder",
        description="PBKR v4 Screening Builder — candidate generation only.",
    )
    p.add_argument("--tradingview", required=True, help="TradingView MCP scan JSON path")
    p.add_argument("--kiwoom-features", required=True, help="Kiwoom daily-feature JSON path")
    p.add_argument("--kiwoom-universe", required=True, help="Kiwoom universe close-series JSON path")
    p.add_argument("--official-risk", required=True, help="KRX/KIND/DART risk-flags JSON path")
    p.add_argument("--asof", required=True, help="As-of trading date, YYYY-MM-DD")
    default_out = os.getenv("PBKR_SCREENING_OUT") or "/tmp/pbkr_v4_screening_out"
    p.add_argument("--out-dir", default=default_out, help="Local/private output directory (NOT in repo)")
    p.add_argument("--rs-threshold", type=float, default=DEFAULT_RS_THRESHOLD)
    p.add_argument("--min-trading-value", type=float, default=DEFAULT_MIN_TRADING_VALUE)
    p.add_argument("--rs-weight-m1",  type=float, default=DEFAULT_RS_WEIGHTS["m1"])
    p.add_argument("--rs-weight-m3",  type=float, default=DEFAULT_RS_WEIGHTS["m3"])
    p.add_argument("--rs-weight-m6",  type=float, default=DEFAULT_RS_WEIGHTS["m6"])
    p.add_argument("--rs-weight-m12", type=float, default=DEFAULT_RS_WEIGHTS["m12"])
    p.add_argument("--no-verify", action="store_true", help="Skip post-write verification")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    out_dir = Path(args.out_dir).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[2]
    try:
        out_dir.relative_to(repo_root)
        print(
            f"refusing to write outputs inside the repository: {out_dir}\n"
            "Set --out-dir to a local/private path (e.g., /tmp/pbkr_v4_screening_out).",
            file=sys.stderr,
        )
        return 2
    except ValueError:
        pass  # outside repo, good

    weights = {
        "m1": args.rs_weight_m1,
        "m3": args.rs_weight_m3,
        "m6": args.rs_weight_m6,
        "m12": args.rs_weight_m12,
    }
    total_w = sum(weights.values())
    if total_w <= 0:
        print("rs weights must sum to a positive number", file=sys.stderr)
        return 2

    manifest = build_screening_run(
        tradingview_path=args.tradingview,
        kiwoom_features_path=args.kiwoom_features,
        kiwoom_universe_path=args.kiwoom_universe,
        official_risk_path=args.official_risk,
        asof_date=args.asof,
        out_dir=out_dir,
        rs_threshold=args.rs_threshold,
        min_trading_value=args.min_trading_value,
        rs_weights=weights,
    )

    print(f"[builder] wrote run dir: {manifest['out_dir']}")
    for key, path in manifest["files"].items():
        print(f"  - {key}: {path}")

    print("\n[builder] counts:")
    print(json.dumps(manifest["counts"], indent=2, ensure_ascii=False))
    print("\n[builder] PBKR_RS_RANK summary:")
    print(json.dumps(manifest["rs_summary"], indent=2, ensure_ascii=False))

    if args.no_verify:
        return 0

    print("\n[verify] run directory invariants:")
    report = verify_run_directory(manifest["out_dir"])
    keys = (
        "direct_trade_signal_true_count",
        "trade_signal_true_count",
        "automatic_execution_allowed_true_count",
        "trade_ticket_generation_allowed_true_count",
        "operator_decision_execute_count",
        "pb_trigger_count",
        "pb_ready_count",
        "pb_scout_count",
        "trade_ticket_count",
        "order_intent_count",
        "order_preparation_count",
        "execution_artifact_count",
        "automatic_alert_count",
        "automatic_execution_hook_count",
        "trade_ticket_file_count",
    )
    for k in keys:
        print(f"  {k}: {report[k]}")
    print(f"  pass: {report['pass']}")
    if report["errors"]:
        for e in report["errors"]:
            print(f"  error: {e}", file=sys.stderr)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
