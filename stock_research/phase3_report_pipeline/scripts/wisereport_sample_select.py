#!/usr/bin/env python3
"""
Phase 3 — WiseReport sample selector for PR #11 real-data sample dry-run.

Picks up to 10 PDFs from a single date folder under a Drive-mounted
WiseReport root and writes a metadata-only inventory (sha256, size, mtime,
filename, inferred ticker hint, dup-suspect flag). It does NOT call OCR,
Vision, or any network API. It does NOT modify Drive. It does NOT copy
file bodies unless --copy-pdfs is explicitly passed (default: off).

This script is the only PR #11 artifact that actually touches user data.
The downstream chain (bridge → merge → build --strict → rolling --dry-run)
remains exactly the existing scripts; the procedure for running them on
the resulting inventory is documented in
`stock_research/phase3_report_pipeline/docs/REALDATA_SAMPLE_RUN.md`.

Hard caps (refuse to violate):
  * --max is clamped to 10 (PR #11 scope).
  * Output path must live OUTSIDE the repo. Refused with exit 2 otherwise.
  * --copy-pdfs is off by default; even when on, the destination must
    also be outside the repo.
  * No write back to --root. The script reads only.
  * On read errors (permission, decode, etc.) the entry is skipped with
    a warning rather than aborting the whole run.

Selection rules (documented for auditability):
  1. Restrict to `<root>/<date>/<include-folder>/*.pdf` (default
     `--include-folder 기업` for company reports).
  2. Infer a ticker hint from the standard filename pattern
     `YYYYMMDD_[종목명] 제목.pdf` — anything inside the first `[...]` block
     is the inferred ticker hint. If absent, the inferred hint is the
     stem before the first space.
  3. Sort by (mtime descending, filename ascending) so the picks are
     deterministic across runs.
  4. Prefer DIFFERENT inferred-ticker hints. The first occurrence of any
     hint wins; later occurrences are flagged `dup_suspect=true` and SKIPPED
     for selection (still listed in the inventory's `skipped` array so the
     user can inspect the redundancies).
  5. Stop selecting once `len(selected) == --max`.

This script is a metadata reader. There is intentionally no --apply: the
ONLY side effect is writing the inventory file to --out. dry-run-vs-apply
is not a meaningful distinction here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

HARD_MAX_PDFS = 10
DEFAULT_INCLUDE_FOLDER = "기업"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Capture content inside the first [...] block of the filename stem.
TICKER_HINT_RE = re.compile(r"\[([^\]]+)\]")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--root", required=True,
                   help="WiseReport root (Drive-mounted). e.g. "
                        "$GOOGLE_DRIVE_ROOT/01_data_inbox/wisereport_company")
    p.add_argument("--date", required=True, help="Target date YYYY-MM-DD")
    p.add_argument("--include-folder", default=DEFAULT_INCLUDE_FOLDER,
                   help=f"Subfolder under <root>/<date>/. Default: {DEFAULT_INCLUDE_FOLDER}")
    p.add_argument("--max", dest="max_pdfs", type=int, default=HARD_MAX_PDFS,
                   help=f"Max PDFs to select. Hard-capped at {HARD_MAX_PDFS} (PR #11 scope).")
    p.add_argument("--out", required=True,
                   help="Output directory (must live outside the repo). The "
                        "inventory is written to <out>/sample_inventory.json. "
                        "If --copy-pdfs is set, PDF bodies are also copied here.")
    p.add_argument("--copy-pdfs", action="store_true", default=False,
                   help="In addition to inventory, copy the selected PDF bytes "
                        "into <out>/pdfs/. Default off (metadata-only).")
    return p.parse_args(argv)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _infer_ticker_hint(name: str) -> str:
    stem = Path(name).stem
    m = TICKER_HINT_RE.search(stem)
    if m:
        return m.group(1).strip()
    # Fallback: first whitespace-delimited token of the stem.
    return stem.split()[0] if stem else ""


def _sha256_of(path: Path, *, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not DATE_RE.match(args.date):
        print(f"error: --date must be YYYY-MM-DD (got {args.date!r})", file=sys.stderr)
        return 2

    if args.max_pdfs > HARD_MAX_PDFS:
        print(f"error: --max {args.max_pdfs} exceeds the PR #11 hard cap "
              f"({HARD_MAX_PDFS}); refusing.", file=sys.stderr)
        return 2
    if args.max_pdfs < 1:
        print("error: --max must be >= 1", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser()
    out_dir = Path(args.out).expanduser().resolve()
    if _is_inside_repo(out_dir):
        print(f"error: --out must live outside the repo (got {out_dir}); "
              f"pick a path under /tmp.", file=sys.stderr)
        return 2

    target_dir = root / args.date / args.include_folder
    if not target_dir.is_dir():
        print(f"error: target dir not found or not a directory: {target_dir}",
              file=sys.stderr)
        return 2

    # Read-only: list .pdf files in the target dir, no recursion (intentional —
    # PR #11 scope is one date folder, one category).
    pdf_paths: list[Path] = sorted(
        [p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
    )
    if not pdf_paths:
        print(f"error: no PDF files in {target_dir}", file=sys.stderr)
        return 2

    # Build per-file metadata records.
    raw_records: list[dict] = []
    for pdf in pdf_paths:
        try:
            stat = pdf.stat()
            sha = _sha256_of(pdf)
        except OSError as exc:
            print(f"warning: skipping unreadable file {pdf}: {exc}", file=sys.stderr)
            continue
        raw_records.append({
            "filename": pdf.name,
            "source_path": str(pdf),
            "size_bytes": stat.st_size,
            "mtime_iso": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                                 .strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_pdf_sha256": sha,
            "ticker_hint": _infer_ticker_hint(pdf.name),
        })

    # Deterministic order: newest first (mtime desc), filename asc as tiebreak.
    raw_records.sort(key=lambda r: (-_iso_to_epoch(r["mtime_iso"]), r["filename"]))

    selected: list[dict] = []
    skipped: list[dict] = []
    seen_hints: set[str] = set()
    seen_sha: set[str] = set()
    for rec in raw_records:
        # Independent dup checks: same hint -> dup_suspect_hint;
        # same sha256 -> dup_suspect_content (always skipped).
        is_hint_dup = rec["ticker_hint"] in seen_hints if rec["ticker_hint"] else False
        is_sha_dup = rec["source_pdf_sha256"] in seen_sha
        rec = dict(rec)  # local copy

        if is_sha_dup:
            rec["dup_suspect"] = True
            rec["dup_reason"] = "same_sha256_already_selected"
            skipped.append(rec)
            continue
        if is_hint_dup:
            rec["dup_suspect"] = True
            rec["dup_reason"] = "same_ticker_hint_already_selected"
            skipped.append(rec)
            continue
        if len(selected) >= args.max_pdfs:
            rec["dup_suspect"] = False
            rec["skip_reason"] = "max_cap_reached"
            skipped.append(rec)
            continue

        rec["dup_suspect"] = False
        selected.append(rec)
        if rec["ticker_hint"]:
            seen_hints.add(rec["ticker_hint"])
        seen_sha.add(rec["source_pdf_sha256"])

    # Hard post-condition: NEVER write more than HARD_MAX_PDFS even if --max
    # somehow slipped past validation.
    if len(selected) > HARD_MAX_PDFS:
        print(f"error: invariant violated — selected {len(selected)} > "
              f"{HARD_MAX_PDFS}; refusing to write inventory", file=sys.stderr)
        return 3

    out_dir.mkdir(parents=True, exist_ok=True)
    inventory = {
        "schema": "phase3:wisereport_sample_inventory:v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "date": args.date,
        "include_folder": args.include_folder,
        "max_pdfs": args.max_pdfs,
        "hard_max": HARD_MAX_PDFS,
        "total_seen": len(raw_records),
        "selected_count": len(selected),
        "skipped_count": len(skipped),
        "selected": selected,
        "skipped": skipped,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "drive_writes": 0,
            "drive_renames": 0,
            "repo_writes": 0,  # this script never writes inside the repo by design
            "pdfs_copied": 0,  # updated below if --copy-pdfs
        },
    }

    if args.copy_pdfs:
        pdf_dst = out_dir / "pdfs"
        pdf_dst.mkdir(parents=True, exist_ok=True)
        copied = 0
        for rec in selected:
            src = Path(rec["source_path"])
            dst = pdf_dst / src.name
            shutil.copyfile(src, dst)
            copied += 1
        inventory["forbidden_actions_confirmed"]["pdfs_copied"] = copied

    inv_path = out_dir / "sample_inventory.json"
    inv_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[select] root              = {root}")
    print(f"[select] date              = {args.date}")
    print(f"[select] include-folder    = {args.include_folder}")
    print(f"[select] total PDFs seen   = {len(raw_records)}")
    print(f"[select] selected          = {len(selected)} (cap {args.max_pdfs})")
    print(f"[select] skipped           = {len(skipped)}")
    print(f"[select] wrote inventory   = {inv_path}")
    if args.copy_pdfs:
        print(f"[select] copied PDFs       = {inventory['forbidden_actions_confirmed']['pdfs_copied']} → {out_dir/'pdfs'}")
    return 0


def _iso_to_epoch(iso: str) -> float:
    # Tolerant parse: we control the input format above, so it's always
    # "YYYY-MM-DDTHH:MM:SSZ".
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    ).timestamp()


if __name__ == "__main__":
    raise SystemExit(main())
