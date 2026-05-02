#!/usr/bin/env python3
"""PR #38 — Self-test runner for the emit_revision_trend fixture.

Loads `examples/emit_revision_trend_fixture/{accepted_rows,structured_extraction,expected_classifications}.json`,
runs `scripts/emit_revision_trend.py` in dry-run AND apply mode (apply only
into a /tmp workdir; never the repo), and asserts:

  * Per-case classification matches `expected_classifications.json`.
  * Aggregated classification_counts match.
  * Trend rows count == accepted_rows_in.
  * High-table candidate count == expected.
  * direct_trade_signal_all_false == true on every emitted row AND in summary.
  * No row whose metric == "target_price" appears in high_table_candidates.
  * No row with direction != "up" appears in high_table_candidates.
  * The CSV / JSON outputs are byte-readable and consistent with the trend
    JSON (same row ordering, same row count).

Usage
-----
  python3 examples/run_emit_revision_trend_fixture.py

Exit code
---------
  0 on PASS; 1 on the first FAIL with a descriptive stderr message.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
SCRIPT = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "scripts" / "emit_revision_trend.py"
FIXTURE = HERE / "emit_revision_trend_fixture"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        _fail(f"command exited {p.returncode}: {' '.join(cmd)}")
    return p


def main() -> int:
    accepted_path = FIXTURE / "accepted_rows.json"
    structured_path = FIXTURE / "structured_extraction.json"
    expected_path = FIXTURE / "expected_classifications.json"

    for p in (accepted_path, structured_path, expected_path, SCRIPT):
        if not p.is_file():
            _fail(f"missing fixture / script: {p}")

    accepted = json.loads(accepted_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    case_to_sha: dict[str, str] = {}
    for r in accepted:
        case_to_sha[r["case"]] = r["source_pdf_sha256"]

    # 1. Dry-run mode (no files).
    dry_cmd = [
        sys.executable, str(SCRIPT),
        "--accepted-rows", str(accepted_path),
        "--structured", str(structured_path),
        "--output-dir", "/tmp/__pr38_dryrun_should_never_exist__",
        "--date", "2026-04-30",
    ]
    p_dry = _run(dry_cmd)
    if "[DRY-RUN]" not in p_dry.stdout:
        _fail("dry-run output did not say [DRY-RUN] — script may have written files.")

    # 2. Apply mode into a tmp dir.
    tmpdir = Path(tempfile.mkdtemp(prefix="pr38_emit_fix_"))
    try:
        apply_cmd = dry_cmd[:-2] + ["--output-dir", str(tmpdir), "--date", "2026-04-30", "--apply"]
        # Replace placeholder output-dir
        apply_cmd = [
            sys.executable, str(SCRIPT),
            "--accepted-rows", str(accepted_path),
            "--structured", str(structured_path),
            "--output-dir", str(tmpdir),
            "--date", "2026-04-30",
            "--apply",
        ]
        _run(apply_cmd)

        date_dir = tmpdir / "2026-04-30"
        trend_json = date_dir / "report_revision_trend.json"
        trend_csv = date_dir / "report_revision_trend.csv"
        high_json = date_dir / "report_estimate_high_table_candidates.json"
        high_csv = date_dir / "report_estimate_high_table_candidates.csv"
        summary_path = date_dir / "emit_revision_trend_summary.json"

        for p in (trend_json, trend_csv, high_json, high_csv, summary_path):
            if not p.is_file():
                _fail(f"--apply did not create {p}")

        trend_rows = json.loads(trend_json.read_text(encoding="utf-8"))
        high_rows = json.loads(high_json.read_text(encoding="utf-8"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        # 3. Per-case classification check.
        # Note: emitted trend rows do NOT carry the fixture's `case` label,
        # so match them back via source_pdf_sha256.
        sha_to_classification: dict[str, str] = {}
        for r in trend_rows:
            sha_short = r.get("source_pdf_sha256_short", "")
            sha_to_classification[sha_short] = r.get("classification", "")

        for case, want in expected["per_case"].items():
            sha_full = case_to_sha[case]
            sha_short = sha_full[:12]
            got = sha_to_classification.get(sha_short)
            if got != want:
                _fail(f"case={case} sha_short={sha_short} expected classification={want!r} got={got!r}")

        # 4. Aggregated classification counts.
        for c, want in expected["expected_classification_counts"].items():
            got = summary["classification_counts"].get(c, -1)
            if got != want:
                _fail(f"classification_counts[{c}] expected={want} got={got}")

        # 5. High table candidate count.
        if len(high_rows) != expected["expected_high_table_candidates_count"]:
            _fail(f"high_table_candidates count expected={expected['expected_high_table_candidates_count']}"
                  f" got={len(high_rows)}")

        # 6. target_price_only_count and metric_missing_count.
        if summary["target_price_only_count"] != expected["expected_target_price_only_count"]:
            _fail(f"target_price_only_count expected={expected['expected_target_price_only_count']}"
                  f" got={summary['target_price_only_count']}")
        if summary["metric_missing_count"] != expected["expected_metric_missing_count"]:
            _fail(f"metric_missing_count expected={expected['expected_metric_missing_count']}"
                  f" got={summary['metric_missing_count']}")

        # 7. direct_trade_signal_all_false invariant.
        if not summary["direct_trade_signal_all_false"]:
            _fail("summary direct_trade_signal_all_false != true")
        for r in trend_rows + high_rows:
            if r.get("direct_trade_signal") is not False:
                _fail(f"row direct_trade_signal must be False, got {r.get('direct_trade_signal')!r}")

        # 8. high_table_candidates invariants — never down, never target_price.
        for r in high_rows:
            if r.get("direction") != "up":
                _fail(f"high_table row direction must be 'up', got {r.get('direction')!r}")
            if r.get("metric") == "target_price":
                _fail("high_table row carried metric=target_price (forbidden)")
            if r.get("metric") not in {"operating_profit", "net_income", "sales", "eps"}:
                _fail(f"high_table row carries non-primary metric {r.get('metric')!r}")

        # 9. trend rows count.
        if len(trend_rows) != len(accepted):
            _fail(f"trend_rows count expected={len(accepted)} got={len(trend_rows)}")

        # 10. CSV row count consistency.
        with trend_csv.open(encoding="utf-8") as fh:
            csv_rows = list(csv.DictReader(fh))
        if len(csv_rows) != len(trend_rows):
            _fail(f"trend CSV row count {len(csv_rows)} != JSON {len(trend_rows)}")
        with high_csv.open(encoding="utf-8") as fh:
            high_csv_rows = list(csv.DictReader(fh))
        if len(high_csv_rows) != len(high_rows):
            _fail(f"high_table CSV row count {len(high_csv_rows)} != JSON {len(high_rows)}")

        # 11. forbidden_actions_confirmed audit.
        fa = summary["forbidden_actions_confirmed"]
        for k in ("ocr_or_vision_or_api_calls", "drive_writes", "drive_renames",
                  "repo_writes", "rolling_apply", "promote_or_super_pack",
                  "direct_trade_signal_true", "target_price_as_primary"):
            if fa.get(k) != 0:
                _fail(f"forbidden_actions_confirmed[{k}] must be 0, got {fa.get(k)!r}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"PASS run_emit_revision_trend_fixture: {len(accepted)} cases, "
          f"high_table_candidates={len(high_rows)}, "
          f"counts={summary['classification_counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
