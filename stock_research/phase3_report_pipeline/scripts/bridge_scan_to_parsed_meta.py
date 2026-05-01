#!/usr/bin/env python3
"""
Phase 3 — Bridge: scan_company.json + manual partial meta + ticker_map → parsed_meta.json.

Pure projection only. NO OCR, NO Vision API, NO PDF body parsing.
Missing fields are RECORDED, never guessed.

Inputs
  --scan-json    Path to scan_company.json from scan_wisereport_company.py
  --manual-meta  Path to manual partial parsed_meta JSON (list of dict; see
                 examples/parsed_meta.example.json)
  --ticker-map   Path to ticker_map CSV. Either rich schema
                 (company_name_kr,ticker,aliases,market,notes — PR #21) or
                 legacy (name_kr,ticker — PR #4) is auto-detected by
                 ticker_resolver.load_ticker_map_rows.
  --out          Output parsed_meta.json path

Output
  list of dict ready to feed build_report_estimate_v132.py:
    REQUIRED (per record): ticker, broker, report_date, old_target, new_target, horizon
    OPTIONAL filled by bridge: source_pdf_sha256, source_key, direction,
                               filename, missing_fields, bridge_matched_scan
  Manual record's `confidence`, `extraction_method`, `notes` are passed through.

Bridge rules
  * Match strategy (first hit wins): source_pdf_sha256 → filename → "[<korean name>]"
    substring inside scan filename (with PR #21 normalization on the name).
    Returns None if no match.
  * If matched and source_pdf_sha256 / filename are blank in the manual record,
    bridge fills them from the scan record.
  * `ticker` normalization: if value already matches KRX:NNNNNN it is kept as-is.
    Otherwise the bridge runs ticker_resolver.resolve over the value AND the
    filename's '[<name>]' bracket; this honors aliases (e.g. Samsung Electronics
    → 삼성전자 → KRX:005930) and entity-form prefixes ((주) / ㈜ / 주식회사).
    On miss the Korean name is preserved AND 'ticker_unmapped' is added to
    missing_fields.
  * `direction`: derived from old_target → new_target (up/down/flat). Bridge
    DOES NOT estimate target values themselves.
  * `source_key`: 'phase3:report_estimate:v1.3.2' (+ '+<sha256[:12]>' if known).
  * `missing_fields`: every required field that is null/empty after projection.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Local import — keeps bridge and resolver coupled by file location, no PYTHONPATH needed.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ticker_resolver  # noqa: E402

REQUIRED_FIELDS = ["ticker", "broker", "report_date", "old_target", "new_target", "horizon"]
SOURCE_KEY_BASE = "phase3:report_estimate:v1.3.2"
BRIDGE_VERSION = "phase3:bridge_scan_to_parsed_meta:v2"


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scan-json", required=True, help="scan_company.json path")
    p.add_argument("--manual-meta", required=True, help="manual partial parsed_meta JSON path")
    p.add_argument("--ticker-map", required=True,
                   help="ticker_map CSV path (rich PR #21 schema OR legacy 2-col schema)")
    p.add_argument("--out", required=True, help="output parsed_meta.json path")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) summarize only; no file written")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="materialize the output JSON")
    return p.parse_args(argv)


def load_ticker_map(path: Path) -> dict[str, str]:
    """Backed by ticker_resolver.load_ticker_map. Rich schema is validated;
    legacy schema is accepted with strict_market disabled."""
    rows = ticker_resolver.load_ticker_map_rows(path)
    is_legacy = all(not r.get("market") for r in rows)
    errors = ticker_resolver.validate_ticker_map(rows, strict_market=not is_legacy)
    if errors:
        raise ValueError(
            "ticker_map validation failed:\n  " + "\n  ".join(errors)
        )
    return ticker_resolver.build_lookup(rows)


def derive_direction(old: object, new: object) -> str:
    """Return 'up' / 'down' / 'flat' / 'unknown'.

    'unknown' is the canonical marker when either value is null or non-numeric;
    consumers must treat it as data-insufficient (NEVER a tradeable signal).
    """
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return "unknown"
    if n > o:
        return "up"
    if n < o:
        return "down"
    return "flat"


def is_krx(t: object) -> bool:
    return ticker_resolver.is_krx(t)


def find_scan_record(rec: dict, by_sha: dict, by_name: dict, scan: list[dict]) -> dict | None:
    sha = rec.get("source_pdf_sha256")
    if sha and sha in by_sha:
        return by_sha[sha]
    fn = rec.get("filename")
    if fn and fn in by_name:
        return by_name[fn]
    name = rec.get("ticker") or rec.get("stock_name_kr") or ""
    if isinstance(name, str) and name and not is_krx(name):
        norm = ticker_resolver.normalize_kr_company(name)
        for sr in scan:
            sr_fn = sr.get("filename") or ""
            if f"[{name}]" in sr_fn:
                return sr
            if norm and f"[{norm}]" in sr_fn:
                return sr
            # Compare against the bracket name (also normalized) so '(주)대덕전자'
            # in the manual rec finds '[대덕전자]' in the scan filename.
            sr_bracket = ticker_resolver.extract_bracketed_name(sr_fn)
            if norm and sr_bracket and norm == sr_bracket:
                return sr
    return None


def project_record(m: dict, by_sha: dict, by_name: dict, scan: list[dict], ticker_map: dict[str, str]) -> dict:
    rec = dict(m)

    scan_rec = find_scan_record(rec, by_sha, by_name, scan)
    rec["bridge_matched_scan"] = bool(scan_rec)
    if scan_rec:
        if not rec.get("source_pdf_sha256"):
            rec["source_pdf_sha256"] = scan_rec.get("sha256", "")
        if not rec.get("filename"):
            rec["filename"] = scan_rec.get("filename", "")

    t = rec.get("ticker", "") or ""
    if isinstance(t, str) and t and not is_krx(t):
        hit = ticker_resolver.resolve(
            t,
            filename=rec.get("filename") or "",
            ticker_map=ticker_map,
        )
        if hit is not None:
            rec["ticker"] = hit

    rec["direction"] = derive_direction(rec.get("old_target"), rec.get("new_target"))

    sha_short = (rec.get("source_pdf_sha256") or "")[:12]
    rec["source_key"] = f"{SOURCE_KEY_BASE}+{sha_short}" if sha_short else SOURCE_KEY_BASE

    missing: list[str] = []
    for f in REQUIRED_FIELDS:
        v = rec.get(f)
        if v in (None, "", [], {}):
            missing.append(f)
    if rec.get("ticker") and not is_krx(rec["ticker"]):
        missing.append("ticker_unmapped")
    rec["missing_fields"] = missing

    return rec


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    scan_path = Path(args.scan_json).expanduser()
    if not scan_path.exists():
        print(f"error: --scan-json not found: {scan_path}", file=sys.stderr)
        return 2
    try:
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in --scan-json: {exc}", file=sys.stderr)
        return 2
    if not isinstance(scan, list):
        print("error: --scan-json must be a JSON array", file=sys.stderr)
        return 2
    by_sha = {r.get("sha256"): r for r in scan if r.get("sha256")}
    by_name = {r.get("filename"): r for r in scan if r.get("filename")}

    manual_path = Path(args.manual_meta).expanduser()
    if not manual_path.exists():
        print(f"error: --manual-meta not found: {manual_path}", file=sys.stderr)
        return 2
    try:
        manual = json.loads(manual_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in --manual-meta: {exc}", file=sys.stderr)
        return 2
    if not isinstance(manual, list):
        print("error: --manual-meta must be a JSON array of objects", file=sys.stderr)
        return 2

    tmap_path = Path(args.ticker_map).expanduser()
    if not tmap_path.exists():
        print(f"error: --ticker-map not found: {tmap_path}", file=sys.stderr)
        return 2
    try:
        ticker_map = load_ticker_map(tmap_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = [project_record(m, by_sha, by_name, scan, ticker_map) for m in manual]

    total = len(out)
    matched = sum(1 for r in out if r.get("bridge_matched_scan"))
    fully_complete = sum(1 for r in out if not r.get("missing_fields"))
    by_missing: dict[str, int] = {}
    for r in out:
        for f in r.get("missing_fields", []):
            by_missing[f] = by_missing.get(f, 0) + 1

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] scan_records    = {len(scan)}")
    print(f"[{mode}] manual_records  = {total}")
    print(f"[{mode}] matched_to_scan = {matched}/{total}")
    print(f"[{mode}] fully_complete  = {fully_complete}/{total}  (no missing_fields)")
    print(f"[{mode}] ticker_map_size = {len(ticker_map)}")
    if by_missing:
        print(f"[{mode}] missing field counts:")
        for f, c in sorted(by_missing.items(), key=lambda x: -x[1]):
            print(f"  {f}: {c}")

    for r in out[:5]:
        ticker = r.get("ticker", "")
        miss = r.get("missing_fields", [])
        print(f"  - {r.get('report_date','?')}  {ticker:14}  "
              f"{r.get('broker',''):14}  "
              f"{r.get('old_target','')}→{r.get('new_target','')} ({r.get('direction','')})  "
              f"missing={miss}")
    if len(out) > 5:
        print(f"  ... (+{len(out) - 5} more)")

    if args.dry_run:
        print("[DRY-RUN] no parsed_meta.json written. Re-run with --apply.")
        print(f"[NOTE] bridge version: {BRIDGE_VERSION}")
        return 0

    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote {out_path}")
    print(f"[NEXT] feed this file to build_report_estimate_v132.py --input {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
