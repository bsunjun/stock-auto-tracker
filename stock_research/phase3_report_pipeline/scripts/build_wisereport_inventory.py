#!/usr/bin/env python3
"""
Phase 3 — PR #39 — WiseReport date-folder inventory builder.

Scans an `operator-host local mount` (or any filesystem path that mirrors
the Drive layout) of the form

    <root>/<YYYY-MM-DD>/기업/*.pdf       (company reports)
    <root>/<YYYY-MM-DD>/산업/*.pdf       (industry reports)

and emits a single inventory JSON containing per-PDF metadata for both
report types. The output is consumable by:

  * Company entries — `examples/run_inventory_batch_smoke.py --inventory`
    (i.e., the existing PR #29 chain runner: parser → bridge → merge → build).
  * Industry entries — a separate downstream LLM-summary queue (NOT the
    parser; industry PDFs are not run through deterministic metric
    extraction in v1 of this script).

Usage
-----
    python3 scripts/build_wisereport_inventory.py \
        --root /path/to/wisereport \
        --date 2026-04-30 \
        --include-company \
        --include-industry \
        --out /tmp/wisereport_inventory.json \
        --max-company-pdfs 50 \
        --max-industry-pdfs 50 \
        [--apply]

Defaults
--------
  --max-company-pdfs   50   (hard cap 50 — values > 50 refused with exit 2)
  --max-industry-pdfs  50   (hard cap 50)
  default mode         dry-run; --apply is the only path that writes --out.

Schema (`phase3:wisereport_date_folder_inventory:v1`)
-----------------------------------------------------
{
  "schema": "phase3:wisereport_date_folder_inventory:v1",
  "root": "<root>",
  "date": "YYYY-MM-DD",
  "include_company": true|false,
  "include_industry": true|false,
  "max_company_pdfs": 50,
  "max_industry_pdfs": 50,
  "summary": {
    "company_pdf_count": int,
    "industry_pdf_count": int,
    "malformed_filename_count": int,
    "duplicate_basename_count": int,
    "skipped_non_pdf_count": int,
    "capped_company_count": int,
    "capped_industry_count": int,
    "direct_trade_signal_true_count": 0,
    "selected_alias_count": int,                  # PR #40: == len(selected_company)
    "selected_alias_matches_company": true        # PR #40: invariant
  },
  "selected": [ ... ],            # PR #40: alias mirroring `selected_company[]`
                                  #         (so `extract_report_estimate_table.py`
                                  #         and `run_inventory_batch_smoke.py
                                  #         --inventory` consume directly).
                                  #         NEVER mirrors `selected_industry[]`.
  "selected_company": [ ... ],   # capped at max-company-pdfs
  "selected_industry": [ ... ],  # capped at max-industry-pdfs (NOT in `selected`)
  "malformed": [ {filename, folder, reason} ... ],
  "skipped_non_pdf": [ {filename, folder} ... ],
  "duplicate_basename": [ {basename, folder, count} ... ],
  "forbidden_actions_confirmed": { ... }
}

Per-PDF entry shape
-------------------
Company (selected_company[]):
  { report_date, report_type=company, filename, local_pdf_path,
    ticker_hint, title_hint, folder_type=기업, sha256_prefix_12,
    direct_trade_signal=false }

Industry (selected_industry[]):
  { report_date, report_type=industry, filename, local_pdf_path,
    sector_hint, title_hint, folder_type=산업, sha256_prefix_12,
    direct_trade_signal=false, summary_queue=true }

Forbidden / refused operations
------------------------------
  * Drive writes / renames / deletes — this script never modifies the
    source folder; it only stat / read files.
  * No OCR / Vision / network calls.
  * No write of PDF body text or extracted text — only filenames,
    paths, and the first 12 hex chars of sha256.
  * `--out` resolving inside the repo + `--apply` → exit 2 (PR #29 guard
    policy: outputs cannot leak into the worktree).
  * `--max-*-pdfs` > 50 → exit 2 (HARD_MAX invariant).
  * Default dry-run; only `--apply` writes the file.
  * Every emitted entry carries `direct_trade_signal: false`. The summary
    counter `direct_trade_signal_true_count` is hard-coded to 0; if any
    upstream-supplied entry tried to set it to true, this script would
    not emit such an entry by construction (the field is never read from
    user input).

This script does NOT change parser / bridge / merge / build / emit / ticker
map / broker autodetect logic. It is purely a folder-scanner that builds
an inventory JSON for downstream consumption.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

INVENTORY_SCHEMA = "phase3:wisereport_date_folder_inventory:v1"

HARD_MAX_PDFS = 50

FOLDER_COMPANY = "기업"
FOLDER_INDUSTRY = "산업"

# `YYYYMMDD_[<bracket>] <title>.pdf`
_FILENAME_RE = re.compile(
    r"^(?P<date>\d{8})_\[(?P<bracket>[^\]]+)\]\s*(?P<title>.+)\.pdf$",
    re.IGNORECASE,
)

PDF_EXT_LOWER = ".pdf"


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _sha256_prefix_12(path: Path) -> str:
    """Return first 12 hex chars of the file's sha256.

    We deliberately stop at 12 chars — sha256 collisions across 12 hex
    digits are still vanishingly unlikely for a single date-folder cohort
    (≤ 100 PDFs), and limiting the surface keeps PDF body fingerprints
    out of any downstream artifact. Full sha256 stays on disk only.
    """
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def _classify_filename(filename: str) -> tuple[str | None, str | None, str | None]:
    """Return (bracket_text, title_text, malformed_reason).

    On success: (bracket, title, None).
    On malformed: (None, None, reason_token).
    """
    m = _FILENAME_RE.match(filename)
    if m:
        return m.group("bracket").strip(), m.group("title").strip(), None

    if not filename.lower().endswith(PDF_EXT_LOWER):
        return None, None, "not_pdf_extension"
    if "[" not in filename or "]" not in filename:
        return None, None, "no_bracket_segment"
    if not re.match(r"^\d{8}_", filename):
        return None, None, "no_yyyymmdd_prefix"
    return None, None, "regex_match_failed"


def _scan_folder(
    folder: Path,
    folder_type: str,
    report_type: str,
    report_date: str,
    max_pdfs: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict], int, int]:
    """Scan one folder for PDFs.

    Returns:
        selected:           list of per-file dicts (capped at max_pdfs)
        malformed:          list of {filename, folder, reason}
        skipped_non_pdf:    list of {filename, folder}
        duplicate_basename: list of {basename, folder, count}  (count > 1)
        scanned_pdf_count:  total PDFs the folder contained (pre-cap, malformed-included)
        capped_dropped:     number of PDFs dropped because of the per-folder cap
    """
    selected: list[dict] = []
    malformed: list[dict] = []
    skipped_non_pdf: list[dict] = []
    duplicate_basename: list[dict] = []
    scanned_pdf_count = 0
    capped_dropped = 0

    if not folder.is_dir():
        return selected, malformed, skipped_non_pdf, duplicate_basename, 0, 0

    # Deterministic ordering for capping.
    entries = sorted(folder.iterdir(), key=lambda p: p.name)

    seen_basename_to_count: dict[str, int] = {}
    valid_pre_cap: list[tuple[Path, str, str]] = []  # (path, bracket, title)

    for ent in entries:
        if not ent.is_file():
            continue
        name = ent.name
        if not name.lower().endswith(PDF_EXT_LOWER):
            skipped_non_pdf.append({"filename": name, "folder": folder_type})
            continue

        scanned_pdf_count += 1

        seen_basename_to_count[name] = seen_basename_to_count.get(name, 0) + 1

        bracket, title, reason = _classify_filename(name)
        if reason is not None:
            malformed.append({
                "filename": name,
                "folder": folder_type,
                "reason": reason,
            })
            continue

        valid_pre_cap.append((ent, bracket or "", title or ""))

    # Duplicate basenames within this folder. Filesystem-level duplicates
    # cannot exist (two files in the same dir cannot share the exact same
    # name), but case-insensitive filesystems / mounts surfaced via Drive
    # may produce them when a folder is mirrored. We detect by basename
    # frequency in the iteration above; counts > 1 land here.
    for bn, cnt in seen_basename_to_count.items():
        if cnt > 1:
            duplicate_basename.append({
                "basename": bn,
                "folder": folder_type,
                "count": cnt,
            })

    # Cap.
    if len(valid_pre_cap) > max_pdfs:
        capped_dropped = len(valid_pre_cap) - max_pdfs
        valid_pre_cap = valid_pre_cap[:max_pdfs]

    for path, bracket, title in valid_pre_cap:
        sha_pref = _sha256_prefix_12(path)
        entry: dict = {
            "report_date": report_date,
            "report_type": report_type,
            "filename": path.name,
            "local_pdf_path": str(path.resolve()),
            "title_hint": title,
            "folder_type": folder_type,
            "sha256_prefix_12": sha_pref,
            "direct_trade_signal": False,
        }
        if report_type == "company":
            entry["ticker_hint"] = bracket
        else:  # industry
            entry["sector_hint"] = bracket
            entry["summary_queue"] = True
        selected.append(entry)

    return (selected, malformed, skipped_non_pdf,
            duplicate_basename, scanned_pdf_count, capped_dropped)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", required=True,
                   help="WiseReport root directory (operator-host local mount or "
                        "Drive mount). The script reads <root>/<date>/기업 and "
                        "<root>/<date>/산업.")
    p.add_argument("--date", required=True,
                   help="Date subdirectory name (YYYY-MM-DD).")
    p.add_argument("--include-company", action="store_true", default=False,
                   help="Include the 기업 (company) folder in the inventory.")
    p.add_argument("--include-industry", action="store_true", default=False,
                   help="Include the 산업 (industry) folder in the inventory.")
    p.add_argument("--out", required=True,
                   help="Output JSON path. With --apply this file is written; "
                        "without --apply this script is dry-run and prints "
                        "the summary only. Refuses paths inside the repo "
                        "under --apply (PR #29 guard policy).")
    p.add_argument("--max-company-pdfs", type=int, default=50,
                   help=f"Per-folder cap on company entries (HARD_MAX={HARD_MAX_PDFS}).")
    p.add_argument("--max-industry-pdfs", type=int, default=50,
                   help=f"Per-folder cap on industry entries (HARD_MAX={HARD_MAX_PDFS}).")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Do not write --out; print summary only.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize the inventory JSON at --out.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.max_company_pdfs > HARD_MAX_PDFS or args.max_company_pdfs < 0:
        print(f"error: --max-company-pdfs must be 0..{HARD_MAX_PDFS} (got {args.max_company_pdfs})",
              file=sys.stderr)
        return 2
    if args.max_industry_pdfs > HARD_MAX_PDFS or args.max_industry_pdfs < 0:
        print(f"error: --max-industry-pdfs must be 0..{HARD_MAX_PDFS} (got {args.max_industry_pdfs})",
              file=sys.stderr)
        return 2

    if not (args.include_company or args.include_industry):
        print("error: at least one of --include-company / --include-industry must be set",
              file=sys.stderr)
        return 2

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
        print(f"error: --date must be YYYY-MM-DD (got {args.date})", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: --root not a directory: {root}", file=sys.stderr)
        return 2

    out_path = Path(args.out).expanduser().resolve()
    if not args.dry_run and _is_inside_repo(out_path):
        print(f"error: --out must live outside the repo under --apply (got {out_path})",
              file=sys.stderr)
        return 2

    date_dir = root / args.date

    company_dir = date_dir / FOLDER_COMPANY
    industry_dir = date_dir / FOLDER_INDUSTRY

    selected_company: list[dict] = []
    selected_industry: list[dict] = []
    malformed_all: list[dict] = []
    skipped_non_pdf_all: list[dict] = []
    duplicate_basename_all: list[dict] = []
    capped_company_count = 0
    capped_industry_count = 0

    if args.include_company:
        (selected_company, mal, npdf, dup, _scanned_c, capped_c) = _scan_folder(
            company_dir,
            folder_type=FOLDER_COMPANY,
            report_type="company",
            report_date=args.date,
            max_pdfs=args.max_company_pdfs,
        )
        malformed_all.extend(mal)
        skipped_non_pdf_all.extend(npdf)
        duplicate_basename_all.extend(dup)
        capped_company_count = capped_c

    if args.include_industry:
        (selected_industry, mal, npdf, dup, _scanned_i, capped_i) = _scan_folder(
            industry_dir,
            folder_type=FOLDER_INDUSTRY,
            report_type="industry",
            report_date=args.date,
            max_pdfs=args.max_industry_pdfs,
        )
        malformed_all.extend(mal)
        skipped_non_pdf_all.extend(npdf)
        duplicate_basename_all.extend(dup)
        capped_industry_count = capped_i

    summary = {
        "company_pdf_count": len(selected_company),
        "industry_pdf_count": len(selected_industry),
        "malformed_filename_count": len(malformed_all),
        "duplicate_basename_count": len(duplicate_basename_all),
        "skipped_non_pdf_count": len(skipped_non_pdf_all),
        "capped_company_count": capped_company_count,
        "capped_industry_count": capped_industry_count,
        "direct_trade_signal_true_count": 0,
        # PR #40: alias counters. `selected[]` is exactly `selected_company[]`
        # (industry entries NEVER mirror into the alias; see schema doc).
        "selected_alias_count": len(selected_company),
        "selected_alias_matches_company": True,
    }

    inventory = {
        "schema": INVENTORY_SCHEMA,
        "root": str(root),
        "date": args.date,
        "include_company": bool(args.include_company),
        "include_industry": bool(args.include_industry),
        "max_company_pdfs": args.max_company_pdfs,
        "max_industry_pdfs": args.max_industry_pdfs,
        "summary": summary,
        # PR #40: top-level `selected[]` alias of `selected_company[]` so the
        # existing PR #29 chain runner (`run_inventory_batch_smoke.py
        # --inventory`) and the parser
        # (`extract_report_estimate_table.py`, which reads `selected[]`)
        # consume this inventory directly without an adapter step.
        # By construction the alias mirrors `selected_company[]` ONLY;
        # `selected_industry[]` is preserved separately for the LLM-summary
        # queue and is NEVER folded into `selected[]`. The parser therefore
        # cannot accidentally process industry PDFs.
        "selected": list(selected_company),
        "selected_company": selected_company,
        "selected_industry": selected_industry,
        "malformed": malformed_all,
        "skipped_non_pdf": skipped_non_pdf_all,
        "duplicate_basename": duplicate_basename_all,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "drive_writes": 0,
            "drive_renames": 0,
            "drive_deletes": 0,
            "repo_writes": 0,
            "rolling_apply": 0,
            "promote_or_super_pack": 0,
            "direct_trade_signal_true": 0,
            "target_price_as_primary": 0,
            "pdf_body_text_committed": 0,
        },
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] root  = {root}")
    print(f"[{mode}] date  = {args.date}")
    print(f"[{mode}] include_company  = {args.include_company}")
    print(f"[{mode}] include_industry = {args.include_industry}")
    for k, v in summary.items():
        print(f"[{mode}]   summary.{k:35s} = {v}")

    if args.dry_run:
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[APPLY] wrote {out_path}")
    print(f"[NEXT] feed selected_company entries to "
          f"`examples/run_inventory_batch_smoke.py --inventory <out>` if "
          f"the existing PR #29 chain runner is desired.")
    print(f"[NEXT] selected_industry entries are NOT fed to the parser; "
          f"they are queued for downstream LLM summarization (out of scope "
          f"for PR #39).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
