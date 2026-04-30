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
        "source_pdf_sha256": "...",
        "complete": true,
        "missing_fields": [],
        "direction": "up"
      }, ...
    ]

산출 형식 (apply 시 `<output-root>/<date>/estimate_revision_rows.json`):
    [
      {date, ticker, broker, old_target, new_target, direction, horizon,
       source_key, source_pdf_sha256, direct_trade_signal=false},
      ...
    ]

direction: 입력에 명시된 값 우선, 없으면 old→new 비교로 자동
           ("up" | "down" | "flat" | "unknown")
source_key: phase3:report_estimate:v1.3.2 (+source_pdf_sha256[:12] 가 있으면 부착)

--strict (PR #7):
    merge_meta 산출물 중 다운스트림 history CSV에 안전하게 흘려도 되는
    row만 estimate_revision_rows.json 으로 projection 한다.
    제외된 row는 estimate_revision_rejected_rows.json 에 reject_reasons 와 함께
    별도 보존된다 (drop 하지 않음). 기본값은 False — 기존 호환성 유지.

본 스크립트는 매매 신호를 생성하지 않는다. accepted row 의
`direct_trade_signal` 은 항상 false 이며 summary 의
`direct_trade_signal_all_false` 도 항상 true 이어야 한다.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

DEFAULT_OUTPUT = "./output"
SOURCE_KEY_BASE = "phase3:report_estimate:v1.3.2"
HEADER = ["date", "ticker", "broker", "old_target", "new_target", "direction", "horizon", "source_key"]

VALID_DIRECTIONS = {"up", "down", "flat"}


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True, help="parsed_meta.json path (list of dict)")
    p.add_argument("--output-root",
                   default=os.getenv("PHASE3_OUTPUT_ROOT") or DEFAULT_OUTPUT,
                   help=f"Output root (default: {DEFAULT_OUTPUT})")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="Target date YYYY-MM-DD (default: today). Used for output dir.")
    p.add_argument("--strict", dest="strict", action="store_true", default=False,
                   help="Reject rows that are not safely complete; keep them in "
                        "estimate_revision_rejected_rows.json with reject_reasons. "
                        "Default off for backward compatibility.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--apply", dest="dry_run", action="store_false")
    return p.parse_args(argv)


def derive_direction(old: object, new: object) -> str:
    """Return 'up' / 'down' / 'flat' / 'unknown' (data-insufficient)."""
    try:
        o, n = float(old), float(new)
    except (TypeError, ValueError):
        return "unknown"
    if n > o:
        return "up"
    if n < o:
        return "down"
    return "flat"


def _stringify_target(v: object) -> str:
    """Stringify a target value; null/None becomes empty string (not the literal 'None')."""
    if v is None:
        return ""
    return str(v)


def _is_numeric(v: object) -> bool:
    """True iff v is a finite number or a string that parses to one.

    NaN / +inf / -inf are rejected — silently letting them through would
    poison downstream direction comparisons (NaN != NaN; inf > finite).
    """
    if v is None or isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        try:
            return math.isfinite(float(v))
        except (TypeError, ValueError):
            return False
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if not s:
            return False
        try:
            return math.isfinite(float(s))
        except ValueError:
            return False
    return False


def _is_krx_ticker(t: object) -> bool:
    return isinstance(t, str) and t.startswith("KRX:") and len(t) > len("KRX:")


def _record_date(m: dict) -> str:
    return m.get("report_date") or m.get("date") or ""


def evaluate_strict(m: dict, direction: str) -> list[str]:
    """Return list of reject reasons for record `m`. Empty list = accept.

    Order is stable so summary counts are deterministic.
    """
    reasons: list[str] = []

    if m.get("complete") is not True:
        reasons.append("complete_not_true")

    # missing_fields: tolerate the canonical empty/absent shapes (`[]`, `None`,
    # field absent). Any other truthy shape — non-empty list, non-empty string,
    # non-empty dict, anything — is treated as "merge_meta flagged something",
    # so reject. Defensive against producers that emit `"target_parse_failed"`
    # as a bare string instead of `["target_parse_failed"]`.
    mf = m.get("missing_fields", None)
    if mf is not None and mf != []:
        reasons.append("missing_fields_nonempty")

    if direction == "unknown":
        reasons.append("direction_unknown")

    if not _is_numeric(m.get("old_target")):
        reasons.append("old_target_invalid")
    if not _is_numeric(m.get("new_target")):
        reasons.append("new_target_invalid")

    if not _is_krx_ticker(m.get("ticker")):
        reasons.append("ticker_not_krx")

    if not (isinstance(m.get("broker"), str) and m.get("broker").strip()):
        reasons.append("broker_empty")

    if not _record_date(m).strip():
        reasons.append("date_empty")

    horizon = m.get("horizon")
    if not (isinstance(horizon, str) and horizon.strip()):
        reasons.append("horizon_empty")

    return reasons


def project_accepted(m: dict, direction: str) -> dict:
    sha = m.get("source_pdf_sha256") or ""
    sha_short = sha[:12]
    sk = SOURCE_KEY_BASE + (f"+{sha_short}" if sha_short else "")
    return {
        "date": _record_date(m),
        "ticker": m.get("ticker", ""),
        "broker": m.get("broker", ""),
        "old_target": _stringify_target(m.get("old_target")),
        "new_target": _stringify_target(m.get("new_target")),
        "direction": direction,
        "horizon": m.get("horizon", ""),
        "source_key": sk,
        "source_pdf_sha256": sha,
        # Phase3 산출물은 추정치/실적 모멘텀 입력일 뿐, 매매 신호가 아니다.
        "direct_trade_signal": False,
    }


def project_rejected(m: dict, direction: str, reasons: list[str]) -> dict:
    sha = m.get("source_pdf_sha256") or ""
    sha_short = sha[:12]
    sk = SOURCE_KEY_BASE + (f"+{sha_short}" if sha_short else "")
    return {
        "ticker": m.get("ticker", ""),
        "broker": m.get("broker", ""),
        "date": _record_date(m),
        "old_target": _stringify_target(m.get("old_target")),
        "new_target": _stringify_target(m.get("new_target")),
        "direction": direction,
        # Preserve the original missing_fields value (may be list, string,
        # dict, etc.) so audit logs reflect what merge_meta actually emitted.
        # Default to [] only when the field is genuinely absent.
        "missing_fields": m.get("missing_fields", []) if "missing_fields" in m else [],
        "reject_reasons": reasons,
        "source_key": sk,
        "source_pdf_sha256": sha,
    }


def split_rows(meta: list[dict], strict: bool) -> tuple[list[dict], list[dict], dict[str, int]]:
    """Return (accepted, rejected, reject_reason_counts).

    When strict is False, every record is accepted (backward compat) and
    rejected list is empty.
    """
    accepted: list[dict] = []
    rejected: list[dict] = []
    reason_counts: dict[str, int] = {}

    for m in meta:
        if not strict:
            # Legacy behavior: always derive direction locally from old/new, ignoring
            # any pre-computed `direction` on the input record.
            direction = derive_direction(m.get("old_target"), m.get("new_target"))
            accepted.append(project_accepted(m, direction))
            continue

        # Strict path: trust merge_meta's `direction` if present, else derive.
        # This lets strict reject `direction == "unknown"` records that merge_meta
        # already flagged (e.g. parse_failed targets) without re-deriving them.
        direction = m.get("direction")
        if direction not in VALID_DIRECTIONS and direction != "unknown":
            direction = derive_direction(m.get("old_target"), m.get("new_target"))

        reasons = evaluate_strict(m, direction)
        if reasons:
            for r in reasons:
                reason_counts[r] = reason_counts.get(r, 0) + 1
            rejected.append(project_rejected(m, direction, reasons))
        else:
            accepted.append(project_accepted(m, direction))

    return accepted, rejected, reason_counts


def by_direction(rows: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        d = r.get("direction") or "unknown"
        out[d] = out.get(d, 0) + 1
    return out


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

    accepted, rejected, reason_counts = split_rows(meta, args.strict)
    by_dir = by_direction(accepted)

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    strict_label = "ON" if args.strict else "OFF"
    print(f"[{mode}] input  = {in_path}  rows_in={len(meta)}  strict={strict_label}")
    print(f"[{mode}] accepted = {len(accepted)}  rejected = {len(rejected)}")
    print(f"[{mode}] by_direction (accepted) = {by_dir}")
    print(f"[{mode}] header order = {HEADER}")
    if args.strict:
        if reason_counts:
            print(f"[{mode}] reject_reason_counts:")
            for reason, count in sorted(reason_counts.items(), key=lambda kv: -kv[1]):
                print(f"  {reason}: {count}")
        else:
            print(f"[{mode}] reject_reason_counts: (none)")

    for r in accepted[:5]:
        print(f"  + {r['date']} {r['ticker']} {r['broker']} {r['old_target']}→{r['new_target']} ({r['direction']})")
    if len(accepted) > 5:
        print(f"  ... (+{len(accepted) - 5} more accepted)")
    for r in rejected[:5]:
        print(f"  - {r['date']} {r['ticker']} {r['broker']} reasons={r['reject_reasons']}")
    if len(rejected) > 5:
        print(f"  ... (+{len(rejected) - 5} more rejected)")

    # Safety guard: every accepted row MUST have direct_trade_signal=false.
    # This is a Phase3 invariant (estimate revision rows are NOT trade signals).
    if any(r.get("direct_trade_signal") is not False for r in accepted):
        print("error: invariant violated — accepted row with direct_trade_signal!=false",
              file=sys.stderr)
        return 3

    if args.dry_run:
        print("[DRY-RUN] no files written. Re-run with --apply.")
        if args.strict:
            print("[DRY-RUN] strict gate ON: --apply will write estimate_revision_rows.json, "
                  "estimate_revision_rejected_rows.json, estimate_revision_summary.json.")
        else:
            print("[DRY-RUN] strict gate OFF: --apply will write estimate_revision_rows.json only "
                  "(legacy behavior).")
        print("[NOTE] CSV append is NOT performed by this script.")
        print("       Use stock_research/scripts/rolling_append.py with the output JSON.")
        return 0

    out_root = Path(args.output_root).expanduser()
    out_dir = out_root / args.date
    out_dir.mkdir(parents=True, exist_ok=True)

    rows_path = out_dir / "estimate_revision_rows.json"
    rows_path.write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[APPLY] wrote {rows_path}")

    # Strict-mode-only artifacts. In legacy (non-strict) --apply we keep the
    # original behavior: only estimate_revision_rows.json is written.
    if args.strict:
        rejected_path = out_dir / "estimate_revision_rejected_rows.json"
        rejected_path.write_text(json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[APPLY] wrote {rejected_path}")

        summary = {
            "rows_in": len(meta),
            "rows_accepted": len(accepted),
            "rows_rejected": len(rejected),
            "by_direction": by_dir,
            "reject_reason_counts": reason_counts,
            "strict_enabled": True,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_key_base": SOURCE_KEY_BASE,
            "direct_trade_signal_all_false": True,
        }
        summary_path = out_dir / "estimate_revision_summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[APPLY] wrote {summary_path}")

    print("[NEXT] feed estimate_revision_rows.json to stock_research/scripts/rolling_append.py")
    print("       --csv <STOCK_RESEARCH_ROOT>/03_daily_reports/_rolling/estimate_revision_history.csv")
    print("       --rows <output_path> --dedupe-keys date,ticker,broker,source_key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
