#!/usr/bin/env python3
"""
Phase 3 — Report estimate revision row builder (v1.3.2).

외부에서 추출한 PDF 메타 JSON을 받아 estimate_revision_history.csv 헤더 형식의
row를 생성한다. 본 스크립트는 row projection만 수행하며,
실제 CSV append는 stock_research/scripts/rolling_append.py 가 담당한다.

입력 형식 (--input):
    [
      {
        "ticker": "KRX:058470",
        "broker": "NH투자증권",
        "report_date": "2026-04-30",
        "old_target": 240000,
        "new_target": 260000,
        "horizon": "12M",
        "source_pdf_sha256": "..."
      }, ...
    ]

산출 형식 (apply 시 `<output-root>/<date>/estimate_revision_rows.json`):
    [
      {date, ticker, broker, old_target, new_target, direction, horizon, source_key},
      ...
    ]

direction: old→new 비교로 자동 ("up" | "down" | "flat")
source_key: phase3:report_estimate:v1.3.2 (+source_pdf_sha256[:12] 가 있으면 부착)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

DEFAULT_OUTPUT = "./output"
SOURCE_KEY_BASE = "phase3:report_estimate:v1.3.2"
HEADER = ["date", "ticker", "broker", "old_target", "new_target", "direction", "horizon", "source_key"]


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="parsed_meta.json path (list of dict)")
    p.add_argument("--output-root",
                   default=os.getenv("PHASE3_OUTPUT_ROOT") or DEFAULT_OUTPUT,
                   help=f"Output root (default: {DEFAULT_OUTPUT})")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="Target date YYYY-MM-DD (default: today). Used for output dir.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--apply", dest="dry_run", action="store_false")
    return p.parse_args(argv)


def derive_direction(old: object, new: object) -> str:
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return ""
    if n > o:
        return "up"
    if n < o:
        return "down"
    return "flat"


def project(meta: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for m in meta:
        sha_short = (m.get("source_pdf_sha256") or "")[:12]
        sk = SOURCE_KEY_BASE + (f"+{sha_short}" if sha_short else "")
        rows.append({
            "date": m.get("report_date") or m.get("date") or "",
            "ticker": m.get("ticker", ""),
            "broker": m.get("broker", ""),
            "old_target": str(m.get("old_target", "")),
            "new_target": str(m.get("new_target", "")),
            "direction": derive_direction(m.get("old_target"), m.get("new_target")),
            "horizon": m.get("horizon", ""),
            "source_key": sk,
        })
    return rows


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    in_path = Path(args.input).expanduser()
    if not in_path.exists():
        print(f"error: --input not found: {in_path}", file=sys.stderr)
        return 2
    try:
        meta = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(meta, list) or not all(isinstance(m, dict) for m in meta):
        print("error: --input must be a JSON array of objects", file=sys.stderr)
        return 2

    rows = project(meta)
    by_dir: dict[str, int] = {}
    for r in rows:
        by_dir[r["direction"] or "unknown"] = by_dir.get(r["direction"] or "unknown", 0) + 1

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] input  = {in_path}  rows_in={len(meta)}")
    print(f"[{mode}] output rows = {len(rows)}  by_direction={by_dir}")
    print(f"[{mode}] header order = {HEADER}")
    for r in rows[:5]:
        print(f"  - {r['date']} {r['ticker']} {r['broker']} {r['old_target']}→{r['new_target']} ({r['direction']})")
    if len(rows) > 5:
        print(f"  ... (+{len(rows) - 5} more)")

    if args.dry_run:
        print("[DRY-RUN] no estimate_revision_rows.json written. Re-run with --apply.")
        print("[NOTE] CSV append is NOT performed by this script.")
        print("       Use stock_research/scripts/rolling_append.py with the output JSON.")
        return 0

    out_root = Path(args.output_root).expanduser()
    out_dir = out_root / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "estimate_revision_rows.json"
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote {out_path}")
    print("[NEXT] feed this file to stock_research/scripts/rolling_append.py")
    print("       --csv <STOCK_RESEARCH_ROOT>/03_daily_reports/_rolling/estimate_revision_history.csv")
    print("       --rows <output_path> --dedupe-keys date,ticker,broker,source_key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
