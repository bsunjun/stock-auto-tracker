#!/usr/bin/env python3
"""
PBKR 산출 JSON을 schemas/ 기준으로 검증.

사용 방식:
1) 단일 파일: --pack <json> --schema <schema.json>
2) 디렉토리 일괄: --dir <dir>  (파일명 패턴으로 schema 자동 매핑)

자동 매핑 규칙 (--dir 모드):
    *candidate_score_pack*.json   ->  candidate_score_pack.schema.json
    *audit_pack*.json             ->  audit_pack.schema.json
    *news_pack*.json              ->  news_pack.schema.json
    *trade_ticket*.json           ->  trade_ticket.schema.json
    *rolling_memory*.json         ->  rolling_memory.schema.json

`jsonschema` 패키지가 설치돼 있으면 정식 검증, 없으면 최소 구조 검증(필수 키 존재만)으로 graceful fallback.

CLI 표준 인자(전제):
    --stock-research-root, --date, --category, --dry-run
검증은 read-only이므로 --dry-run은 동작 변화 없음(호환을 위해 수용).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable, List

REPO_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

PATTERN_TO_SCHEMA = (
    ("candidate_score_pack", "candidate_score_pack.schema.json"),
    ("audit_pack", "audit_pack.schema.json"),
    ("news_pack", "news_pack.schema.json"),
    ("trade_ticket", "trade_ticket.schema.json"),
    ("rolling_memory", "rolling_memory.schema.json"),
)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stock-research-root", default=os.getenv("STOCK_RESEARCH_ROOT"))
    p.add_argument("--date", default=None, help="(선택) --dir 내 파일명/경로에 이 날짜가 포함된 항목만 검사")
    p.add_argument("--category", choices=("기업", "산업", "all"), default="all", help="(선택) 호환용")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(기본) read-only이므로 동작 동일. 호환 플래그.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="호환용. 검증은 read-only이므로 결과 동일.")
    p.add_argument("--pack", help="검증할 단일 JSON 경로")
    p.add_argument("--schema", help="--pack과 함께 사용할 schema JSON 경로 (생략 시 파일명에서 추론)")
    p.add_argument("--dir", dest="dir_", help="이 디렉토리 내 .json을 일괄 검증")
    return p.parse_args(argv)


def guess_schema(name: str) -> Path | None:
    lower = name.lower()
    for needle, fname in PATTERN_TO_SCHEMA:
        if needle in lower:
            return REPO_SCHEMAS_DIR / fname
    return None


def load_json(p: Path) -> object:
    return json.loads(p.read_text(encoding="utf-8"))


def validate_with_jsonschema(instance: object, schema: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return _basic_validate(instance, schema)
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))]


def _basic_validate(instance: object, schema: dict) -> list[str]:
    """jsonschema가 없을 때의 최소 검증: 최상위 required 키 존재."""
    errs: list[str] = []
    if not isinstance(instance, dict):
        return ["<root>: expected object"]
    for k in schema.get("required", []):
        if k not in instance:
            errs.append(f"<root>: missing required key '{k}'")
    return errs


def iter_pack_files(root: Path, date: str | None) -> Iterable[Path]:
    for f in sorted(root.rglob("*.json")):
        if date and date not in str(f):
            continue
        if guess_schema(f.name) is None:
            continue
        yield f


def validate_one(pack_path: Path, schema_path: Path) -> tuple[bool, list[str]]:
    instance = load_json(pack_path)
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        return False, ["schema is not an object"]
    errs = validate_with_jsonschema(instance, schema)
    return (len(errs) == 0), errs


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    targets: list[tuple[Path, Path]] = []
    if args.pack:
        pack = Path(args.pack).expanduser()
        if args.schema:
            schema = Path(args.schema).expanduser()
        else:
            schema = guess_schema(pack.name) or Path()
        if not schema.exists():
            print(f"error: schema not found for {pack.name} (try --schema)", file=sys.stderr)
            return 2
        targets.append((pack, schema))
    elif args.dir_:
        d = Path(args.dir_).expanduser()
        if not d.exists():
            print(f"error: --dir not found: {d}", file=sys.stderr)
            return 2
        for f in iter_pack_files(d, args.date):
            schema = guess_schema(f.name)
            if schema is None or not schema.exists():
                continue
            targets.append((f, schema))
    else:
        print("error: provide --pack or --dir", file=sys.stderr)
        return 2

    if not targets:
        print("[VALIDATE] no matching files found.")
        return 0

    pass_n = fail_n = 0
    print(f"[VALIDATE] {len(targets)} file(s) to check")
    for pack, schema in targets:
        ok, errs = validate_one(pack, schema)
        if ok:
            pass_n += 1
            print(f"  PASS  {pack}  (schema: {schema.name})")
        else:
            fail_n += 1
            print(f"  FAIL  {pack}  (schema: {schema.name})")
            for e in errs:
                print(f"        - {e}")
    print(f"[VALIDATE] summary: pass={pass_n}, fail={fail_n}")
    return 0 if fail_n == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
