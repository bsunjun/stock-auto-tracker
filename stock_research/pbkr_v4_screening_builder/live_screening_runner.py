"""Read-only live screening runner.

This runner targets *real* live inputs (TradingView MCP scan, Kiwoom
REST features, Kiwoom daily-OHLCV universe, KRX/KIND/DART
designation feed) and produces a `DAILY_INPUT_PACKET` for the GPT
Orchestrator.

**It is read-only.** It never authorizes a broker order, never
generates a trade ticket, never produces an `order_intent` /
`order_preparation` / `execution_artifact` / `automatic_alert` /
`automatic_execution_hook`, and never emits `PB_READY`, `PB_SCOUT`,
or `PB_TRIGGER`. Screening is candidate generation only.

Hard rules enforced here (in addition to the screening builder's
existing invariants):

1. ``--no-execution`` is **required**. Without it the runner refuses
   to start. There is no mode that authorizes execution; the flag is
   a forcing function so the operator types the disclaimer every
   time.
2. The output directory must be **outside the repository**. If the
   resolved path is inside the repo the runner exits 2 before any
   file is written.
3. Every input source must be an existing, non-empty file. **The
   runner never silently substitutes a synthetic / mock input on
   network or source failure.** Missing or empty inputs raise a
   ``LiveInputError`` and the runner exits 2.
4. After the build, a ``verification_report.json`` is written
   alongside the four screening outputs. The report records every
   doctrinal counter (``pb_trigger_count``, ``trade_ticket_count``,
   ``order_intent_count``, …) and asserts ``pass: true``. If any
   counter is non-zero the runner exits 1.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .builder import build_screening_run
from .constants import (
    DAILY_PACKET_SIGNAL_SAFETY,
    DEFAULT_MIN_TRADING_VALUE,
    DEFAULT_RS_THRESHOLD,
    DEFAULT_RS_WEIGHTS,
    SCHEMA_VERSION,
)
from .validator import verify_run_directory


DEFAULT_OUTPUT_BASE = (
    os.getenv("PBKR_LIVE_SCREENING_OUT_BASE")
    or "/Users/bsunjun/trading/phase3/output/pbkr_screening"
)


class LiveScreeningError(Exception):
    """Base class for live-screening runner errors."""


class LiveInputError(LiveScreeningError):
    """A required live input source is missing, empty, or unreadable."""


class OutputPathInRepoError(LiveScreeningError):
    """The requested output directory is inside the repository."""


class NoExecutionFlagRequiredError(LiveScreeningError):
    """The --no-execution flag was not supplied."""


class SafetyVerificationFailed(LiveScreeningError):
    """The post-write verifier reported at least one non-zero counter."""


def _resolve_output_dir(date: str, output_dir: str | None) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    base = Path(DEFAULT_OUTPUT_BASE).expanduser()
    return (base / date.replace("-", "")).resolve()


def _assert_outside_repo(path: Path, repo_root: Path) -> None:
    try:
        path.resolve().relative_to(repo_root)
    except ValueError:
        return  # outside repo — good
    raise OutputPathInRepoError(
        f"refusing to write live-screening outputs inside the repository: {path}\n"
        f"set --output-dir (or $PBKR_LIVE_SCREENING_OUT_BASE) to a local/private path "
        f"such as {DEFAULT_OUTPUT_BASE}/<YYYYMMDD>"
    )


def _stat_input(path: Path) -> dict[str, Any]:
    """Probe a real input source. Refuse to silently fall back to synthetic.

    Records: existence, size, mtime, sha256 of the first 1 MiB
    (enough to fingerprint typical screening inputs without reading
    the whole file twice). Empty files are rejected.
    """
    if not path.exists():
        raise LiveInputError(
            f"live-screening input not found: {path}\n"
            "the runner refuses to substitute a synthetic / mock input on missing source."
        )
    if not path.is_file():
        raise LiveInputError(f"live-screening input is not a regular file: {path}")
    st = path.stat()
    if st.st_size == 0:
        raise LiveInputError(
            f"live-screening input is empty: {path}\n"
            "the runner refuses to substitute a synthetic / mock input on empty source."
        )
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(1024 * 1024))
    return {
        "path": str(path),
        "size_bytes": int(st.st_size),
        "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "sha256_first_mib": h.hexdigest(),
        "exists": True,
    }


def _build_verification_report(
    asof_date: str,
    inputs: dict[str, dict[str, Any]],
    output_dir: Path,
    output_files: list[str],
    verifier_report: dict[str, Any],
    rs_summary: dict[str, Any],
    counts: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the verification_report.json payload."""
    counter_keys = (
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
    counters = {k: int(verifier_report.get(k, 0)) for k in counter_keys}

    return {
        "schema_version": SCHEMA_VERSION,
        "runner": "live_screening_runner",
        "asof_date": asof_date,
        "no_execution": True,
        "broker_order_path_present": False,
        "auto_execution_allowed": False,
        "input_sources": inputs,
        "output_dir": str(output_dir),
        "output_files": sorted(output_files),
        "doctrinal_counters": counters,
        "screening_candidates_counts": counts,
        "pbkr_rs_rank_summary": rs_summary,
        "pass": bool(verifier_report.get("pass", False)),
        "signal_safety": dict(DAILY_PACKET_SIGNAL_SAFETY),
    }


def run_live_screen(
    *,
    date: str,
    tradingview: str,
    kiwoom_features: str,
    kiwoom_universe: str,
    official_risk: str,
    output_dir: str | None,
    no_execution: bool,
    repo_root: Path,
    rs_threshold: float = DEFAULT_RS_THRESHOLD,
    min_trading_value: float = DEFAULT_MIN_TRADING_VALUE,
    rs_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run the read-only live screening pipeline.

    Returns the merged manifest (build manifest + verification report).
    Raises a LiveScreeningError subclass on any precondition failure.
    """
    if not no_execution:
        raise NoExecutionFlagRequiredError(
            "live-screen requires --no-execution.\n"
            "this runner is read-only, never authorizes broker orders, "
            "and never produces trade tickets / order intents / automatic execution hooks. "
            "re-invoke with --no-execution to acknowledge."
        )

    resolved_output = _resolve_output_dir(date, output_dir)
    _assert_outside_repo(resolved_output, repo_root)

    inputs = {
        "tradingview":      _stat_input(Path(tradingview).expanduser()),
        "kiwoom_features":  _stat_input(Path(kiwoom_features).expanduser()),
        "kiwoom_universe":  _stat_input(Path(kiwoom_universe).expanduser()),
        "official_risk":    _stat_input(Path(official_risk).expanduser()),
    }

    # Build subdirectory: write_outputs creates <output_dir>/<YYYY-MM-DD>/.
    # The user-facing default already encodes the date in YYYYMMDD form,
    # so we point write_outputs at the *parent* of the requested dir.
    # That keeps a single tree on disk:
    #     <DEFAULT_OUTPUT_BASE>/<YYYYMMDD>/<YYYY-MM-DD>/
    # ...is verbose. Simpler: pass --output-dir directly and tell the
    # builder to write into <output-dir>/<asof-date>. We honour that.
    out_parent = resolved_output

    manifest = build_screening_run(
        tradingview_path=Path(tradingview).expanduser(),
        kiwoom_features_path=Path(kiwoom_features).expanduser(),
        kiwoom_universe_path=Path(kiwoom_universe).expanduser(),
        official_risk_path=Path(official_risk).expanduser(),
        asof_date=date,
        out_dir=out_parent,
        rs_threshold=rs_threshold,
        min_trading_value=min_trading_value,
        rs_weights=rs_weights or DEFAULT_RS_WEIGHTS,
    )

    run_dir = Path(manifest["out_dir"])
    verifier_report = verify_run_directory(run_dir)
    output_files = [str(Path(p).relative_to(run_dir)) for p in manifest["files"].values()]

    report = _build_verification_report(
        asof_date=date,
        inputs=inputs,
        output_dir=run_dir,
        output_files=output_files,
        verifier_report=verifier_report,
        rs_summary=manifest["rs_summary"],
        counts=manifest["counts"],
    )

    report_path = run_dir / "verification_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest["verification_report"] = str(report_path)

    if not report["pass"]:
        raise SafetyVerificationFailed(
            f"live-screen post-write verification failed at {run_dir}.\n"
            f"counters: {report['doctrinal_counters']}"
        )
    return manifest


def cli_main(args: Any, repo_root: Path) -> int:
    """Argparse entry point. Translates exceptions into exit codes."""
    try:
        manifest = run_live_screen(
            date=args.date,
            tradingview=args.tradingview,
            kiwoom_features=args.kiwoom_features,
            kiwoom_universe=args.kiwoom_universe,
            official_risk=args.official_risk,
            output_dir=args.output_dir,
            no_execution=args.no_execution,
            repo_root=repo_root,
            rs_threshold=args.rs_threshold,
            min_trading_value=args.min_trading_value,
            rs_weights={
                "m1": args.rs_weight_m1,
                "m3": args.rs_weight_m3,
                "m6": args.rs_weight_m6,
                "m12": args.rs_weight_m12,
            },
        )
    except (NoExecutionFlagRequiredError, OutputPathInRepoError, LiveInputError) as e:
        print(f"[live-screen] {e}", file=sys.stderr)
        return 2
    except SafetyVerificationFailed as e:
        print(f"[live-screen] {e}", file=sys.stderr)
        return 1

    print(f"[live-screen] wrote run dir: {manifest['out_dir']}")
    for key, path in manifest["files"].items():
        print(f"  - {key}: {path}")
    print(f"  - verification_report: {manifest['verification_report']}")
    print("\n[live-screen] counts:")
    print(json.dumps(manifest["counts"], indent=2, ensure_ascii=False))
    print("[live-screen] pass: True (verification_report asserts no execution path)")
    return 0
