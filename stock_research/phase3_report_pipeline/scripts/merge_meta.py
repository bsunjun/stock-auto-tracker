#!/usr/bin/env python3
"""
Phase 3 — Merge bridge parsed_meta.json with structured_extraction.json.

NO OCR. NO Vision API. NO PDF body parsing. NO history CSV append.

Inputs
  --bridge-meta  parsed_meta.json from bridge_scan_to_parsed_meta.py (PR #4)
  --structured   structured_extraction.json (output of vision_ocr_pdf.py
                 --extract-mode estimate, or hand-prepared per
                 examples/structured_extraction.example.json)
  --out          merged parsed_meta.json output path

Field-level priority (highest wins):
    manual          (bridge record where extraction_method == 'manual')
  > structured_extraction (any non-empty value from --structured)
  > filename_only (bridge record where extraction_method == 'filename_only'
                   or unset)

Per-record merge rules
  * Match by source_pdf_sha256 only. No filename / fuzzy fallback —
    sha256 is canonical to prevent silent mismatch.
  * For each of {broker, old_target, new_target, horizon}: gather all
    candidates from sources with non-empty values, keep the highest-
    priority one. Provenance recorded in `merge_provenance[<field>]`.
  * Conflicts (two sources with non-empty disagreeing values) are
    counted in the summary AND captured per-record under
    `merge_conflicts: [{field, kept_source, other_source, kept, other}]`.
  * After merging, recompute `direction` and `missing_fields`.
  * `complete = (missing_fields == [])`. NEVER set complete=true while
    any required field is empty.

Records present in --bridge-meta but with no matching extraction (or no
extraction file at all) pass through unchanged with merge_provenance
filled from the bridge's own extraction_method.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

REQUIRED_FIELDS = ["ticker", "broker", "report_date", "old_target", "new_target", "horizon"]
MERGE_FIELDS = ["broker", "old_target", "new_target", "horizon"]
PRIORITY = {"manual": 3, "structured_extraction": 2, "filename_only": 1}
MERGE_VERSION = "phase3:merge_meta:v1"


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bridge-meta", required=True, help="bridge parsed_meta.json (input)")
    p.add_argument("--structured", required=True, help="structured_extraction.json (input)")
    p.add_argument("--out", required=True, help="merged parsed_meta.json (output)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) summarize only; no file written")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="materialize merged JSON")
    return p.parse_args(argv)


def is_blank(v: object) -> bool:
    return v in (None, "", [], {})


def is_krx(t: object) -> bool:
    return isinstance(t, str) and t.startswith("KRX:")


def derive_direction(old: object, new: object) -> str:
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return "unknown"
    if n > o:
        return "up"
    if n < o:
        return "down"
    return "flat"


def bridge_method(rec: dict) -> str:
    """The record-level extraction_method that gates priority for bridge fields."""
    m = (rec.get("extraction_method") or "").strip()
    return m if m in ("manual", "filename_only") else "filename_only"


def merge_record(bridge_rec: dict, ext_rec: dict | None) -> dict:
    out = dict(bridge_rec)
    b_method = bridge_method(bridge_rec)
    provenance: dict[str, str] = {}
    conflicts: list[dict] = []

    for field in MERGE_FIELDS:
        b_val = bridge_rec.get(field)
        e_val = ext_rec.get(field) if ext_rec else None

        candidates: list[tuple[int, object, str]] = []
        if not is_blank(b_val):
            candidates.append((PRIORITY[b_method], b_val, b_method))
        if not is_blank(e_val):
            candidates.append((PRIORITY["structured_extraction"], e_val, "structured_extraction"))

        if not candidates:
            continue

        candidates.sort(key=lambda x: -x[0])
        kept_pri, kept_val, kept_src = candidates[0]
        out[field] = kept_val
        provenance[field] = kept_src

        if len(candidates) >= 2 and candidates[1][1] != kept_val:
            other_pri, other_val, other_src = candidates[1]
            conflicts.append({
                "field": field,
                "kept_source": kept_src,
                "kept": kept_val,
                "other_source": other_src,
                "other": other_val,
            })

    out["direction"] = derive_direction(out.get("old_target"), out.get("new_target"))

    missing: list[str] = []
    for f in REQUIRED_FIELDS:
        if is_blank(out.get(f)):
            missing.append(f)
    if out.get("ticker") and not is_krx(out["ticker"]):
        missing.append("ticker_unmapped")
    out["missing_fields"] = missing
    out["complete"] = len(missing) == 0

    out["merge_provenance"] = provenance
    if conflicts:
        out["merge_conflicts"] = conflicts

    out["extraction_method"] = (
        "merged"
        if ext_rec and any(provenance.get(f) == "structured_extraction" for f in MERGE_FIELDS)
        else b_method
    )
    return out


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    bridge_path = Path(args.bridge_meta).expanduser()
    if not bridge_path.exists():
        print(f"error: --bridge-meta not found: {bridge_path}", file=sys.stderr)
        return 2
    try:
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in --bridge-meta: {exc}", file=sys.stderr)
        return 2
    if not isinstance(bridge, list):
        print("error: --bridge-meta must be a JSON array", file=sys.stderr)
        return 2

    structured_path = Path(args.structured).expanduser()
    if not structured_path.exists():
        print(f"error: --structured not found: {structured_path}", file=sys.stderr)
        return 2
    try:
        structured = json.loads(structured_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in --structured: {exc}", file=sys.stderr)
        return 2
    if not isinstance(structured, list):
        print("error: --structured must be a JSON array", file=sys.stderr)
        return 2

    by_sha = {r.get("source_pdf_sha256"): r for r in structured if r.get("source_pdf_sha256")}

    merged: list[dict] = []
    matched_to_extraction = 0
    for b in bridge:
        sha = b.get("source_pdf_sha256")
        ext_rec = by_sha.get(sha)
        if ext_rec:
            matched_to_extraction += 1
        merged.append(merge_record(b, ext_rec))

    total = len(merged)
    fully_complete = sum(1 for r in merged if r.get("complete"))
    has_conflict = sum(1 for r in merged if r.get("merge_conflicts"))
    by_missing: dict[str, int] = {}
    for r in merged:
        for f in r.get("missing_fields", []):
            by_missing[f] = by_missing.get(f, 0) + 1

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] bridge_records          = {total}")
    print(f"[{mode}] structured_records      = {len(structured)}")
    print(f"[{mode}] matched_to_extraction   = {matched_to_extraction}/{total}  (sha256 join)")
    print(f"[{mode}] fully_complete (after)  = {fully_complete}/{total}")
    print(f"[{mode}] records_with_conflicts  = {has_conflict}")
    if by_missing:
        print(f"[{mode}] missing field counts (after merge):")
        for f, c in sorted(by_missing.items(), key=lambda x: -x[1]):
            print(f"  {f}: {c}")

    for r in merged[:5]:
        prov = r.get("merge_provenance", {})
        prov_brief = ",".join(f"{k}={v}" for k, v in prov.items()) or "-"
        print(f"  - {r.get('ticker','?'):14}  complete={str(r.get('complete')):5}  "
              f"missing={r.get('missing_fields')}  provenance=[{prov_brief}]")
    if len(merged) > 5:
        print(f"  ... (+{len(merged) - 5} more)")

    if args.dry_run:
        print("[DRY-RUN] no merged JSON written. Re-run with --apply.")
        print(f"[NOTE] merge version: {MERGE_VERSION}")
        return 0

    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote {out_path}")
    print("[NEXT] feed this file to build_report_estimate_v132.py --input <path>")
    print("[NEXT] downstream rolling_append should ONLY accept records with complete=true")
    print("       (--strict gate is OUT OF SCOPE for this PR; planned for a follow-up PR).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
