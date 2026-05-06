"""CLI for the PBKR v4 Screening Builder.

Three subcommands:

    screen          — run the screening pipeline against any inputs
                      (offline / fixture / dev).  Output may live under
                      $PBKR_SCREENING_OUT or /tmp/pbkr_v4_screening_out
                      by default; the CLI refuses any --out-dir inside
                      the repository.

    live-screen     — run the screening pipeline against *real* live
                      inputs.  This subcommand is read-only:
                        * --no-execution is required;
                        * inputs must exist and be non-empty (no
                          silent synthetic fallback);
                        * output must live outside the repository;
                        * a verification_report.json is emitted that
                          asserts every doctrinal counter is zero.

    kiwoom-collect  — read-only Kiwoom REST today-universe collector.
                      Produces ``kiwoom_features_latest.json`` and
                      ``kiwoom_universe_latest.json`` (plus an audit
                      report) under $PBKR_PROCESSED_ROOT/live_screen_inputs.
                      Order / account endpoints are out of scope.

For backward compatibility, when invoked with no subcommand the CLI
defaults to ``screen``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .builder import build_screening_run
from .constants import DEFAULT_MIN_TRADING_VALUE, DEFAULT_RS_THRESHOLD, DEFAULT_RS_WEIGHTS
from .kiwoom_today_universe_collector import (
    DEFAULT_OUTPUT_BASE as COLLECTOR_DEFAULT_OUTPUT_BASE,
    LIVE_SCREEN_INPUTS_SUBDIR,
    cli_main as collector_cli_main,
)
from .live_screening_runner import (
    DEFAULT_OUTPUT_BASE,
    cli_main as live_cli_main,
)
from .validator import verify_run_directory


_SUBCOMMANDS = ("screen", "live-screen", "kiwoom-collect")


def _add_rs_weight_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--rs-threshold", type=float, default=DEFAULT_RS_THRESHOLD)
    p.add_argument("--min-trading-value", type=float, default=DEFAULT_MIN_TRADING_VALUE)
    p.add_argument("--rs-weight-m1",  type=float, default=DEFAULT_RS_WEIGHTS["m1"])
    p.add_argument("--rs-weight-m3",  type=float, default=DEFAULT_RS_WEIGHTS["m3"])
    p.add_argument("--rs-weight-m6",  type=float, default=DEFAULT_RS_WEIGHTS["m6"])
    p.add_argument("--rs-weight-m12", type=float, default=DEFAULT_RS_WEIGHTS["m12"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pbkr_v4_screening_builder",
        description="PBKR v4 Screening Builder — candidate generation only.",
    )
    sub = parser.add_subparsers(
        dest="command", required=True,
        metavar="{screen,live-screen,kiwoom-collect}",
    )

    p_screen = sub.add_parser(
        "screen",
        help="Run the screening pipeline (offline / fixture / dev).",
    )
    p_screen.add_argument("--tradingview", required=True, help="TradingView MCP scan JSON path")
    p_screen.add_argument("--kiwoom-features", required=True, help="Kiwoom daily-feature JSON path")
    p_screen.add_argument("--kiwoom-universe", required=True, help="Kiwoom universe close-series JSON path")
    p_screen.add_argument("--official-risk", required=True, help="KRX/KIND/DART risk-flags JSON path")
    p_screen.add_argument("--asof", required=True, help="As-of trading date, YYYY-MM-DD")
    default_out = os.getenv("PBKR_SCREENING_OUT") or "/tmp/pbkr_v4_screening_out"
    p_screen.add_argument("--out-dir", default=default_out, help="Local/private output directory (NOT in repo)")
    _add_rs_weight_flags(p_screen)
    p_screen.add_argument("--no-verify", action="store_true", help="Skip post-write verification")

    p_live = sub.add_parser(
        "live-screen",
        help="Run the screening pipeline against real live inputs (read-only).",
    )
    p_live.add_argument("--date", required=True, help="As-of trading date, YYYY-MM-DD")
    p_live.add_argument("--tradingview", required=True, help="TradingView MCP scan JSON path (real)")
    p_live.add_argument("--kiwoom-features", required=True, help="Kiwoom daily-feature JSON path (real)")
    p_live.add_argument("--kiwoom-universe", required=True, help="Kiwoom universe close-series JSON path (real)")
    p_live.add_argument("--official-risk", required=True, help="KRX/KIND/DART risk-flags JSON path (real)")
    p_live.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Local/private output directory. MUST live outside the repository. "
            f"Default: {DEFAULT_OUTPUT_BASE}/<YYYYMMDD>"
        ),
    )
    p_live.add_argument(
        "--no-execution",
        action="store_true",
        default=False,
        help=(
            "Required acknowledgement: this runner is read-only and never authorizes "
            "broker orders, automatic execution, or trade tickets."
        ),
    )
    _add_rs_weight_flags(p_live)

    p_collect = sub.add_parser(
        "kiwoom-collect",
        help="Read-only Kiwoom REST today-universe collector for live-screen inputs.",
    )
    p_collect.add_argument("--date", required=True, help="As-of trading date, YYYY-MM-DD")
    p_collect.add_argument(
        "--config",
        default=None,
        help=(
            "Local Kiwoom REST config JSON path (must live outside the repo). "
            "Falls back to $KIWOOM_REST_CONFIG when omitted."
        ),
    )
    default_collect_out = (
        f"{COLLECTOR_DEFAULT_OUTPUT_BASE}/{LIVE_SCREEN_INPUTS_SUBDIR}"
    )
    p_collect.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Local/private output directory for live_screen_inputs. MUST live "
            f"outside the repository.  Default: {default_collect_out}"
        ),
    )
    p_collect.add_argument(
        "--no-execution",
        action="store_true",
        default=False,
        help=(
            "Required acknowledgement: this subcommand is read-only and never "
            "authorizes broker orders, automatic execution, or trade tickets."
        ),
    )
    p_collect.add_argument(
        "--max-tickers",
        type=int,
        default=None,
        help=(
            "Smoke-mode cap: truncate the kept universe to the first N tickers. "
            "Default: collect the full universe.  Recorded as `max_tickers` and "
            "`truncated_universe` in the collection report."
        ),
    )
    p_collect.add_argument(
        "--tickers-file",
        default=None,
        help=(
            "Optional private file (one ticker per line; '#' comments OK) that "
            "restricts the universe to the listed tickers.  MUST live outside "
            "the repository."
        ),
    )

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    """Insert a default ``screen`` subcommand for backward compatibility.

    If the first non-flag token is not a known subcommand and the
    user did not ask for help, prepend ``screen`` so legacy
    invocations (``--tradingview ... --asof ...``) keep working.
    """
    if not argv:
        return argv
    first = argv[0]
    if first in _SUBCOMMANDS:
        return argv
    if first in ("-h", "--help"):
        return argv
    return ["screen", *argv]


def parse_args(argv: list[str]) -> argparse.Namespace:
    return build_parser().parse_args(_normalize_argv(argv))


def _screen_main(args: argparse.Namespace, repo_root: Path) -> int:
    out_dir = Path(args.out_dir).expanduser().resolve()
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
    if sum(weights.values()) <= 0:
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = Path(__file__).resolve().parents[2]

    if args.command == "screen":
        return _screen_main(args, repo_root)
    if args.command == "live-screen":
        return live_cli_main(args, repo_root)
    if args.command == "kiwoom-collect":
        return collector_cli_main(args, repo_root)
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
