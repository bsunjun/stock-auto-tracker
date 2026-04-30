#!/usr/bin/env python3
"""
REPORT_INVENTORY CSV에서 중복 행을 식별하여 duplicate_of 컬럼을 채운다.

중복 판정:
  1차 — sha256 동일 (가장 강한 신호; dedupe_method='sha256')
  2차 — (ticker, broker, report_date) 모두 일치하면서 title 유사도 >= 0.85
        (dedupe_method='fuzzy')

canonical 행 선정 (그룹 내 1개만 비-중복):
  - storage_source 우선순위(낮을수록 정본):
      stock_research_06_wise_report < daily_reports < wisereport < telegram_attachments < manual_upload < unknown
  - 동순위면 mtime이 가장 이른 행
  - 그래도 동률이면 path 사전순

실제 PDF 파일은 절대 이동/삭제하지 않는다. CSV 인덱싱만 수정한다.

CLI: --stock-research-root, --inventory, --date, --dry-run
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import List

CANONICAL_RANK = {
    "stock_research_06_wise_report": 0,
    "daily_reports": 1,
    "wisereport": 2,
    "telegram_attachments": 3,
    "manual_upload": 4,
    "unknown": 5,
}
FUZZY_THRESHOLD = 0.85


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"))
    p.add_argument("--inventory", help="대상 inventory CSV (생략 시 latest)")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--apply", dest="dry_run", action="store_false")
    return p.parse_args(argv)


def resolve_inventory(args: argparse.Namespace) -> Path:
    if args.inventory:
        return Path(args.inventory).expanduser()
    if not args.stock_research_root:
        raise SystemExit("error: provide --inventory or --stock-research-root")
    inv_dir = Path(args.stock_research_root).expanduser() / "06_wise_report" / "inventory"
    dated = inv_dir / f"REPORT_INVENTORY_{args.date.replace('-', '')}.csv"
    return dated if dated.exists() else inv_dir / "REPORT_INVENTORY_latest.csv"


def read_inventory(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def canonical_sort_key(r: dict) -> tuple:
    return (
        CANONICAL_RANK.get(r.get("storage_source", "unknown"), 99),
        r.get("mtime", "9999"),
        r.get("path", ""),
    )


def mark_sha256_duplicates(rows: list[dict]) -> int:
    by_hash: dict[str, list[dict]] = {}
    for r in rows:
        h = r.get("sha256", "")
        if not h:
            continue
        by_hash.setdefault(h, []).append(r)
    marked = 0
    for h, group in by_hash.items():
        if len(group) <= 1:
            continue
        group.sort(key=canonical_sort_key)
        canon = group[0]
        canon["duplicate_of"] = ""
        canon["dedupe_method"] = canon.get("dedupe_method", "")
        for r in group[1:]:
            if r.get("duplicate_of"):
                continue
            r["duplicate_of"] = canon["id"]
            r["dedupe_method"] = "sha256"
            marked += 1
    return marked


def mark_fuzzy_duplicates(rows: list[dict]) -> int:
    # 그룹: 동일 (ticker, broker, report_date) — 셋 모두 비어있지 않음
    eligible = [r for r in rows if not r.get("duplicate_of")
                and r.get("ticker") and r.get("broker") and r.get("report_date")]
    groups: dict[tuple, list[dict]] = {}
    for r in eligible:
        groups.setdefault((r["ticker"], r["broker"], r["report_date"]), []).append(r)
    marked = 0
    for _, group in groups.items():
        if len(group) <= 1:
            continue
        group.sort(key=canonical_sort_key)
        canon = group[0]
        for r in group[1:]:
            ratio = SequenceMatcher(None, canon.get("title", ""), r.get("title", "")).ratio()
            if ratio >= FUZZY_THRESHOLD:
                r["duplicate_of"] = canon["id"]
                r["dedupe_method"] = "fuzzy"
                marked += 1
    return marked


def write_inventory(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    inv_path = resolve_inventory(args)
    if not inv_path.exists():
        print(f"error: inventory not found: {inv_path}", file=sys.stderr)
        return 2
    header, rows = read_inventory(inv_path)
    if "duplicate_of" not in header or "dedupe_method" not in header:
        print("error: inventory missing duplicate_of/dedupe_method columns", file=sys.stderr)
        return 2

    before_dup = sum(1 for r in rows if r.get("duplicate_of"))
    sha_marked = mark_sha256_duplicates(rows)
    fuzzy_marked = mark_fuzzy_duplicates(rows)
    after_dup = sum(1 for r in rows if r.get("duplicate_of"))

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] inventory: {inv_path}")
    print(f"[{mode}] rows={len(rows)}  duplicates_before={before_dup}  +sha256={sha_marked}  +fuzzy={fuzzy_marked}  duplicates_after={after_dup}")

    if args.dry_run:
        for r in [r for r in rows if r.get("dedupe_method") in ("sha256", "fuzzy")][:8]:
            print(f"  - dup id={r['id']} -> {r['duplicate_of']}  via {r['dedupe_method']}  path={r['path']}")
        print("[DRY-RUN] no CSV written. Re-run with --apply.")
        return 0

    write_inventory(inv_path, header, rows)
    latest = inv_path.parent / "REPORT_INVENTORY_latest.csv"
    if inv_path != latest:
        write_inventory(latest, header, rows)
    print(f"[APPLY] wrote {inv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
