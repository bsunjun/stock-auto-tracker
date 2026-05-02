#!/usr/bin/env python3
"""
Phase 3 — PR #41 — Industry-report LLM summary pack STUB generator.

Reads a `phase3:wisereport_date_folder_inventory:v1` inventory (the output
of `build_wisereport_inventory.py`) and emits a `pending_llm_summary`
stub pack for each entry in `selected_industry[]`. The stub deliberately
does NOT touch PDF body text — it only carries `report_date`, `sector`,
`report_title`, `source_file_basename`, and `sha256_prefix_12` from the
inventory, and pre-fills every analytic field with an empty placeholder
plus a `missing_verification` list for the downstream LLM to populate.

`selected_company[]` and the top-level `selected[]` alias are explicitly
ignored; this generator is **industry-only** by design. Industry reports
do NOT pass through `extract_report_estimate_table.py` /
`bridge_scan_to_parsed_meta.py` / `merge_meta.py` /
`build_report_estimate_v132.py` / `emit_revision_trend.py`.

The stub pack is consumed by an out-of-band LLM workflow (Gemini for
inventory triage, Claude for in-depth PDF reading, ChatGPT for sector-
rotation context). See `docs/INDUSTRY_REPORT_HANDOFF_PROMPTS.md` for the
exact prompts. None of those workflows are invoked by THIS script —
this is the deterministic stub-skeleton step that emits the schema
the LLM is asked to fill.

CLI
---
    python3 scripts/build_industry_summary_pack_stub.py \
        --inventory /tmp/wisereport_inventory.json \
        --out-dir   /tmp/industry_summary_pack \
        [--date YYYY-MM-DD]      # default: inventory.date
        [--max-stubs N]          # default 50 (HARD_MAX 50)
        [--apply]

Output (under <out-dir>/<date>/):
    industry_summary_pack_stub.json     — list of per-PDF stub records
    industry_summary_pack_stub.md       — markdown rendering for paste-in
    industry_summary_pack_stub_summary.json  — top-level summary block

Schemas
-------
    per-row     : phase3:industry_summary_pack_stub:v1
    top-level   : phase3:industry_summary_pack_stub_summary:v1

Conservative invariants (PR #41 guards)
---------------------------------------
  * Reads `selected_industry[]` ONLY. If the inventory carries a
    populated `selected_company[]` / `selected[]`, those entries are
    skipped (counted in `selected_company_ignored_count`).
  * `--out-dir` resolving inside the repo + `--apply` → exit 2 (mirrors
    PR #29 / PR #39 guard policy).
  * `--max-stubs > 50` → exit 2 (HARD_MAX matches PR #39 per-folder cap).
  * Default dry-run; only `--apply` writes files.
  * Every stub record carries `direct_trade_signal: false`,
    `status: "pending_llm_summary"`, and `trade_signal: null` (never any
    truthy value). The summary records `direct_trade_signal_true_count: 0`
    and a fully-zero `forbidden_actions_confirmed` block.
  * No PDF body text is read. No OCR / Vision / network. The script only
    walks the inventory's `selected_industry[]` entries (filename + sha
    prefix metadata) and emits placeholder records.
  * The `missing_verification[]` list on every stub records EVERY analytic
    field the LLM still needs to populate — by construction, an unmodified
    stub has all 11 analytic fields in `missing_verification`, which means
    a downstream filter that requires `len(missing_verification)==0` will
    NEVER promote an unfilled stub to a trade-signal-adjacent surface.

This script does NOT touch parser / bridge / merge / build / emit /
ticker_map / broker autodetect / `build_wisereport_inventory.py` logic.
It is a fresh entry point that is purely additive.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List


THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent.parent.parent

PER_ROW_SCHEMA = "phase3:industry_summary_pack_stub:v1"
SUMMARY_SCHEMA = "phase3:industry_summary_pack_stub_summary:v1"
INVENTORY_SCHEMA = "phase3:wisereport_date_folder_inventory:v1"

HARD_MAX_STUBS = 50

# The 11 analytic fields the LLM must populate. Order matches the
# template in docs/INDUSTRY_REPORT_LLM_SUMMARY_TEMPLATE.md.
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
# Optional (nullable) analytic fields. These are NOT in the
# missing_verification list by default — the LLM may set them to null
# explicitly when it has read the PDF and concluded "n/a".
NULLABLE_ANALYTIC_FIELDS: tuple[str, ...] = (
    "earnings_revision_link_possible",
    "source_confidence",
)


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _empty_value_for(field: str) -> Any:
    """Empty placeholder per field type. Pure scalar / list — never a
    sentinel that could be mistaken for a real signal."""
    if field in ("value_chain", "beneficiary_candidates", "risk_flags"):
        return []
    return ""


def build_stub_record(entry: dict, date_fallback: str) -> dict:
    """Project one `selected_industry[]` entry into the stub schema.

    The caller has already filtered to industry entries. This function
    is pure metadata projection — no PDF reading, no LLM call, no
    network. Empty placeholders for analytic fields; `missing_verification`
    pre-populated with the 11 mandatory fields.
    """
    rec: dict[str, Any] = {
        "schema": PER_ROW_SCHEMA,
        "report_date": entry.get("report_date") or date_fallback,
        "sector": entry.get("sector_hint", ""),
        "report_title": entry.get("title_hint", ""),
        "source_file_basename": entry.get("filename", ""),
        "sha256_prefix_12": entry.get("sha256_prefix_12", ""),
        # All 11 analytic fields start empty.
    }
    for f in ANALYTIC_FIELDS:
        rec[f] = _empty_value_for(f)
    for f in NULLABLE_ANALYTIC_FIELDS:
        rec[f] = None

    # The `missing_verification[]` list records every analytic field the
    # LLM still needs to populate. A downstream filter that requires
    # `len(missing_verification) == 0` will refuse to promote unfilled
    # stubs. Default state = ALL 11 fields outstanding.
    rec["missing_verification"] = list(ANALYTIC_FIELDS)

    # Hard invariants — every stub record carries these literally.
    rec["status"] = "pending_llm_summary"
    rec["direct_trade_signal"] = False
    rec["trade_signal"] = None
    return rec


def render_markdown(stubs: List[dict], date: str) -> str:
    """Markdown rendering of the stub pack for paste-in. Each stub gets
    its own H2 section with a fenced JSON block of placeholder fields,
    plus a blank `## Notes` block the LLM can fill freely.
    """
    lines: list[str] = []
    lines.append(f"# Industry summary pack stub — {date}")
    lines.append("")
    lines.append(f"- schema: `{PER_ROW_SCHEMA}`")
    lines.append(f"- entries: {len(stubs)} (all `pending_llm_summary`)")
    lines.append(f"- direct_trade_signal: **false** on every stub")
    lines.append(f"- generated_at: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("")
    lines.append("> Reading guidance: see `docs/INDUSTRY_REPORT_LLM_SUMMARY_TEMPLATE.md` "
                 "and `docs/INDUSTRY_REPORT_HANDOFF_PROMPTS.md`. None of these stubs "
                 "carry trade signals; the LLM must NEVER produce buy/sell calls.")
    lines.append("")
    for i, s in enumerate(stubs, 1):
        title = s.get("report_title") or "(no title)"
        sector = s.get("sector") or "(no sector)"
        lines.append(f"## {i:02d}. [{sector}] {title}")
        lines.append("")
        lines.append(f"- source_file_basename: `{s.get('source_file_basename','')}`")
        lines.append(f"- sha256_prefix_12: `{s.get('sha256_prefix_12','')}`")
        lines.append(f"- report_date: `{s.get('report_date','')}`")
        lines.append(f"- status: `{s.get('status','')}`")
        lines.append(f"- direct_trade_signal: `{s.get('direct_trade_signal')}`")
        lines.append("")
        lines.append("Stub JSON (LLM fills empty fields):")
        lines.append("```json")
        lines.append(json.dumps(s, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### Notes")
        lines.append("")
        lines.append("(LLM may add free-form notes here; do NOT include any buy/sell suggestion.)")
        lines.append("")
    return "\n".join(lines)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--inventory", required=True,
                   help="Path to phase3:wisereport_date_folder_inventory:v1 JSON "
                        "(output of build_wisereport_inventory.py).")
    p.add_argument("--out-dir", required=True,
                   help="Output root. Outputs land under <out-dir>/<date>/.")
    p.add_argument("--date", default=None,
                   help="YYYY-MM-DD subdir name. Default: inventory.date.")
    p.add_argument("--max-stubs", type=int, default=HARD_MAX_STUBS,
                   help=f"Per-pack cap (HARD_MAX={HARD_MAX_STUBS}).")
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="(default) Do not write files; print summary only.")
    p.add_argument("--apply", dest="dry_run", action="store_false",
                   help="Materialize stub JSON / markdown / summary files.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.max_stubs > HARD_MAX_STUBS or args.max_stubs < 0:
        print(f"error: --max-stubs must be 0..{HARD_MAX_STUBS} (got {args.max_stubs})",
              file=sys.stderr)
        return 2

    inv_path = Path(args.inventory).expanduser().resolve()
    if not inv_path.is_file():
        print(f"error: --inventory not found: {inv_path}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve()
    if not args.dry_run and _is_inside_repo(out_dir):
        print(f"error: --out-dir must live outside the repo under --apply (got {out_dir})",
              file=sys.stderr)
        return 2

    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    if not isinstance(inv, dict) or inv.get("schema") != INVENTORY_SCHEMA:
        print(f"error: --inventory must be schema={INVENTORY_SCHEMA!r}", file=sys.stderr)
        return 2

    inv_date = inv.get("date", "")
    date = args.date or inv_date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        print(f"error: date must be YYYY-MM-DD (got {date!r}; from --date or inventory.date)",
              file=sys.stderr)
        return 2

    industry_entries = inv.get("selected_industry") or []
    if not isinstance(industry_entries, list):
        print("error: inventory.selected_industry must be a list", file=sys.stderr)
        return 2

    selected_company_count = len(inv.get("selected_company") or [])
    selected_alias_count = len(inv.get("selected") or [])

    # Defense: refuse if any industry entry already carries
    # direct_trade_signal=true (would never happen via build_wisereport_inventory,
    # but defends against hand-edited inventories).
    bad = [e for e in industry_entries
           if isinstance(e, dict) and e.get("direct_trade_signal") is True]
    if bad:
        print(f"error: {len(bad)} industry entries carry direct_trade_signal=true; refusing.",
              file=sys.stderr)
        return 3

    capped = 0
    if len(industry_entries) > args.max_stubs:
        capped = len(industry_entries) - args.max_stubs
        industry_entries = industry_entries[: args.max_stubs]

    stubs: list[dict] = [
        build_stub_record(e, date) for e in industry_entries
        if isinstance(e, dict)
    ]

    summary = {
        "schema": SUMMARY_SCHEMA,
        "date": date,
        "inventory": str(inv_path),
        "industry_pdf_count": len(stubs),
        "selected_company_ignored_count": selected_company_count,
        "selected_alias_ignored_count": selected_alias_count,
        "capped_count": capped,
        "missing_verification_total": sum(len(s["missing_verification"]) for s in stubs),
        "direct_trade_signal_true_count": 0,
        "all_status_pending_llm_summary": all(
            s.get("status") == "pending_llm_summary" for s in stubs
        ) if stubs else True,
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
            "pdf_body_text_committed": 0,
            "trade_signal_truthy_emitted": 0,
        },
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"[{mode}] inventory                = {inv_path}")
    print(f"[{mode}] date                     = {date}")
    print(f"[{mode}] industry_pdf_count       = {summary['industry_pdf_count']}")
    print(f"[{mode}] selected_company_ignored = {summary['selected_company_ignored_count']}")
    print(f"[{mode}] selected_alias_ignored   = {summary['selected_alias_ignored_count']}")
    print(f"[{mode}] capped_count             = {summary['capped_count']}")
    print(f"[{mode}] missing_verification_total = {summary['missing_verification_total']}")
    print(f"[{mode}] direct_trade_signal_true_count = {summary['direct_trade_signal_true_count']}")

    if args.dry_run:
        return 0

    date_dir = out_dir / date
    date_dir.mkdir(parents=True, exist_ok=True)
    json_out = date_dir / "industry_summary_pack_stub.json"
    md_out = date_dir / "industry_summary_pack_stub.md"
    summary_out = date_dir / "industry_summary_pack_stub_summary.json"

    json_out.write_text(
        json.dumps(stubs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_out.write_text(render_markdown(stubs, date), encoding="utf-8")
    summary_out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[APPLY] wrote {json_out}")
    print(f"[APPLY] wrote {md_out}")
    print(f"[APPLY] wrote {summary_out}")
    print(f"[NEXT] hand the markdown / JSON to a Claude / Gemini / GPT")
    print(f"       LLM workflow per docs/INDUSTRY_REPORT_HANDOFF_PROMPTS.md.")
    print(f"       The LLM MUST NEVER emit buy/sell suggestions; every")
    print(f"       returned stub MUST keep direct_trade_signal=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
