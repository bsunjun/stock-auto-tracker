#!/usr/bin/env python3
"""
Phase 3 — Estimate revision dry-run pipeline runner (PR #9).

Wires three already-existing scripts into a single dry-run-friendly command:

    merge_meta.py
      └─> build_report_estimate_v132.py --strict
            └─> rolling_append.py --strict-estimate  (dry-run only)

This runner is dry-run for rolling/promotion. It may create intermediate
JSON files only under --workdir.

What this runner explicitly DOES NOT do (forbidden apply):
  * rolling_append.py --apply  (the rolling step is always --dry-run)
  * promote_report_outputs.py --apply
  * `latest` updates
  * Super Pack rebuilds
  * Drive / repo / templates writes
  * OCR / Vision / API calls

What this runner DOES do internally (allowed internal apply, scoped to
--workdir only — never the repo, never Drive, never the real rolling CSV):
  * merge_meta.py --apply --out <workdir>/parsed_meta.merged.json
  * build_report_estimate_v132.py --strict --apply --output-root <workdir>

These internal `--apply` invocations exist solely to materialize the
intermediate JSON inputs the next stage needs to read. They never touch
anything outside <workdir>.

The runner's own `--apply` flag is accepted on the command line for clarity
of intent, but it is hard-refused with exit 2: PR #9 is a dry-run connector,
not a promotion tool.

Output
------
On success the runner writes `<workdir>/pipeline_summary.json` capturing
per-step status, accepted/rejected/duplicate counts, the executed commands,
and a forbidden-actions summary. The workdir is removed on exit unless
`--keep-workdir` is passed.

Usage
-----
    python3 stock_research/phase3_report_pipeline/scripts/run_estimate_revision_dryrun.py \\
      --date 2026-04-30 \\
      --bridge-meta stock_research/phase3_report_pipeline/examples/pipeline_runner_fixture/bridge_meta.json \\
      --structured  stock_research/phase3_report_pipeline/examples/pipeline_runner_fixture/structured_extraction.json \\
      --rolling-extra-rows stock_research/phase3_report_pipeline/examples/pipeline_runner_fixture/rolling_extra_rows.json \\
      --workdir /tmp/phase3_pr9 \\
      --print-commands
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# Resolve sibling scripts relative to this file so the runner works regardless
# of the user's CWD.
THIS_FILE = Path(__file__).resolve()
PHASE3_SCRIPTS_DIR = THIS_FILE.parent
REPO_ROOT = PHASE3_SCRIPTS_DIR.parent.parent.parent

MERGE_META_PY = PHASE3_SCRIPTS_DIR / "merge_meta.py"
BUILD_REPORT_PY = PHASE3_SCRIPTS_DIR / "build_report_estimate_v132.py"
ROLLING_APPEND_PY = REPO_ROOT / "stock_research" / "scripts" / "rolling_append.py"
DEFAULT_TEMPLATES_CSV = REPO_ROOT / "stock_research" / "templates" / "estimate_revision_history.csv"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--date", required=True, help="Target date YYYY-MM-DD")
    p.add_argument("--bridge-meta", required=True,
                   help="bridge parsed_meta.json (input to merge_meta)")
    p.add_argument("--structured", required=True,
                   help="structured_extraction.json (input to merge_meta)")
    p.add_argument("--workdir", default="/tmp/phase3_pr9",
                   help="Temporary workdir for merge/build/rolling artifacts. "
                        "Must be outside the repo. Default /tmp/phase3_pr9.")
    p.add_argument("--rolling-csv", default=str(DEFAULT_TEMPLATES_CSV),
                   help="Source CSV used as the rolling-step header/dedupe seed. "
                        "Default: stock_research/templates/estimate_revision_history.csv. "
                        "The runner copies it into the workdir and pre-seeds one "
                        "duplicate row; the original is never modified.")
    p.add_argument("--rolling-extra-rows", default=None,
                   help="Optional JSON file of extra rows merged into the rolling "
                        "step input for negative testing (hostile rows that the "
                        "rolling validator must reject). Default: none.")
    p.add_argument("--strict", dest="strict", action="store_true", default=True,
                   help="(default) Pass --strict to build_report_estimate.")
    p.add_argument("--no-strict", dest="strict", action="store_false",
                   help="Disable strict gate (NOT recommended; defeats the runner's purpose).")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) The only supported mode in PR #9.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Refused. PR #9 is a dry-run connector and never applies "
                        "to a real rolling CSV; passing --apply exits with code 2.")
    p.add_argument("--keep-workdir", action="store_true", default=False,
                   help="Do not delete the workdir on exit.")
    p.add_argument("--print-commands", action="store_true", default=False,
                   help="Echo each downstream subprocess command before running it.")
    p.add_argument("--fail-on-rejected", action="store_true", default=False,
                   help="Exit non-zero if any build-step or rolling-step rejection "
                        "is observed. Default false: rejections are reported but "
                        "do not fail the run.")
    return p.parse_args(argv)


def _is_under_repo_templates(p: Path) -> bool:
    try:
        parts = p.resolve(strict=False).parts
    except (OSError, RuntimeError):
        parts = p.parts
    for i in range(len(parts) - 1):
        if parts[i] == "stock_research" and parts[i + 1] == "templates":
            return True
    return False


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _run(cmd: List[str], *, label: str, print_commands: bool) -> subprocess.CompletedProcess:
    if print_commands:
        print(f"$ [{label}] " + " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


_ROLLING_LINE_PATTERNS = {
    "validated": re.compile(r"validated\s*=\s*(\d+)"),
    "rejected": re.compile(r"rejected\s*=\s*(\d+)"),
    "duplicate_skip": re.compile(r"skipped\(dup\)\s*=\s*(\d+)"),
    "to_add": re.compile(r"to_add\s*=\s*(\d+)"),
}


def parse_rolling_stdout(stdout: str) -> dict:
    """Pull validated/rejected/duplicate/to_add counts out of rolling_append.py
    stdout. We rely on the fixed-format log lines emitted in dry-run."""
    out: dict = {}
    for key, pattern in _ROLLING_LINE_PATTERNS.items():
        # Last match wins — rolling_append prints multiple lines and we want
        # the most recent (after-validation) numbers.
        matches = pattern.findall(stdout)
        if matches:
            out[key] = int(matches[-1])
    return out


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    # ---- input validation -------------------------------------------------
    if not DATE_RE.match(args.date):
        print(f"error: --date must be YYYY-MM-DD (got {args.date!r})", file=sys.stderr)
        return 2

    if not args.dry_run:
        # PR #9 is a dry-run connector. --apply is intentionally inert.
        print(
            "error: --apply is not supported in PR #9; this runner is a dry-run "
            "connector. Use the per-step scripts directly with explicit approval "
            "to perform any real append/promote.",
            file=sys.stderr,
        )
        return 2

    bridge_path = Path(args.bridge_meta).expanduser().resolve()
    structured_path = Path(args.structured).expanduser().resolve()
    rolling_csv_src = Path(args.rolling_csv).expanduser().resolve()
    rolling_extra = (
        Path(args.rolling_extra_rows).expanduser().resolve()
        if args.rolling_extra_rows
        else None
    )

    for label, p in [("--bridge-meta", bridge_path),
                     ("--structured", structured_path),
                     ("--rolling-csv", rolling_csv_src)]:
        if not p.is_file():
            print(f"error: {label} not found: {p}", file=sys.stderr)
            return 2
    if rolling_extra is not None and not rolling_extra.is_file():
        print(f"error: --rolling-extra-rows not found: {rolling_extra}", file=sys.stderr)
        return 2

    workdir = Path(args.workdir).expanduser().resolve()
    if _is_inside_repo(workdir):
        print(
            f"error: --workdir must live outside the repo (got {workdir}); pick a "
            f"path under /tmp.",
            file=sys.stderr,
        )
        return 2

    # ---- workdir setup ----------------------------------------------------
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commands_run: list[str] = []

    summary: dict = {
        "date": args.date,
        "generated_at": started_at,
        "merge_meta_status": "pending",
        "build_status": "pending",
        "rolling_append_status": "pending",
        "rows_in": None,
        "rows_accepted": None,
        "rows_rejected": None,
        "direct_trade_signal_all_false": None,
        "rolling_validated": None,
        "rolling_rejected": None,
        "rolling_duplicate_skip": None,
        "rolling_to_add": None,
        "commands_run": commands_run,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "drive_writes": 0,
            "latest_updates": 0,
            "promote_runs": 0,
            "super_pack_rebuilds": 0,
            "rolling_apply_runs": 0,
            "templates_csv_writes": 0,
        },
    }

    overall_rc = 0

    def _emit_summary() -> None:
        summary_path = workdir / "pipeline_summary.json"
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[runner] wrote {summary_path}")

    try:
        # ---- step 1: merge_meta -----------------------------------------
        merged_path = workdir / "parsed_meta.merged.json"
        merge_cmd = [
            sys.executable, str(MERGE_META_PY),
            "--bridge-meta", str(bridge_path),
            "--structured", str(structured_path),
            "--out", str(merged_path),
            "--apply",  # writes ONLY into workdir; never touches repo/Drive
        ]
        commands_run.append(" ".join(merge_cmd))
        proc = _run(merge_cmd, label="merge_meta", print_commands=args.print_commands)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0 or not merged_path.is_file():
            summary["merge_meta_status"] = f"failed (rc={proc.returncode})"
            print("error: merge_meta step failed; aborting", file=sys.stderr)
            overall_rc = 3
            return overall_rc
        summary["merge_meta_status"] = "ok"

        # ---- step 2: build_report_estimate --strict ---------------------
        build_cmd = [
            sys.executable, str(BUILD_REPORT_PY),
            "--input", str(merged_path),
            "--output-root", str(workdir),
            "--date", args.date,
        ]
        if args.strict:
            build_cmd.append("--strict")
        build_cmd.append("--apply")  # writes ONLY into workdir
        commands_run.append(" ".join(build_cmd))
        proc = _run(build_cmd, label="build_report_estimate",
                    print_commands=args.print_commands)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)

        build_summary_path = workdir / args.date / "estimate_revision_summary.json"
        rows_path = workdir / args.date / "estimate_revision_rows.json"
        rejected_path = workdir / args.date / "estimate_revision_rejected_rows.json"
        if proc.returncode != 0 or not build_summary_path.is_file():
            summary["build_status"] = f"failed (rc={proc.returncode})"
            print("error: build_report_estimate step failed; aborting", file=sys.stderr)
            overall_rc = 3
            return overall_rc

        build_summary = json.loads(build_summary_path.read_text(encoding="utf-8"))
        summary["build_status"] = "ok"
        summary["rows_in"] = build_summary.get("rows_in")
        summary["rows_accepted"] = build_summary.get("rows_accepted")
        summary["rows_rejected"] = build_summary.get("rows_rejected")
        summary["direct_trade_signal_all_false"] = build_summary.get("direct_trade_signal_all_false")

        # Hard invariant — runner refuses to proceed if Phase3 invariant slipped.
        if summary["direct_trade_signal_all_false"] is not True:
            print("error: build summary direct_trade_signal_all_false is not true; aborting",
                  file=sys.stderr)
            summary["build_status"] = "invariant_violated"
            overall_rc = 4
            return overall_rc

        accepted_rows = json.loads(rows_path.read_text(encoding="utf-8"))

        # ---- step 3: rolling_append --strict-estimate (dry-run) ---------
        # Seed CSV: copy templates header into workdir and prepend one
        # duplicate of the FIRST accepted row so the dedupe path exercises
        # `skipped(dup) >= 1`.
        seeded_csv = workdir / "seeded_estimate_history.csv"
        # Read source header
        header_line = rolling_csv_src.read_text(encoding="utf-8").splitlines()[0]
        header = [c.strip() for c in header_line.split(",")]
        with seeded_csv.open("w", encoding="utf-8", newline="") as f:
            f.write(header_line + "\n")
            if accepted_rows:
                seed = accepted_rows[0]
                # Only header columns; drop audit-only fields.
                values = [str(seed.get(c, "")) for c in header]
                f.write(",".join(values) + "\n")

        # Build rolling input: build accepted rows ⊕ optional hostile rows.
        rolling_input = list(accepted_rows)
        if rolling_extra is not None:
            extra = json.loads(rolling_extra.read_text(encoding="utf-8"))
            if not isinstance(extra, list):
                print("error: --rolling-extra-rows must be a JSON array", file=sys.stderr)
                overall_rc = 2
                return overall_rc
            rolling_input.extend(extra)
        rolling_input_path = workdir / "rolling_input.json"
        rolling_input_path.write_text(
            json.dumps(rolling_input, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        rolling_cmd = [
            sys.executable, str(ROLLING_APPEND_PY),
            "--csv", str(seeded_csv),
            "--rows", str(rolling_input_path),
            "--dedupe-keys", "date,ticker,broker,source_key",
            "--strict-estimate",
            # NB: NO --apply. Rolling step is dry-run-only in PR #9.
        ]
        commands_run.append(" ".join(rolling_cmd))
        proc = _run(rolling_cmd, label="rolling_append",
                    print_commands=args.print_commands)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            summary["rolling_append_status"] = f"failed (rc={proc.returncode})"
            print("error: rolling_append step failed; aborting", file=sys.stderr)
            overall_rc = 3
            return overall_rc

        rolling_counts = parse_rolling_stdout(proc.stdout)
        summary["rolling_append_status"] = "ok"
        summary["rolling_validated"] = rolling_counts.get("validated")
        summary["rolling_rejected"] = rolling_counts.get("rejected")
        summary["rolling_duplicate_skip"] = rolling_counts.get("duplicate_skip")
        summary["rolling_to_add"] = rolling_counts.get("to_add")

        # ---- final report -----------------------------------------------
        print()
        print("=" * 60)
        print(f"[runner] date                          = {summary['date']}")
        print(f"[runner] merge_meta_status             = {summary['merge_meta_status']}")
        print(f"[runner] build_status                  = {summary['build_status']}")
        print(f"[runner] rolling_append_status         = {summary['rolling_append_status']}")
        print(f"[runner] rows_in / accepted / rejected = "
              f"{summary['rows_in']} / {summary['rows_accepted']} / {summary['rows_rejected']}")
        print(f"[runner] direct_trade_signal_all_false = {summary['direct_trade_signal_all_false']}")
        print(f"[runner] rolling validated/rejected/dup/to_add = "
              f"{summary['rolling_validated']} / {summary['rolling_rejected']} / "
              f"{summary['rolling_duplicate_skip']} / {summary['rolling_to_add']}")
        print("=" * 60)

        if args.fail_on_rejected:
            if (summary["rows_rejected"] or 0) > 0 or (summary["rolling_rejected"] or 0) > 0:
                print("error: --fail-on-rejected was set and rejections were observed",
                      file=sys.stderr)
                overall_rc = 5
                return overall_rc

        return 0

    finally:
        # Always emit summary (best-effort) before optional cleanup so users
        # can inspect it in --keep-workdir mode.
        try:
            _emit_summary()
        except Exception as exc:
            print(f"[runner] warning: could not write pipeline_summary.json: {exc}",
                  file=sys.stderr)
        if not args.keep_workdir:
            try:
                shutil.rmtree(workdir)
                print(f"[runner] removed workdir {workdir} (use --keep-workdir to retain)")
            except OSError as exc:
                print(f"[runner] warning: could not remove workdir {workdir}: {exc}",
                      file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
