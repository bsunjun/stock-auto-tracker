#!/usr/bin/env python3
"""
Phase 3 — Deterministic PDF estimate table extractor (PR #12 — skeleton).

Reads a WiseReport company-report PDF (or a pre-extracted text file, or an
inventory of either) and emits, per source PDF, at most ONE primary-metric
row to a structured_extraction.json that merge_meta.py can consume.

Design (frozen for PR #12):
  * deterministic-first. No OCR, no Vision, no network call.
  * primary metric priority:
        operating_profit > net_income > sales > eps
    Exactly one primary row per source_pdf_sha256 is emitted to
    structured_extraction.json (matching merge_meta's 1-row-per-sha
    contract).
  * full per-metric breakdown is written to a workdir-only audit file
    (estimate_table_breakdown.json), not consumed by merge_meta.
  * target-price-only reports are NOT emitted to structured_extraction.json
    (they would otherwise become primary-accepted under build --strict).
    They go to a workdir-only audit file (target_price_secondary.json).
  * direct_trade_signal is always False on every emitted row. PR #12 is
    not a trade-signal generator.
  * --apply refuses any --out / --workdir inside the repo.
  * --no-ocr is the default and the only supported mode in PR #12;
    Vision/OCR fallback is documented as a future option, not implemented.

This file is the SKELETON committed by PR #12A. The actual parsing logic
(text → metric rows; metric → primary selection; target-price detection)
lives in TODO functions and is filled in by subsequent commits.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

# Phase3 invariant. Every emitted row carries this verbatim.
DIRECT_TRADE_SIGNAL = False

# Primary metric selection (highest priority first).
PRIMARY_METRIC_PRIORITY: tuple[str, ...] = (
    "operating_profit",
    "net_income",
    "sales",
    "eps",
)

HARD_MAX_PDFS = 10
SOURCE_KEY_BASE = "phase3:pdf_estimate_table:v1"
DATE_FMT_HELP = "YYYY-MM-DD"


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = p.add_argument_group("input (one of)")
    src.add_argument("--pdf", default=None,
                     help="Path to a single PDF (requires pdfplumber if used).")
    src.add_argument("--text", default=None,
                     help="Path to a pre-extracted text file (no PDF parsing needed).")
    src.add_argument("--inventory", default=None,
                     help="Path to a sample_inventory.json (PR #11 shape). "
                          "Each selected[] entry is processed; per-PDF text "
                          "is looked up under --text-dir by filename stem.")
    src.add_argument("--text-dir", default=None,
                     help="Directory holding <stem>.txt files when using --inventory.")

    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help=f"Target date {DATE_FMT_HELP} (default: today)")
    p.add_argument("--out", default=None,
                   help="Output structured_extraction.json path (must live "
                        "outside the repo). Defaults to <workdir>/structured_extraction.json.")
    p.add_argument("--workdir", default="/tmp/phase3_pr12",
                   help="Workdir for audit artifacts (estimate_table_breakdown.json, "
                        "target_price_secondary.json). Must be outside the repo.")
    p.add_argument("--max-pdfs", dest="max_pdfs", type=int, default=HARD_MAX_PDFS,
                   help=f"Hard cap on inputs (clamped to {HARD_MAX_PDFS}).")

    p.add_argument("--no-ocr", dest="ocr", action="store_false", default=False,
                   help="(default) Disable any OCR fallback. PR #12 is "
                        "deterministic-only.")
    p.add_argument("--ocr", dest="ocr", action="store_true",
                   help="Refused in PR #12. Reserved for a future cost-gated PR.")

    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Parse and report; do not write outputs.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize structured_extraction.json + audit files. "
                        "Refused if --out or --workdir is inside the repo.")
    return p.parse_args(argv)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


# --- TODO (next commits in PR #12) ----------------------------------------
# These are intentional stubs. Each will be filled in by a subsequent
# small commit on this branch so each step is independently reviewable.

def parse_text_to_rows(text: str, *, source_pdf_sha256: str, filename: str,
                       date: str) -> dict:
    """Parse a single PDF's text into a structured record.

    Returned dict shape (planned):
        {
          "source_pdf_sha256": ...,
          "filename": ...,
          "broker": ...,
          "ticker_hint": ...,
          "horizon": ...,
          "metrics": {"sales": {old, new}, "operating_profit": {...}, ...},
          "target_price": {"old": ..., "new": ...} | None,
          "extraction_method": "deterministic_pdf_table_v1",
        }
    """
    raise NotImplementedError("parse_text_to_rows: filled in by next commit")


def select_primary_metric(metrics: dict) -> str | None:
    """Apply PRIMARY_METRIC_PRIORITY; return the chosen metric name or None."""
    raise NotImplementedError("select_primary_metric: filled in by next commit")


def project_structured_row(parsed: dict, *, date: str) -> dict | None:
    """Convert a parsed record into a single merge_meta-compatible row.

    Returns None if no primary metric is present (target-price-only or empty).
    Always sets `direct_trade_signal=False`.
    """
    raise NotImplementedError("project_structured_row: filled in by next commit")
# --------------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    # Skeleton-level guards that ARE active in PR #12A.
    if args.ocr:
        print("error: --ocr is refused in PR #12 (deterministic-only). "
              "OCR/Vision fallback is reserved for a future cost-gated PR.",
              file=sys.stderr)
        return 2

    if args.max_pdfs > HARD_MAX_PDFS:
        print(f"error: --max-pdfs {args.max_pdfs} exceeds the hard cap "
              f"({HARD_MAX_PDFS}); refusing.", file=sys.stderr)
        return 2
    if args.max_pdfs < 1:
        print("error: --max-pdfs must be >= 1", file=sys.stderr)
        return 2

    workdir = Path(args.workdir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve() if args.out \
        else (workdir / "structured_extraction.json")

    if not args.dry_run:
        if _is_inside_repo(workdir):
            print(f"error: --workdir must live outside the repo (got {workdir})",
                  file=sys.stderr)
            return 2
        if _is_inside_repo(out_path):
            print(f"error: --out must live outside the repo (got {out_path})",
                  file=sys.stderr)
            return 2

    # Skeleton: declare intent and exit. The actual parsing pipeline
    # is implemented in subsequent commits on this branch.
    inputs_provided = sum(bool(x) for x in (args.pdf, args.text, args.inventory))
    if inputs_provided == 0:
        print("error: provide one of --pdf / --text / --inventory.", file=sys.stderr)
        return 2

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] extractor: skeleton only (PR #12A); parsing logic is TODO.")
    print(f"[{mode}] workdir = {workdir}")
    print(f"[{mode}] out     = {out_path}")
    print(f"[{mode}] max-pdfs = {args.max_pdfs} (hard cap {HARD_MAX_PDFS})")
    print(f"[{mode}] ocr     = {args.ocr} (deterministic-only mode)")
    print(f"[{mode}] primary-metric priority = {PRIMARY_METRIC_PRIORITY}")
    print(f"[{mode}] direct_trade_signal     = {DIRECT_TRADE_SIGNAL}  (every emitted row)")
    print(f"[{mode}] inputs provided         = "
          f"pdf={bool(args.pdf)} text={bool(args.text)} inventory={bool(args.inventory)}")
    print("[NOTE] PR #12A is a scaffold. Re-run after PR #12B+ commits add "
          "parse_text_to_rows / select_primary_metric / project_structured_row.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
