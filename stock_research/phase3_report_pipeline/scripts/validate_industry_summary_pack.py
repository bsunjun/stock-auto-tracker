#!/usr/bin/env python3
"""
Phase 3 — PR #43 — Industry summary validation + catalyst pack stub.

Reads a `phase3:industry_summary_pack_stub:v1` pack (the PR #41 output,
either still-empty `pending_llm_summary` stubs or LLM-filled
`llm_summary_filled` stubs) and:

  1. Runs hard / soft validation per record.
  2. Emits an `industry_catalyst_pack_stub.json` carrying ONLY records
     that pass every check (empty pack is valid output).
  3. Emits a `validation_summary.json` with per-record verdicts and
     global counters.
  4. Emits a markdown rendering of the catalyst pack for paste-in.

This script does NOT call any LLM, does NOT touch PDF body text, does
NOT modify the source stub file. It is purely a validator + projection.

Validation classifications
--------------------------
  hard_fail (script exits 3 immediately, no files written):
    * any record carries `direct_trade_signal: true` — defense in depth
      past PR #41's same guard (would never come from
      `build_industry_summary_pack_stub.py`).

  rejected_pending_summary:
    * `status == "pending_llm_summary"` — still-empty stub; LLM has not
      filled it yet. Cannot be promoted to catalyst pack.

  rejected_missing_verification:
    * `len(missing_verification) > 0` even when status is
      `llm_summary_filled` — LLM claimed it was done but left fields.

  rejected_trade_signal_truthy:
    * `trade_signal not in (None, False)` — LLM injected a non-null
      signal value.

  rejected_forbidden_trade_language:
    * any string-valued analytic field, or any list-element string,
      contains a directional verb / target-price phrase from
      `_FORBIDDEN_TRADE_PATTERNS` (see below).

  rejected_empty_required_field:
    * `status == "llm_summary_filled"` AND any of the 11 mandatory
      analytic fields is empty (string `""` or list `[]`). This catches
      LLMs that flipped status without actually filling fields.

  rejected_unknown_status:
    * `status` is neither `pending_llm_summary` nor
      `llm_summary_filled` — refuse to project unknown lifecycle states.

  valid:
    * passes every check above. Projected into the catalyst pack output
      with `direct_trade_signal: false`, `trade_signal: null`,
      `status: "catalyst_pack_emitted"`, plus a derived
      `catalyst_topology[]` summarizing the 5 signal fields.

CLI
---
    python3 scripts/validate_industry_summary_pack.py \
        --pack    /tmp/industry_summary_pack/<date>/industry_summary_pack_stub.json \
        --out-dir /tmp/industry_catalyst_pack \
        [--date YYYY-MM-DD]      # default: today
        [--apply]

Output files (apply mode, under <out-dir>/<date>/):
    industry_catalyst_pack_stub.json
    industry_catalyst_pack_stub.md
    validation_summary.json

Schemas
-------
    catalyst row     : phase3:industry_catalyst_pack_stub:v1
    catalyst summary : phase3:industry_catalyst_pack_stub_summary:v1
    validation summ. : phase3:industry_summary_validation:v1

Conservative invariants (PR #43 guards)
---------------------------------------
  * `--out-dir` resolving inside the repo + `--apply` → exit 2 (PR #29 /
    PR #39 / PR #41 guard policy).
  * Default dry-run; only `--apply` writes files.
  * Hard-fail on any input record with `direct_trade_signal: true`.
  * Every emitted catalyst record carries `direct_trade_signal: false`,
    `trade_signal: null`, and `status: "catalyst_pack_emitted"`. The
    validation summary records `direct_trade_signal_true_count: 0`
    AND `trade_signal_truthy_emitted: 0` AND a fully-zero
    `forbidden_actions_confirmed` block.
  * The catalyst pack carries NO `recommendation` / `top_pick` /
    `target_price` field. By construction the schema does not include
    any directional verb or position field.
  * No PDF body read. No OCR / Vision / network. The validator only
    inspects fields already present in the input pack JSON.

This script does NOT touch parser / bridge / merge / build / emit /
ticker_map / broker autodetect / `build_wisereport_inventory.py` /
`build_industry_summary_pack_stub.py` source code. It is purely a
downstream validator + projection.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List


THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

INPUT_SCHEMA = "phase3:industry_summary_pack_stub:v1"
CATALYST_ROW_SCHEMA = "phase3:industry_catalyst_pack_stub:v1"
CATALYST_SUMMARY_SCHEMA = "phase3:industry_catalyst_pack_stub_summary:v1"
VALIDATION_SUMMARY_SCHEMA = "phase3:industry_summary_validation:v1"

# Re-declared locally so this validator stays decoupled from the PR #41
# stub generator's source. If those constants drift, the fixture self-
# test will catch the mismatch.
ANALYTIC_FIELDS: tuple[str, ...] = (
    "sub_sector",
    "broker_hint",
    "core_thesis",
    "demand_signal",
    "supply_signal",
    "price_signal",
    "policy_signal",
    "capex_signal",
    "value_chain",
    "beneficiary_candidates",
    "risk_flags",
)
SIGNAL_FIELDS_FOR_TOPOLOGY: tuple[str, ...] = (
    "demand_signal",
    "supply_signal",
    "price_signal",
    "policy_signal",
    "capex_signal",
)

# Directional verbs / target-price phrases / position-size phrases that
# must NOT appear in any analytic field. Korean + English. Patterns are
# deliberately conservative — they target phrases that would only ever
# appear when the LLM produced a buy/sell-adjacent suggestion. Common
# innocent uses (e.g., "buyback", "selloff" as one word) are not
# matched because we anchor on word boundaries / explicit spaces.
_FORBIDDEN_TRADE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"매수\b"),
    re.compile(r"매도\b"),
    re.compile(r"비중\s*확대"),
    re.compile(r"비중\s*축소"),
    re.compile(r"비중\s*상향"),
    re.compile(r"비중\s*하향"),
    re.compile(r"\bTop\s*Pick\b", re.IGNORECASE),
    re.compile(r"\bBottom\s*Pick\b", re.IGNORECASE),
    re.compile(r"\btarget[\s_]?price\b", re.IGNORECASE),
    re.compile(r"\bcut[\s_]?loss\b", re.IGNORECASE),
    re.compile(r"\btake[\s_]?profit\b", re.IGNORECASE),
    re.compile(r"\bposition[\s_]?size\b", re.IGNORECASE),
    re.compile(r"\bbuy\s+at\b", re.IGNORECASE),
    re.compile(r"\bsell\s+at\b", re.IGNORECASE),
    re.compile(r"\bbuy\s+now\b", re.IGNORECASE),
    re.compile(r"\bsell\s+now\b", re.IGNORECASE),
    re.compile(r"매매\s*신호"),
    re.compile(r"매수\s*추천"),
    re.compile(r"매도\s*권고"),
    re.compile(r"목표\s*주가"),
    re.compile(r"\bPB[_\s]?READY\b", re.IGNORECASE),
    re.compile(r"\bPB[_\s]?SCOUT\b", re.IGNORECASE),
    re.compile(r"\bPB[_\s]?TRIGGER\b", re.IGNORECASE),
)

# Status values the validator understands. Anything else → rejected_unknown_status.
_STATUS_PENDING = "pending_llm_summary"
_STATUS_FILLED = "llm_summary_filled"
_STATUS_EMITTED = "catalyst_pack_emitted"
_KNOWN_INPUT_STATUSES: frozenset[str] = frozenset({_STATUS_PENDING, _STATUS_FILLED})

_VALID = "valid"
_REJECTED_PENDING = "rejected_pending_summary"
_REJECTED_MISSING = "rejected_missing_verification"
_REJECTED_TRUTHY = "rejected_trade_signal_truthy"
_REJECTED_FORBIDDEN = "rejected_forbidden_trade_language"
_REJECTED_EMPTY = "rejected_empty_required_field"
_REJECTED_UNKNOWN = "rejected_unknown_status"
_HARD_FAIL = "hard_fail_direct_trade_signal_true"

_VERDICT_BUCKETS: tuple[str, ...] = (
    _VALID,
    _REJECTED_PENDING,
    _REJECTED_MISSING,
    _REJECTED_TRUTHY,
    _REJECTED_FORBIDDEN,
    _REJECTED_EMPTY,
    _REJECTED_UNKNOWN,
)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _scan_strings(value: Any) -> list[str]:
    """Return every string contained in `value` (handles strings + flat
    lists of strings; ignores other types)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            if isinstance(v, str):
                out.append(v)
        return out
    return []


def _detect_forbidden_phrases(rec: dict) -> list[dict]:
    """Return a list of {field, pattern, snippet} for every forbidden-
    phrase match found across the analytic fields. Empty list = clean."""
    hits: list[dict] = []
    for f in ANALYTIC_FIELDS:
        for s in _scan_strings(rec.get(f)):
            for pat in _FORBIDDEN_TRADE_PATTERNS:
                m = pat.search(s)
                if m:
                    snippet = s[max(0, m.start() - 8): m.end() + 8]
                    hits.append({
                        "field": f,
                        "pattern": pat.pattern,
                        "snippet": snippet,
                    })
    return hits


def _is_field_empty(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return value is None


def classify_record(rec: dict) -> tuple[str, dict]:
    """Return (verdict, details).

    `details` carries:
      - reason_token (short stable identifier)
      - extra (verdict-specific extra info, e.g. forbidden hits, missing fields)
    """
    if not isinstance(rec, dict):
        return _REJECTED_UNKNOWN, {"reason_token": "non_dict_record"}

    if rec.get("schema") != INPUT_SCHEMA:
        return _REJECTED_UNKNOWN, {"reason_token": "wrong_input_schema",
                                   "extra": {"got": rec.get("schema")}}

    # Hard-fail BEFORE any other check.
    if rec.get("direct_trade_signal") is True:
        return _HARD_FAIL, {"reason_token": "direct_trade_signal_true"}

    ts = rec.get("trade_signal")
    if ts not in (None, False):
        return _REJECTED_TRUTHY, {"reason_token": "trade_signal_truthy",
                                  "extra": {"got": ts}}

    status = rec.get("status")
    if status == _STATUS_PENDING:
        return _REJECTED_PENDING, {"reason_token": "status_pending"}
    if status not in _KNOWN_INPUT_STATUSES:
        return _REJECTED_UNKNOWN, {"reason_token": "status_unknown",
                                   "extra": {"got": status}}

    # status == llm_summary_filled
    mv = rec.get("missing_verification") or []
    if not isinstance(mv, list) or len(mv) > 0:
        return _REJECTED_MISSING, {"reason_token": "missing_verification_nonempty",
                                   "extra": {"missing": mv}}

    empty_fields = [f for f in ANALYTIC_FIELDS if _is_field_empty(rec.get(f))]
    if empty_fields:
        return _REJECTED_EMPTY, {"reason_token": "empty_required_field",
                                 "extra": {"empty_fields": empty_fields}}

    forbidden_hits = _detect_forbidden_phrases(rec)
    if forbidden_hits:
        return _REJECTED_FORBIDDEN, {"reason_token": "forbidden_trade_language",
                                     "extra": {"hits": forbidden_hits}}

    return _VALID, {"reason_token": "ok"}


def project_catalyst_row(rec: dict) -> dict:
    """Project a valid filled summary record into a catalyst pack row.

    The schema is intentionally MISSING any recommendation / direction /
    position field. catalyst_topology[] is a derived structured list of
    the 5 signal fields; everything else is metadata + analytic content
    inherited from the input.
    """
    topology: list[dict] = []
    for f in SIGNAL_FIELDS_FOR_TOPOLOGY:
        v = rec.get(f, "")
        if isinstance(v, str) and v.strip():
            topology.append({"signal": f, "summary": v.strip()})

    return {
        "schema": CATALYST_ROW_SCHEMA,
        "report_date": rec.get("report_date", ""),
        "sector": rec.get("sector", ""),
        "sub_sector": rec.get("sub_sector", ""),
        "report_title": rec.get("report_title", ""),
        "broker_hint": rec.get("broker_hint", ""),
        "source_file_basename": rec.get("source_file_basename", ""),
        "sha256_prefix_12": rec.get("sha256_prefix_12", ""),
        "core_thesis": rec.get("core_thesis", ""),
        "catalyst_topology": topology,
        "value_chain": list(rec.get("value_chain") or []),
        "beneficiary_candidates": list(rec.get("beneficiary_candidates") or []),
        "risk_flags": list(rec.get("risk_flags") or []),
        "earnings_revision_link_possible": rec.get("earnings_revision_link_possible"),
        "source_confidence": rec.get("source_confidence"),
        "status": _STATUS_EMITTED,
        # Hard invariants — every catalyst row literally carries these.
        "direct_trade_signal": False,
        "trade_signal": None,
    }


def render_markdown(catalyst_rows: list[dict], date: str) -> str:
    lines: list[str] = []
    lines.append(f"# Industry catalyst pack stub — {date}")
    lines.append("")
    lines.append(f"- schema: `{CATALYST_ROW_SCHEMA}`")
    lines.append(f"- valid catalyst rows: {len(catalyst_rows)}")
    lines.append(f"- direct_trade_signal: **false** on every row")
    lines.append(f"- trade_signal: **null** on every row")
    lines.append(f"- generated_at: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("")
    lines.append("> **Reading guidance.** This pack is review-only. It carries NO "
                 "recommendation / target_price / top_pick / position_size field. "
                 "Downstream consumers MUST treat it as sector-rotation context "
                 "ONLY; never as a trading directive.")
    lines.append("")
    for i, r in enumerate(catalyst_rows, 1):
        sector = r.get("sector") or "(no sector)"
        title = r.get("report_title") or "(no title)"
        lines.append(f"## {i:02d}. [{sector}] {title}")
        lines.append("")
        lines.append(f"- sub_sector: `{r.get('sub_sector','')}`")
        lines.append(f"- broker_hint: `{r.get('broker_hint','')}`")
        lines.append(f"- source_file_basename: `{r.get('source_file_basename','')}`")
        lines.append(f"- sha256_prefix_12: `{r.get('sha256_prefix_12','')}`")
        lines.append(f"- direct_trade_signal: `{r.get('direct_trade_signal')}`")
        lines.append(f"- trade_signal: `{r.get('trade_signal')}`")
        lines.append(f"- status: `{r.get('status')}`")
        lines.append("")
        lines.append("Catalyst row JSON:")
        lines.append("```json")
        lines.append(json.dumps(r, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--pack", required=True,
                   help="Path to phase3:industry_summary_pack_stub:v1 pack JSON "
                        "(may be empty stubs or LLM-filled).")
    p.add_argument("--out-dir", required=True,
                   help="Output root. Outputs land under <out-dir>/<date>/.")
    p.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                   help="YYYY-MM-DD subdir name.")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Do not write files; print summary only.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize catalyst pack stub + validation summary.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    pack_path = Path(args.pack).expanduser().resolve()
    if not pack_path.is_file():
        print(f"error: --pack not found: {pack_path}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve()
    if not args.dry_run and _is_inside_repo(out_dir):
        print(f"error: --out-dir must live outside the repo under --apply (got {out_dir})",
              file=sys.stderr)
        return 2

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    if not isinstance(pack, list):
        print(f"error: --pack must be a JSON array of stub records", file=sys.stderr)
        return 2

    counts: dict[str, int] = {b: 0 for b in _VERDICT_BUCKETS}
    per_record: list[dict] = []
    catalyst_rows: list[dict] = []
    direct_trade_signal_true_count = 0
    forbidden_total_hits = 0

    for idx, rec in enumerate(pack):
        verdict, details = classify_record(rec)
        if verdict == _HARD_FAIL:
            direct_trade_signal_true_count += 1
            print(f"error: record index={idx} carries direct_trade_signal=true; refusing.",
                  file=sys.stderr)
            return 3
        counts[verdict] += 1
        sha = (rec.get("sha256_prefix_12") if isinstance(rec, dict) else "") or ""
        per_record.append({
            "index": idx,
            "sha256_prefix_12": sha,
            "verdict": verdict,
            "reason_token": details.get("reason_token", ""),
            "extra": details.get("extra", {}),
        })
        if verdict == _REJECTED_FORBIDDEN:
            forbidden_total_hits += len(details.get("extra", {}).get("hits", []))
        if verdict == _VALID:
            catalyst_rows.append(project_catalyst_row(rec))

    # Re-assert invariants on catalyst output (paranoid second pass).
    truthy_emitted = sum(
        1 for r in catalyst_rows
        if r.get("trade_signal") is not None or r.get("direct_trade_signal") is not False
    )
    if truthy_emitted:
        print(f"error: {truthy_emitted} catalyst rows leaked truthy trade_signal", file=sys.stderr)
        return 3

    validation_summary = {
        "schema": VALIDATION_SUMMARY_SCHEMA,
        "date": args.date,
        "pack": str(pack_path),
        "records_in": len(pack),
        "valid_count": counts[_VALID],
        "verdict_counts": counts,
        "direct_trade_signal_true_count": direct_trade_signal_true_count,
        "trade_signal_truthy_emitted": truthy_emitted,
        "forbidden_trade_language_total_hits": forbidden_total_hits,
        "per_record": per_record,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "drive_writes": 0,
            "drive_renames": 0,
            "drive_deletes": 0,
            "repo_writes": 0,
            "rolling_apply": 0,
            "promote_or_super_pack": 0,
            "direct_trade_signal_true": 0,
            "target_price_as_primary": 0,
            "trade_signal_truthy_emitted": 0,
            "pdf_body_text_committed": 0,
            "buy_or_sell_recommendation_emitted": 0,
        },
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    catalyst_summary = {
        "schema": CATALYST_SUMMARY_SCHEMA,
        "date": args.date,
        "pack_source": str(pack_path),
        "valid_count": counts[_VALID],
        "rejected_count": sum(counts[b] for b in _VERDICT_BUCKETS if b != _VALID),
        "verdict_counts": counts,
        "all_direct_trade_signal_false": all(r.get("direct_trade_signal") is False for r in catalyst_rows),
        "all_trade_signal_null": all(r.get("trade_signal") is None for r in catalyst_rows),
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] pack                    = {pack_path}")
    print(f"[{mode}] records_in              = {len(pack)}")
    for b in _VERDICT_BUCKETS:
        print(f"[{mode}]   {b:35s} = {counts[b]}")
    print(f"[{mode}] direct_trade_signal_true_count   = {direct_trade_signal_true_count}")
    print(f"[{mode}] trade_signal_truthy_emitted      = {truthy_emitted}")
    print(f"[{mode}] forbidden_trade_language_total_hits = {forbidden_total_hits}")
    print(f"[{mode}] catalyst rows emitted   = {len(catalyst_rows)}")

    if args.dry_run:
        return 0

    date_dir = out_dir / args.date
    date_dir.mkdir(parents=True, exist_ok=True)
    catalyst_path = date_dir / "industry_catalyst_pack_stub.json"
    catalyst_md_path = date_dir / "industry_catalyst_pack_stub.md"
    catalyst_summary_path = date_dir / "industry_catalyst_pack_stub_summary.json"
    validation_path = date_dir / "validation_summary.json"

    catalyst_path.write_text(
        json.dumps(catalyst_rows, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    catalyst_md_path.write_text(render_markdown(catalyst_rows, args.date), encoding="utf-8")
    catalyst_summary_path.write_text(
        json.dumps(catalyst_summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    validation_path.write_text(
        json.dumps(validation_summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    print(f"[APPLY] wrote {catalyst_path}")
    print(f"[APPLY] wrote {catalyst_md_path}")
    print(f"[APPLY] wrote {catalyst_summary_path}")
    print(f"[APPLY] wrote {validation_path}")
    print(f"[NEXT] catalyst pack is REVIEW-ONLY. Carries no buy/sell/target_price/")
    print(f"       position_size/top_pick field by construction. Do NOT feed it")
    print(f"       to rolling_append.py / latest / promote / Super Pack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
