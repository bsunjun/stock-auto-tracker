#!/usr/bin/env python3
"""
다중 소스에서 PDF 리포트를 발견(스캔)하여 정규화된 레코드를 산출.

실제 파일 이동/삭제는 절대 하지 않는다. read-only 스캔만 수행.

스캔 후보:
  1) <wisereport-root>/<DATE>/{기업|산업}/*.pdf
  2) <wisereport-root>/<DATE>/*.pdf  (loose)
  3) <wisereport-root>/*.pdf         (loose at root)
  4) <stock-research-root>/06_wise_report/**/*.pdf
  5) <telegram-root>/<DATE>/<channel>/attachments/*.pdf
     또는 <stock-research-root>/01_raw_telegram/<DATE>/<channel>/attachments/*.pdf
  6) <stock-research-root>/03_daily_reports/<DATE>/**/*.pdf
  7) --source-root 로 추가된 임의 경로 (반복 가능)

산출:
  --apply 가 주어지면 <stock-research-root>/06_wise_report/inventory/scan_<DATE>.json 에 저장.
  기본은 dry-run: stdout 요약만 출력.

CLI 표준 인자: --wisereport-root, --telegram-root, --stock-research-root, --date, --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

SOURCE_KEY = "scan:scan_report_sources:v1"


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wisereport-root", default=os.getenv("WISE_REPORT_ROOT"))
    p.add_argument("--telegram-root", default=os.getenv("TELEGRAM_ROOT"))
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"))
    p.add_argument("--source-root", action="append", default=[],
                   help="추가 스캔 루트 (반복 가능)")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="대상 날짜 YYYY-MM-DD (기본: 오늘)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--apply", dest="dry_run", action="store_false")
    return p.parse_args(argv)


def sha256_of(path: Path, buf_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(buf_size):
            h.update(chunk)
    return h.hexdigest()


def classify(path: Path, args: argparse.Namespace) -> tuple[str, str, str, str]:
    """Return (storage_source, discovery_source, date_dir, category, channel) — channel may be ''."""
    s = str(path.resolve())
    parts = path.resolve().parts

    def under(root_str: str | None) -> bool:
        if not root_str:
            return False
        try:
            return Path(root_str).expanduser().resolve() in path.resolve().parents
        except Exception:
            return False

    sr = args.stock_research_root
    if under(args.wisereport_root):
        rel = path.resolve().relative_to(Path(args.wisereport_root).expanduser().resolve())
        rel_parts = rel.parts
        date_dir = rel_parts[0] if rel_parts and _looks_like_date(rel_parts[0]) else ""
        category = rel_parts[1] if len(rel_parts) >= 2 and rel_parts[1] in ("기업", "산업") else ""
        sub = "/".join(rel_parts[:-1]) or "loose"
        return "wisereport", f"wisereport/{sub}", date_dir, category, ""
    if sr and under(f"{sr}/06_wise_report"):
        return "stock_research_06_wise_report", "manual_06_wise_report", "", "", ""
    if sr and under(f"{sr}/03_daily_reports"):
        rel = path.resolve().relative_to(Path(sr).expanduser().resolve() / "03_daily_reports")
        date_dir = rel.parts[0] if rel.parts and _looks_like_date(rel.parts[0]) else ""
        return "daily_reports", f"daily_reports/{date_dir}".rstrip("/"), date_dir, "", ""
    # telegram detection: dedicated --telegram-root, or under <sr>/01_raw_telegram
    tg_root = args.telegram_root or (f"{sr}/01_raw_telegram" if sr else None)
    if tg_root and under(tg_root):
        rel = path.resolve().relative_to(Path(tg_root).expanduser().resolve())
        rel_parts = rel.parts
        date_dir = rel_parts[0] if rel_parts and _looks_like_date(rel_parts[0]) else ""
        channel = rel_parts[1] if len(rel_parts) >= 2 else ""
        return "telegram_attachments", f"telegram/{date_dir}/{channel}/attachments".strip("/"), date_dir, "", channel
    return "unknown", "source_root", "", "", ""


def _looks_like_date(s: str) -> bool:
    return len(s) == 10 and s[4] == "-" and s[7] == "-"


def discover(args: argparse.Namespace) -> Iterable[Path]:
    seen: set[Path] = set()

    def walk(root: Path):
        if not root.exists():
            print(f"[discover] missing: {root}", file=sys.stderr)
            return
        for p in root.rglob("*.pdf"):
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            yield rp

    roots: list[Path] = []
    if args.wisereport_root:
        wr = Path(args.wisereport_root).expanduser()
        for sub in (wr / args.date / "기업", wr / args.date / "산업", wr / args.date, wr):
            roots.append(sub)
    if args.stock_research_root:
        sr = Path(args.stock_research_root).expanduser()
        roots.append(sr / "06_wise_report")
        roots.append(sr / "03_daily_reports" / args.date)
        if not args.telegram_root:
            roots.append(sr / "01_raw_telegram" / args.date)
    if args.telegram_root:
        roots.append(Path(args.telegram_root).expanduser() / args.date)
    for s in args.source_root:
        roots.append(Path(s).expanduser())

    for r in roots:
        # Use shallow glob for top-of-root non-recursive cases to avoid double counting
        if r.exists() and r.is_dir():
            for p in walk(r):
                yield p


def build_record(path: Path, args: argparse.Namespace) -> dict:
    digest = sha256_of(path)
    storage_source, discovery_source, date_dir, category, channel = classify(path, args)
    st = path.stat()
    return {
        "id": digest[:16],
        "sha256": digest,
        "path": str(path.resolve()),
        "filename": path.name,
        "size_bytes": str(st.st_size),
        "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
        "discovered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "storage_source": storage_source,
        "discovery_source": discovery_source,
        "date_dir": date_dir,
        "category": category,
        "channel": channel,
        "ticker": "",
        "broker": "",
        "title": path.stem,
        "report_date": "",
        "duplicate_of": "",
        "dedupe_method": "",
        "source_key": SOURCE_KEY,
    }


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    records: list[dict] = []
    for p in discover(args):
        try:
            records.append(build_record(p, args))
        except Exception as exc:  # noqa: BLE001
            print(f"[scan] error on {p}: {exc}", file=sys.stderr)

    by_source: dict[str, int] = {}
    for r in records:
        by_source[r["storage_source"]] = by_source.get(r["storage_source"], 0) + 1
    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] date={args.date}  total_pdfs={len(records)}")
    for k, v in sorted(by_source.items()):
        print(f"  {k}: {v}")

    if args.dry_run:
        for r in records[:8]:
            print(f"  - [{r['storage_source']}] {r['path']}  sha256={r['sha256'][:12]}…")
        if len(records) > 8:
            print(f"  ... (+{len(records) - 8} more)")
        print("[DRY-RUN] no scan_<date>.json written. Re-run with --apply.")
        return 0

    if not args.stock_research_root:
        print("error: --stock-research-root required for --apply", file=sys.stderr)
        return 2
    out_dir = Path(args.stock_research_root).expanduser() / "06_wise_report" / "inventory"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"scan_{args.date}.json"
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
