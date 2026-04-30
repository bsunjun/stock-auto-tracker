#!/usr/bin/env python3
"""
Phase 3 — WiseReport 기업 카테고리 PDF 스캔 (read-only, mobile-friendly).

`<report-root>/<DATE>/기업/*.pdf` 만을 빠르게 인덱싱한다.
PDF 파일은 절대 이동/복사/수정/삭제하지 않는다.

산출 (--apply 시): `<output-root>/<date>/scan_company.json`
records: [{path, filename, sha256, size_bytes, mtime, source_key}, ...]

CLI 표준 인자: --report-root, --output-root, --date, --dry-run/--apply
환경변수 fallback: PHASE3_REPORT_ROOT, WISE_REPORT_ROOT, PHASE3_OUTPUT_ROOT
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

DEFAULT_ROOT = "./data_inbox/wisereport"
DEFAULT_OUTPUT = "./output"
SOURCE_KEY = "phase3:scan_wisereport_company:v1"


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--report-root",
                   default=os.getenv("PHASE3_REPORT_ROOT") or os.getenv("WISE_REPORT_ROOT") or DEFAULT_ROOT,
                   help=f"WiseReport PDF root (default: {DEFAULT_ROOT})")
    p.add_argument("--output-root",
                   default=os.getenv("PHASE3_OUTPUT_ROOT") or DEFAULT_OUTPUT,
                   help=f"Output root (default: {DEFAULT_OUTPUT})")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="Target date YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) plan only; no files written")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="materialize scan_company.json under --output-root")
    return p.parse_args(argv)


def sha256_of(path: Path, buf_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


def scan(report_root: Path, date: str) -> list[dict]:
    target_dir = report_root / date / "기업"
    if not target_dir.exists():
        print(f"[scan] missing dir: {target_dir}", file=sys.stderr)
        return []
    records: list[dict] = []
    for pdf in sorted(target_dir.glob("*.pdf")):
        try:
            st = pdf.stat()
            digest = sha256_of(pdf)
        except Exception as exc:  # noqa: BLE001
            print(f"[scan] error on {pdf}: {exc}", file=sys.stderr)
            continue
        records.append({
            "path": str(pdf.resolve()),
            "filename": pdf.name,
            "sha256": digest,
            "size_bytes": str(st.st_size),
            "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
            "source_key": SOURCE_KEY,
        })
    return records


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    report_root = Path(args.report_root).expanduser()
    output_root = Path(args.output_root).expanduser()

    records = scan(report_root, args.date)

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] report_root = {report_root}")
    print(f"[{mode}] target      = {report_root / args.date / '기업'}")
    print(f"[{mode}] discovered  = {len(records)} pdf(s)")
    for r in records[:5]:
        print(f"  - {r['filename']}  sha256={r['sha256'][:12]}…  size={r['size_bytes']}")
    if len(records) > 5:
        print(f"  ... (+{len(records) - 5} more)")

    if args.dry_run:
        print("[DRY-RUN] no scan_company.json written. Re-run with --apply.")
        return 0

    out_dir = output_root / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "scan_company.json"
    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
