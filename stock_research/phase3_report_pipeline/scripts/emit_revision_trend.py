#!/usr/bin/env python3
"""
Phase 3 — PR #38 — Emit `REPORT_REVISION_TREND` and
`REPORT_ESTIMATE_HIGH_TABLE_CANDIDATES` operational outputs from
`build_report_estimate_v132.py --strict --apply` accepted rows.

Inputs
------
  --accepted-rows  Path to estimate_revision_rows.json (build accepted rows).
                   Each entry is a dict with at least
                   {date, ticker, broker, old_target, new_target, direction,
                    horizon, source_key, source_pdf_sha256,
                    direct_trade_signal=False}.
  --structured     Optional structured_extraction.json. Used purely to look
                   up the `metric` field per row via source_pdf_sha256. If
                   omitted (or no match), the row's metric is treated as
                   missing and the row classifies as `data_insufficient`.
  --output-dir     Output directory. Outputs land under <output-dir>/<date>/.
                   --apply also writes there. Default: dry-run (no files).
  --date           YYYY-MM-DD (default = today). Forms the date subdir.

Outputs (apply mode)
--------------------
  <output-dir>/<date>/report_revision_trend.json
  <output-dir>/<date>/report_revision_trend.csv
  <output-dir>/<date>/report_estimate_high_table_candidates.json
  <output-dir>/<date>/report_estimate_high_table_candidates.csv
  <output-dir>/<date>/emit_revision_trend_summary.json

Schemas
-------
  report_revision_trend rows         → phase3:report_revision_trend:v1
  high_table_candidates rows         → phase3:report_estimate_high_table_candidates:v1
  emit_revision_trend_summary block  → phase3:emit_revision_trend_summary:v1

Classification (per accepted row)
---------------------------------
  data_insufficient
    → any of {ticker, broker, horizon, metric, old_target, new_target,
      direction} missing / non-finite, OR ticker not KRX:NNNNNN, OR direction
      not in {up, down, flat}, OR metric not one of the four primary metrics
      below (i.e. metric == 'target_price' counts as data_insufficient — it
      is preserved as `secondary_reference` only and never becomes a primary
      signal).

  downside_guard_excluded
    → direction == 'down' (estimate cut). The row is preserved in the
      revision-trend output for historical context but is NEVER promoted to
      high_table_candidates. Phase 3 does not emit downside trade signals.

  marginal_review
    → direction == 'flat' (delta == 0), OR direction == 'up' with
      |new - old| / |old| < HIGH_CONVICTION_DELTA_PCT (5% by default), OR
      direction == 'up' but old_target is 0 (delta % undefined).

  margin_expansion
    → reserved bucket for future margin-metric expansion (e.g. operating
      margin / GP margin). The current parser does not surface margin
      revisions as a primary metric, so this bucket stays empty in v1.
      Reserved up-front so the schema is stable.

  high_conviction
    → direction == 'up' AND metric in {operating_profit, net_income, sales,
      eps} AND |new - old| / |old| >= HIGH_CONVICTION_DELTA_PCT AND old_target
      is a finite non-zero number AND new_target is a finite number.

Defenses
--------
  * direct_trade_signal is forced to False on every emitted row. The
    summary records `direct_trade_signal_all_false: true`. Any input row
    arriving with direct_trade_signal=true makes this script exit 3 (the
    upstream build already gates this; this is a belt-and-braces guard).
  * target_price is recorded as `secondary_reference` only — no row whose
    sole metric is target_price is ever classified as high_conviction or
    margin_expansion. Such rows surface in the trend output with
    classification=data_insufficient and `is_target_price_only=true`.
  * Output is dry-run by default. --apply is the only path that writes
    files; even then the date subdir is created lazily and the script
    refuses --output-dir paths that resolve inside the repo (mirrors the
    PR #29 chain runner workdir guard).

Forbidden actions audit (in summary)
------------------------------------
  ocr_or_vision_or_api_calls = 0
  drive_writes / drive_renames / repo_writes = 0
  rolling_apply / promote_or_super_pack = 0
  direct_trade_signal_true = 0
  target_price_as_primary = 0

This script never imports OCR / vision / network libraries. All work is
pure JSON/CSV transformation of the upstream accepted rows.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List


THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

PRIMARY_METRICS: frozenset[str] = frozenset({
    "operating_profit", "net_income", "sales", "eps",
})
SECONDARY_REFERENCE_METRIC = "target_price"

VALID_DIRECTIONS: frozenset[str] = frozenset({"up", "down", "flat"})

HIGH_CONVICTION_DELTA_PCT = 0.05  # 5%

TREND_SCHEMA = "phase3:report_revision_trend:v1"
HIGH_TABLE_SCHEMA = "phase3:report_estimate_high_table_candidates:v1"
SUMMARY_SCHEMA = "phase3:emit_revision_trend_summary:v1"

CLASSIFICATIONS: tuple[str, ...] = (
    "high_conviction",
    "margin_expansion",
    "marginal_review",
    "downside_guard_excluded",
    "data_insufficient",
)

TREND_CSV_HEADER: tuple[str, ...] = (
    "date", "ticker", "broker", "metric",
    "old_target", "new_target", "delta_pct",
    "direction", "horizon", "classification",
    "is_target_price_only", "source_key", "source_pdf_sha256_short",
)
HIGH_TABLE_CSV_HEADER: tuple[str, ...] = (
    "date", "ticker", "broker", "metric",
    "old_target", "new_target", "delta_pct",
    "direction", "horizon", "source_key", "source_pdf_sha256_short",
)


def _is_finite_number(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return math.isfinite(float(v))
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if not s:
            return False
        try:
            f = float(s)
        except ValueError:
            return False
        return math.isfinite(f)
    return False


def _to_float(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if not s:
            return None
        try:
            f = float(s)
        except ValueError:
            return None
        return f if math.isfinite(f) else None
    return None


def _is_krx(t: Any) -> bool:
    return isinstance(t, str) and t.startswith("KRX:") and len(t) == 10 and t[4:].isdigit()


def _delta_pct(old_v: float | None, new_v: float | None) -> float | None:
    """|new - old| / |old|. Returns None if either is None or old == 0."""
    if old_v is None or new_v is None:
        return None
    if old_v == 0:
        return None
    return abs(new_v - old_v) / abs(old_v)


def _short_sha(s: Any) -> str:
    if not isinstance(s, str):
        return ""
    return s[:12]


def classify_row(row: dict, metric: str | None) -> tuple[str, dict]:
    """Return (classification, derived_fields).

    `derived_fields` is a small dict the caller layers onto the trend row:
      * delta_pct (float | None)
      * is_target_price_only (bool)
      * classification_reason (short stable token)
    """
    derived: dict[str, Any] = {
        "delta_pct": None,
        "is_target_price_only": False,
        "classification_reason": "",
    }

    direction = row.get("direction")
    ticker = row.get("ticker")
    broker = row.get("broker")
    horizon = row.get("horizon")
    old_v = _to_float(row.get("old_target"))
    new_v = _to_float(row.get("new_target"))

    if metric == SECONDARY_REFERENCE_METRIC:
        derived["is_target_price_only"] = True
        derived["classification_reason"] = "target_price_secondary_only"
        return "data_insufficient", derived

    required_present = (
        _is_krx(ticker)
        and isinstance(broker, str) and broker
        and isinstance(horizon, str) and horizon
        and metric in PRIMARY_METRICS
        and direction in VALID_DIRECTIONS
        and old_v is not None
        and new_v is not None
    )
    if not required_present:
        derived["classification_reason"] = "required_field_missing_or_invalid"
        return "data_insufficient", derived

    delta = _delta_pct(old_v, new_v)
    derived["delta_pct"] = delta

    if direction == "down":
        derived["classification_reason"] = "direction_down_excluded"
        return "downside_guard_excluded", derived

    if direction == "flat":
        derived["classification_reason"] = "direction_flat_review"
        return "marginal_review", derived

    # direction == "up"
    if delta is None:
        derived["classification_reason"] = "old_target_zero_delta_undefined"
        return "marginal_review", derived
    if delta < HIGH_CONVICTION_DELTA_PCT:
        derived["classification_reason"] = "delta_below_threshold"
        return "marginal_review", derived

    derived["classification_reason"] = "primary_metric_revision_up"
    return "high_conviction", derived


def project_trend_row(row: dict, metric: str | None,
                      classification: str, derived: dict) -> dict:
    """Build one REPORT_REVISION_TREND row.

    Always carries direct_trade_signal=False. Never carries any field
    derived from target_price as a primary signal — `metric` is reported
    verbatim from structured_extraction (or "" if missing) for traceability.
    """
    return {
        "schema": TREND_SCHEMA,
        "date": row.get("date", ""),
        "ticker": row.get("ticker", ""),
        "broker": row.get("broker", ""),
        "metric": metric or "",
        "old_target": row.get("old_target"),
        "new_target": row.get("new_target"),
        "delta_pct": derived.get("delta_pct"),
        "direction": row.get("direction", ""),
        "horizon": row.get("horizon", ""),
        "classification": classification,
        "classification_reason": derived.get("classification_reason", ""),
        "is_target_price_only": bool(derived.get("is_target_price_only")),
        "source_key": row.get("source_key", ""),
        "source_pdf_sha256_short": _short_sha(row.get("source_pdf_sha256")),
        "direct_trade_signal": False,
    }


def project_high_table_row(trend_row: dict) -> dict:
    """Build one REPORT_ESTIMATE_HIGH_TABLE_CANDIDATES row from a
    classification=high_conviction trend row."""
    return {
        "schema": HIGH_TABLE_SCHEMA,
        "date": trend_row["date"],
        "ticker": trend_row["ticker"],
        "broker": trend_row["broker"],
        "metric": trend_row["metric"],
        "old_target": trend_row["old_target"],
        "new_target": trend_row["new_target"],
        "delta_pct": trend_row["delta_pct"],
        "direction": trend_row["direction"],
        "horizon": trend_row["horizon"],
        "source_key": trend_row["source_key"],
        "source_pdf_sha256_short": trend_row["source_pdf_sha256_short"],
        "direct_trade_signal": False,
    }


def write_csv(path: Path, header: Iterable[str], rows: list[dict]) -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(header), extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    path.write_text(buf.getvalue(), encoding="utf-8")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--accepted-rows", required=True,
                   help="estimate_revision_rows.json from build --strict --apply")
    p.add_argument("--structured", default=None,
                   help="Optional structured_extraction.json (for metric lookup)")
    p.add_argument("--output-dir", required=True,
                   help="Output root. Outputs land under <output-dir>/<date>/.")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Do not write files; print summary only.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize trend / high_table / summary files.")
    return p.parse_args(argv)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    accepted_path = Path(args.accepted_rows).expanduser().resolve()
    if not accepted_path.is_file():
        print(f"error: --accepted-rows not found: {accepted_path}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    if not args.dry_run and _is_inside_repo(output_dir):
        print(f"error: --output-dir must live outside the repo (got {output_dir})",
              file=sys.stderr)
        return 2

    rows = _load_json(accepted_path)
    if not isinstance(rows, list):
        print("error: --accepted-rows must be a JSON array", file=sys.stderr)
        return 2

    metric_by_sha: dict[str, str] = {}
    if args.structured:
        structured_path = Path(args.structured).expanduser().resolve()
        if not structured_path.is_file():
            print(f"error: --structured not found: {structured_path}", file=sys.stderr)
            return 2
        structured = _load_json(structured_path)
        if not isinstance(structured, list):
            print("error: --structured must be a JSON array", file=sys.stderr)
            return 2
        for s in structured:
            sha = s.get("source_pdf_sha256") if isinstance(s, dict) else None
            metric = s.get("metric") if isinstance(s, dict) else None
            if isinstance(sha, str) and sha and isinstance(metric, str) and metric:
                # If multiple rows share a sha, the FIRST wins. The parser
                # already enforces "at most ONE primary-metric row per PDF",
                # so this is defensive only.
                metric_by_sha.setdefault(sha, metric)

    trend_rows: list[dict] = []
    high_table_rows: list[dict] = []
    classification_counts: dict[str, int] = {c: 0 for c in CLASSIFICATIONS}
    direct_trade_signal_true_count = 0
    target_price_only_count = 0
    metric_missing_count = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("direct_trade_signal") is True:
            direct_trade_signal_true_count += 1
            print("error: input row carries direct_trade_signal=true; "
                  "PR #38 refuses to emit. Re-run upstream build --strict.",
                  file=sys.stderr)
            return 3

        sha = row.get("source_pdf_sha256") or ""
        metric = metric_by_sha.get(sha) if sha else None
        if metric is None:
            metric_missing_count += 1

        classification, derived = classify_row(row, metric)
        if derived.get("is_target_price_only"):
            target_price_only_count += 1
        classification_counts[classification] += 1

        trend_row = project_trend_row(row, metric, classification, derived)
        trend_rows.append(trend_row)

        if classification == "high_conviction":
            high_table_rows.append(project_high_table_row(trend_row))

    summary = {
        "schema": SUMMARY_SCHEMA,
        "date": args.date,
        "accepted_rows_in": len(rows),
        "trend_rows_emitted": len(trend_rows),
        "high_table_candidates_emitted": len(high_table_rows),
        "classification_counts": classification_counts,
        "metric_missing_count": metric_missing_count,
        "target_price_only_count": target_price_only_count,
        "high_conviction_delta_pct_threshold": HIGH_CONVICTION_DELTA_PCT,
        "primary_metrics": sorted(PRIMARY_METRICS),
        "secondary_reference_metric": SECONDARY_REFERENCE_METRIC,
        "direct_trade_signal_all_false": direct_trade_signal_true_count == 0,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "drive_writes": 0,
            "drive_renames": 0,
            "repo_writes": 0,
            "rolling_apply": 0,
            "promote_or_super_pack": 0,
            "direct_trade_signal_true": direct_trade_signal_true_count,
            "target_price_as_primary": 0,
        },
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] accepted_rows_in = {summary['accepted_rows_in']}")
    print(f"[{mode}] trend_rows_emitted = {summary['trend_rows_emitted']}")
    print(f"[{mode}] high_table_candidates = {summary['high_table_candidates_emitted']}")
    for c in CLASSIFICATIONS:
        print(f"[{mode}]   classification[{c}] = {classification_counts[c]}")
    print(f"[{mode}] metric_missing_count = {metric_missing_count}")
    print(f"[{mode}] target_price_only_count = {target_price_only_count}")
    print(f"[{mode}] direct_trade_signal_all_false = "
          f"{summary['direct_trade_signal_all_false']}")

    if args.dry_run:
        return 0

    date_dir = output_dir / args.date
    date_dir.mkdir(parents=True, exist_ok=True)

    trend_json = date_dir / "report_revision_trend.json"
    trend_csv = date_dir / "report_revision_trend.csv"
    high_json = date_dir / "report_estimate_high_table_candidates.json"
    high_csv = date_dir / "report_estimate_high_table_candidates.csv"
    summary_path = date_dir / "emit_revision_trend_summary.json"

    trend_json.write_text(
        json.dumps(trend_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(trend_csv, TREND_CSV_HEADER, trend_rows)
    high_json.write_text(
        json.dumps(high_table_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(high_csv, HIGH_TABLE_CSV_HEADER, high_table_rows)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[APPLY] wrote {trend_json}")
    print(f"[APPLY] wrote {trend_csv}")
    print(f"[APPLY] wrote {high_json}")
    print(f"[APPLY] wrote {high_csv}")
    print(f"[APPLY] wrote {summary_path}")
    print(f"[NEXT] These outputs are dry-run operational artifacts. They are NOT")
    print(f"       fed to rolling_append.py or any --apply path. Treat them as")
    print(f"       read-only inputs for downstream review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
