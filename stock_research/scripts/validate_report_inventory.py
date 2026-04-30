#!/usr/bin/env python3
"""
REPORT_INVENTORY CSV의 각 행을 schemas/report_inventory.schema.json 기준으로 검증.

검증 항목:
  - 필수 컬럼 존재 (schema.required)
  - sha256 형식 (^[0-9a-f]{64}$)
  - storage_source / dedupe_method enum
  - duplicate_of 가 비어있지 않으면 같은 인벤토리 내 어떤 row의 id 와 매칭
  - id 가 sha256 첫 16자와 같은지 (warn)

`jsonschema` 패키지가 설치돼 있으면 정식 검증, 없으면 위 규칙을 직접 적용.

CLI: --stock-research-root, --inventory, --schema, --date, --dry-run
검증은 read-only이므로 --dry-run은 동작 동일.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List

REPO_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
DEFAULT_SCHEMA = REPO_SCHEMAS_DIR / "report_inventory.schema.json"

ALLOWED_STORAGE = {
    "wisereport", "stock_research_06_wise_report", "telegram_attachments",
    "daily_reports", "manual_upload", "unknown",
}
ALLOWED_DEDUPE = {"", "sha256", "fuzzy"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"))
    p.add_argument("--inventory", help="대상 CSV (생략 시 latest)")
    p.add_argument("--schema", default=str(DEFAULT_SCHEMA))
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


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def validate_with_jsonschema(rows: list[dict], schema: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return _basic_validate(rows, schema)
    validator = jsonschema.Draft202012Validator(schema)
    errs: list[str] = []
    for i, r in enumerate(rows):
        for e in sorted(validator.iter_errors(r), key=lambda e: list(e.absolute_path)):
            errs.append(f"row {i}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}")
    return errs


def _basic_validate(rows: list[dict], schema: dict) -> list[str]:
    errs: list[str] = []
    required = schema.get("required", [])
    for i, r in enumerate(rows):
        for k in required:
            if not r.get(k):
                errs.append(f"row {i}: missing required '{k}'")
        if r.get("sha256") and not SHA256_RE.match(r["sha256"]):
            errs.append(f"row {i}: invalid sha256")
        if r.get("storage_source") and r["storage_source"] not in ALLOWED_STORAGE:
            errs.append(f"row {i}: unknown storage_source '{r['storage_source']}'")
        if r.get("dedupe_method", "") not in ALLOWED_DEDUPE:
            errs.append(f"row {i}: invalid dedupe_method '{r['dedupe_method']}'")
    return errs


def cross_row_checks(rows: list[dict]) -> list[str]:
    errs: list[str] = []
    ids = {r.get("id", "") for r in rows if r.get("id")}
    for i, r in enumerate(rows):
        ref = r.get("duplicate_of", "")
        if ref and ref not in ids:
            errs.append(f"row {i}: duplicate_of='{ref}' not found in inventory")
        if r.get("id") and r.get("sha256") and not r["sha256"].startswith(r["id"]):
            errs.append(f"row {i}: id '{r['id']}' is not a prefix of sha256")
    return errs


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    inv = resolve_inventory(args)
    if not inv.exists():
        print(f"error: inventory not found: {inv}", file=sys.stderr)
        return 2
    schema_path = Path(args.schema).expanduser()
    if not schema_path.exists():
        print(f"error: schema not found: {schema_path}", file=sys.stderr)
        return 2
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    rows = read_rows(inv)

    errs = validate_with_jsonschema(rows, schema) + cross_row_checks(rows)
    print(f"[VALIDATE] inventory={inv}  rows={len(rows)}  errors={len(errs)}")
    for e in errs[:50]:
        print(f"  - {e}")
    if len(errs) > 50:
        print(f"  ... (+{len(errs) - 50} more)")
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
