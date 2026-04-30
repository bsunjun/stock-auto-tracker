#!/usr/bin/env python3
"""
History CSV에 신규 행을 idempotent하게 append.

원칙:
- 기본 dry-run. 변경 적용은 --apply 명시적으로.
- 같은 (dedupe-keys) 조합은 반복 실행해도 한 번만 들어간다.
- 입력 행의 컬럼 집합은 CSV 헤더와 정확히 일치해야 함.
- repo 내 templates/*.csv는 헤더만 두는 것이 원칙. 실제 누적은 Drive 측 동일 파일에 한다.
  --stock-research-root 가 주어지면 --csv는 그 경로 기준 상대로 해석한다.

CLI 표준 인자(전제):
    --stock-research-root, --date, --category, --dry-run
스크립트 고유 인자:
    --csv, --rows, --dedupe-keys
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"),
                   help="stock_research 루트 (Drive). --csv가 상대경로면 이 기준으로 해석.")
    p.add_argument("--csv", required=True,
                   help="대상 history CSV 경로 (절대 또는 stock-research-root 기준 상대)")
    p.add_argument("--rows", required=True,
                   help="신규 행을 담은 JSON 파일 경로 (list of dict)")
    p.add_argument("--dedupe-keys", default="date,ticker,source_key",
                   help="중복 차단 키 (콤마구분, 기본 'date,ticker,source_key')")
    p.add_argument("--date", default=None,
                   help="(선택) 입력 행을 이 날짜로 강제 필터")
    p.add_argument("--category", choices=("기업", "산업", "all"), default="all",
                   help="(선택) 입력 행에 'category' 컬럼이 있을 때만 의미. 기본 all")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(기본) 미리보기만 수행")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="실제 append 적용")
    return p.parse_args(argv)


def resolve_csv(args: argparse.Namespace) -> Path:
    p = Path(args.csv).expanduser()
    if p.is_absolute() or args.stock_research_root is None:
        return p
    return (Path(args.stock_research_root).expanduser() / p).resolve()


def read_existing(csv_path: Path) -> tuple[list[str], list[dict]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"target csv not found: {csv_path}")
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"csv has no header: {csv_path}")
        rows = list(reader)
        return list(reader.fieldnames), rows


def load_new_rows(rows_path: Path) -> list[dict]:
    data = json.loads(rows_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ValueError(f"rows file must be a JSON array of objects: {rows_path}")
    return data


def filter_rows(rows: list[dict], date: str | None, category: str) -> list[dict]:
    out = rows
    if date:
        out = [r for r in out if str(r.get("date")) == date]
    if category != "all":
        out = [r for r in out if "category" not in r or r["category"] == category]
    return out


def dedupe_key_tuple(row: dict, keys: list[str]) -> tuple:
    return tuple(str(row.get(k, "")) for k in keys)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    csv_path = resolve_csv(args)
    rows_path = Path(args.rows).expanduser()
    keys = [k.strip() for k in args.dedupe_keys.split(",") if k.strip()]
    if not keys:
        print("error: --dedupe-keys must list at least one column", file=sys.stderr)
        return 2

    header, existing = read_existing(csv_path)
    missing_keys = [k for k in keys if k not in header]
    if missing_keys:
        print(f"error: dedupe keys not in csv header: {missing_keys} (header={header})", file=sys.stderr)
        return 2

    incoming = filter_rows(load_new_rows(rows_path), args.date, args.category)

    bad = [r for r in incoming if set(r.keys()) - set(header)]
    if bad:
        sample = list(set(bad[0].keys()) - set(header))
        print(f"error: incoming rows have columns not in header: {sample}", file=sys.stderr)
        return 2

    seen: set[tuple] = {dedupe_key_tuple(r, keys) for r in existing}
    to_add: list[dict] = []
    skipped = 0
    for r in incoming:
        k = dedupe_key_tuple(r, keys)
        if k in seen:
            skipped += 1
            continue
        seen.add(k)
        to_add.append(r)

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    before_lines = len(existing)
    print(f"[{mode}] csv = {csv_path}")
    print(f"[{mode}] dedupe-keys = {keys}")
    print(f"[{mode}] incoming = {len(incoming)}, skipped(dup) = {skipped}, to_add = {len(to_add)}")
    print(f"[{mode}] before lines = {before_lines}, after lines = {before_lines + (0 if args.dry_run else len(to_add))}")

    if args.dry_run or not to_add:
        if args.dry_run:
            print("[DRY-RUN] no changes written. Re-run with --apply to append.")
        return 0

    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        for r in to_add:
            writer.writerow({k: r.get(k, "") for k in header})
    print(f"[APPLY] appended {len(to_add)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
