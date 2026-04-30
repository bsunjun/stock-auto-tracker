#!/usr/bin/env python3
"""
scan_<DATE>.json (또는 새로 발견한 PDF들)을 인벤토리 CSV로 빌드.

산출:
  <stock-research-root>/06_wise_report/inventory/REPORT_INVENTORY_<YYYYMMDD>.csv
  <stock-research-root>/06_wise_report/inventory/REPORT_INVENTORY_latest.csv  (복사본)

이 스크립트는 PDF 파일을 절대 이동/복사하지 않는다. 인덱싱(메타데이터 CSV) 만 생성.

CLI 표준 인자: --wisereport-root, --telegram-root, --stock-research-root, --source-root, --date, --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_report_sources import (  # noqa: E402
    SOURCE_KEY as SCAN_SOURCE_KEY,
    discover,
    build_record,
)

INVENTORY_HEADER = [
    "id", "sha256", "path", "filename", "size_bytes", "mtime", "discovered_at",
    "storage_source", "discovery_source", "date_dir", "category", "channel",
    "ticker", "broker", "title", "report_date", "duplicate_of", "dedupe_method", "source_key",
]

KNOWN_BROKERS = (
    "삼성증권", "NH투자증권", "KB증권", "미래에셋증권", "키움증권", "한국투자증권",
    "신한투자증권", "대신증권", "메리츠증권", "하나증권", "유진투자증권",
    "교보증권", "이베스트투자증권", "DB금융투자", "유안타증권", "현대차증권",
    "SK증권", "다올투자증권", "IBK투자증권", "BNK투자증권", "상상인증권",
    "WiseFn", "WISEfn", "에프앤가이드",
)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wisereport-root", default=os.getenv("WISE_REPORT_ROOT"))
    p.add_argument("--telegram-root", default=os.getenv("TELEGRAM_ROOT"))
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"))
    p.add_argument("--source-root", action="append", default=[])
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    p.add_argument("--scan", help="기존 scan_<date>.json 입력 (없으면 직접 스캔)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--apply", dest="dry_run", action="store_false")
    return p.parse_args(argv)


def enrich_metadata(rec: dict) -> dict:
    """파일명에서 ticker/broker/report_date/title을 보수적으로 추출."""
    name = rec["filename"]
    stem = Path(name).stem

    # report_date: YYYY-MM-DD / YYYY_MM_DD / YYYYMMDD (2000~2100 연도만 채택,
    # 앞뒤로 다른 숫자에 끼어 있는 경우 제외하여 6자리 종목코드와의 부분매치 회피)
    for pat in (
        r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)",
        r"(?<!\d)(\d{4})_(\d{2})_(\d{2})(?!\d)",
        r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)",
    ):
        m = re.search(pat, stem)
        if not m:
            continue
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 2000 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
            rec["report_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            break

    # ticker: KRX:NNNNNN 또는 6-digit code
    m = re.search(r"\bKRX[:_-]?(\d{6})\b", stem)
    if m:
        rec["ticker"] = f"KRX:{m.group(1)}"
    else:
        m = re.search(r"(?<![\d])(\d{6})(?![\d])", stem)
        if m:
            rec["ticker"] = f"KRX:{m.group(1)}"

    # broker: known list substring match
    for b in KNOWN_BROKERS:
        if b in stem:
            rec["broker"] = b
            break

    # title: stem with extracted parts removed (best-effort)
    title = stem
    for s in (rec.get("ticker", "").replace("KRX:", ""), rec.get("broker", ""), rec.get("report_date", "")):
        if s:
            title = title.replace(s, "")
    title = re.sub(r"[\[\]\(\)_\-\.]+", " ", title).strip()
    rec["title"] = title or stem
    return rec


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=INVENTORY_HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in INVENTORY_HEADER})


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    # 입력 행 확보: --scan 우선, 없으면 직접 스캔
    if args.scan:
        scan_path = Path(args.scan).expanduser()
        if not scan_path.exists():
            print(f"error: --scan not found: {scan_path}", file=sys.stderr)
            return 2
        rows = json.loads(scan_path.read_text(encoding="utf-8"))
    else:
        rows = []
        for p in discover(args):
            try:
                rows.append(build_record(p, args))
            except Exception as exc:  # noqa: BLE001
                print(f"[scan] error on {p}: {exc}", file=sys.stderr)

    enriched = [enrich_metadata(dict(r)) for r in rows]
    for r in enriched:
        if r.get("source_key") in ("", None):
            r["source_key"] = SCAN_SOURCE_KEY
        r["source_key"] = r["source_key"] + "+build_report_inventory:v1"

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] inventory rows: {len(enriched)}")
    by_storage: dict[str, int] = {}
    for r in enriched:
        by_storage[r["storage_source"]] = by_storage.get(r["storage_source"], 0) + 1
    for k, v in sorted(by_storage.items()):
        print(f"  {k}: {v}")

    if args.dry_run:
        print("[DRY-RUN] no CSV written. Re-run with --apply.")
        return 0

    if not args.stock_research_root:
        print("error: --stock-research-root required for --apply", file=sys.stderr)
        return 2
    inv_dir = Path(args.stock_research_root).expanduser() / "06_wise_report" / "inventory"
    out_csv = inv_dir / f"REPORT_INVENTORY_{args.date.replace('-', '')}.csv"
    latest_csv = inv_dir / "REPORT_INVENTORY_latest.csv"
    write_csv(enriched, out_csv)
    shutil.copyfile(out_csv, latest_csv)
    print(f"[APPLY] wrote {out_csv}")
    print(f"[APPLY] copied -> {latest_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
