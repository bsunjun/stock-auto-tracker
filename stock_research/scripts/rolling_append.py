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

--strict-estimate (PR #8):
    build_report_estimate_v132.py --strict 가 만든 estimate_revision_rows.json
    전용 검증 모드. 다음을 강제한다:
      * direct_trade_signal == False 인 row 만 통과
      * ticker 가 'KRX:' 형식
      * direction ∈ {up, down, flat}
      * old_target / new_target 비어있지 않음
      * source_key 존재
      * reject_reasons 같은 필드가 들어있으면 (즉 rejected_rows.json 형태)
        무조건 거부 — rolling history 에는 rejected row 가 들어가서는 안 된다.
    검증 실패 row 는 reject_reasons 와 함께 dry-run 출력에만 표시되고
    history 에 append 되지 않는다. 검증 통과 row 는 CSV 헤더 컬럼만
    남기고 audit 전용 컬럼 (source_pdf_sha256, direct_trade_signal) 은
    write 시점에 자연스럽게 drop 된다.
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
    p.add_argument("--strict-estimate", dest="strict_estimate", action="store_true",
                   default=False,
                   help="estimate_revision_rows.json (build_report_estimate_v132.py --strict "
                        "산출물) 전용 검증 모드. 자세한 내용은 module docstring 참조.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(기본) 미리보기만 수행")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="실제 append 적용")
    return p.parse_args(argv)


# Audit-only columns produced by build_report_estimate_v132.py --strict. They
# are tolerated in --strict-estimate input, used for validation, then dropped
# before write so the existing CSV-header-equality contract is preserved.
STRICT_ESTIMATE_AUDIT_COLUMNS = {"source_pdf_sha256", "direct_trade_signal"}

# Fields that, if present, indicate the input is a rejected_rows.json shape
# (or otherwise carries reject metadata) — never append these to history.
STRICT_ESTIMATE_REJECT_MARKERS = ("reject_reasons", "missing_fields")

VALID_DIRECTIONS = ("up", "down", "flat")


def _row_is_blank(v: object) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return False


def validate_strict_estimate_row(row: dict) -> list[str]:
    """Return a list of reject reasons for a strict-estimate row. Empty = ok.

    Order is stable so summary counts are deterministic.
    """
    reasons: list[str] = []

    # Hard guard: rejected_rows.json shape must never be appended.
    for marker in STRICT_ESTIMATE_REJECT_MARKERS:
        if marker in row:
            reasons.append(f"has_{marker}")

    dts = row.get("direct_trade_signal")
    # Accept only the explicit boolean False. Missing → reject (defends
    # against pre-PR#7 outputs that don't carry the field).
    if dts is not False:
        reasons.append("direct_trade_signal_not_false")

    ticker = row.get("ticker")
    if not (isinstance(ticker, str) and ticker.startswith("KRX:") and len(ticker) > len("KRX:")):
        reasons.append("ticker_not_krx")

    direction = row.get("direction")
    if direction not in VALID_DIRECTIONS:
        reasons.append("direction_invalid")

    if _row_is_blank(row.get("old_target")):
        reasons.append("old_target_blank")
    if _row_is_blank(row.get("new_target")):
        reasons.append("new_target_blank")

    if _row_is_blank(row.get("source_key")):
        reasons.append("source_key_blank")

    return reasons


def split_strict_estimate(
    incoming: list[dict],
    header: list[str],
) -> tuple[list[dict], list[dict], dict[str, int]]:
    """Validate strict-estimate rows.

    Returns (clean_rows, rejected_with_reasons, reject_reason_counts).
    `clean_rows` are header-aligned dicts (audit columns dropped) ready for
    the dedupe pass.
    """
    clean: list[dict] = []
    rejected: list[dict] = []
    reasons_counter: dict[str, int] = {}

    for row in incoming:
        # Tolerate audit-only columns; flag anything else outside the header.
        extra = (set(row.keys()) - set(header)) - STRICT_ESTIMATE_AUDIT_COLUMNS
        # Reject markers should drive the validator, not the schema check —
        # they're surfaced as their own reject reason below.
        extra -= set(STRICT_ESTIMATE_REJECT_MARKERS)

        local_reasons: list[str] = []
        if extra:
            local_reasons.append(f"unknown_columns:{sorted(extra)}")

        local_reasons.extend(validate_strict_estimate_row(row))

        if local_reasons:
            for r in local_reasons:
                # Bucket the unknown_columns variants under one stable key.
                bucket = "unknown_columns" if r.startswith("unknown_columns:") else r
                reasons_counter[bucket] = reasons_counter.get(bucket, 0) + 1
            rejected.append({
                "ticker": row.get("ticker", ""),
                "broker": row.get("broker", ""),
                "date": row.get("date", ""),
                "direction": row.get("direction", ""),
                "source_key": row.get("source_key", ""),
                "reject_reasons": local_reasons,
            })
            continue

        clean.append({k: row.get(k, "") for k in header})

    return clean, rejected, reasons_counter


def resolve_csv(args: argparse.Namespace) -> Path:
    p = Path(args.csv).expanduser()
    if p.is_absolute() or args.stock_research_root is None:
        return p
    return (Path(args.stock_research_root).expanduser() / p).resolve()


def _is_repo_templates_path(p: Path) -> bool:
    """True iff `p` resolves to a location under any `stock_research/templates/`.

    The repo's `stock_research/templates/*.csv` files hold only headers — real
    rolling history lives outside the repo (Drive). Apply into templates would
    pollute the source tree, so we hard-refuse it (dry-run is still allowed).
    """
    try:
        parts = p.resolve(strict=False).parts
    except (OSError, RuntimeError):
        parts = p.parts
    for i in range(len(parts) - 1):
        if parts[i] == "stock_research" and parts[i + 1] == "templates":
            return True
    return False


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

    # Safety guard (PR #8 hardening): repo templates are header-only and meant
    # for dry-run / schema validation. Refuse --apply against any path under
    # stock_research/templates/.
    if not args.dry_run and _is_repo_templates_path(csv_path):
        print(
            "error: refusing to --apply into stock_research/templates; "
            "use a real rolling csv path outside templates",
            file=sys.stderr,
        )
        return 2

    header, existing = read_existing(csv_path)
    missing_keys = [k for k in keys if k not in header]
    if missing_keys:
        print(f"error: dedupe keys not in csv header: {missing_keys} (header={header})", file=sys.stderr)
        return 2

    incoming = filter_rows(load_new_rows(rows_path), args.date, args.category)

    rejected: list[dict] = []
    reject_reason_counts: dict[str, int] = {}
    if args.strict_estimate:
        incoming, rejected, reject_reason_counts = split_strict_estimate(incoming, header)
    else:
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
    if args.strict_estimate:
        print(f"[{mode}] strict-estimate = ON")
        print(f"[{mode}] validated = {len(incoming)}, rejected = {len(rejected)}")
        if reject_reason_counts:
            print(f"[{mode}] reject_reason_counts:")
            for reason, count in sorted(reject_reason_counts.items(), key=lambda kv: -kv[1]):
                print(f"  {reason}: {count}")
        for r in rejected[:5]:
            print(f"  ! {r.get('date','')} {r.get('ticker','')} reasons={r['reject_reasons']}")
        if len(rejected) > 5:
            print(f"  ... (+{len(rejected) - 5} more rejected)")
    print(f"[{mode}] incoming = {len(incoming)}, skipped(dup) = {skipped}, to_add = {len(to_add)}")
    print(f"[{mode}] before lines = {before_lines}, after lines = {before_lines + (0 if args.dry_run else len(to_add))}")

    # Hard invariant (PR #8): nothing slips through with the audit columns
    # set incorrectly or with a reject marker. This is redundant with the
    # validator above but cheap to verify before writing.
    if args.strict_estimate and to_add:
        for r in to_add:
            if any(m in r for m in STRICT_ESTIMATE_REJECT_MARKERS):
                print(f"error: invariant violated — to_add row carries reject marker: {r}",
                      file=sys.stderr)
                return 3

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
