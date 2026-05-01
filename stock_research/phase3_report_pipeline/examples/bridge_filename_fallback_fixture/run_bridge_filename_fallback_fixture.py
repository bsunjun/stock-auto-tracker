#!/usr/bin/env python3
"""Run the PR #22 bridge filename-fallback fixture end-to-end.

Reads `manual_meta.json` + `scan_company.json` (sibling to this script),
invokes `bridge_scan_to_parsed_meta.project_record` with the authoritative
`resources/ticker_map.csv`, and asserts each record's resolved ticker /
ticker_unmapped flag matches the case's expected value.

This guards the PR #22 hotfix path specifically: the bridge's
`if not is_krx(t)` gate must let empty tickers reach
`ticker_resolver.resolve` so the bracket-filename fallback fires. Pure
stdlib; no third-party deps.

Exit 0 = all PASS, 1 = any failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
SCRIPTS = THIS.parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bridge_scan_to_parsed_meta as bridge  # noqa: E402
import ticker_resolver  # noqa: E402

REPO_ROOT = THIS.parent.parent.parent.parent.parent
TICKER_MAP_PATH = REPO_ROOT / "stock_research/phase3_report_pipeline/resources/ticker_map.csv"


def expected_for(case: str) -> tuple[str, frozenset[str]]:
    """Returns (expected_ticker, expected_missing_fields_subset).

    The bridge's missing_fields contract distinguishes two unresolved shapes:

      * empty ticker (no Korean name to map; resolver couldn't help)
        → missing_fields contains 'ticker' (general missing field)
      * non-empty Korean name that didn't map
        → missing_fields contains 'ticker_unmapped'

    Both cases reject under build --strict; the labels just preserve operator
    triage info. We assert against subsets so the test isn't brittle if
    other fields go missing for unrelated reasons.
    """
    table = {
        "pr22_empty_ticker_bracket_filename_dd":         ("KRX:353200", frozenset()),
        "pr22_empty_ticker_bracket_filename_nota":       ("KRX:486990", frozenset()),
        "pr22_empty_ticker_unresolved_machinarox":       ("",           frozenset({"ticker"})),
        "pr22_krx_passthrough_with_unrelated_filename":  ("KRX:353200", frozenset()),
        "pr22_canonical_only_no_filename":               ("KRX:353200", frozenset()),
        "pr22_empty_ticker_no_bracket_filename":         ("",           frozenset({"ticker"})),
    }
    return table[case]


def main() -> int:
    fixture_dir = THIS.parent
    scan = json.loads((fixture_dir / "scan_company.json").read_text(encoding="utf-8"))
    manual = json.loads((fixture_dir / "manual_meta.json").read_text(encoding="utf-8"))
    by_sha = {r.get("sha256"): r for r in scan if r.get("sha256")}
    by_name = {r.get("filename"): r for r in scan if r.get("filename")}
    tmap = ticker_resolver.load_ticker_map(TICKER_MAP_PATH, strict_market=True)

    passes, failures = [], []
    for rec in manual:
        case = rec.get("case", "<no-case>")
        out = bridge.project_record(rec, by_sha, by_name, scan, tmap)
        exp_ticker, exp_missing_subset = expected_for(case)
        got_ticker = out.get("ticker", "")
        got_missing = set(out.get("missing_fields", []))
        ok = got_ticker == exp_ticker and exp_missing_subset.issubset(got_missing)
        line = (
            f"  [{'PASS' if ok else 'FAIL'}] {case:50s} "
            f"got_ticker={got_ticker!r}  missing_fields⊇{sorted(exp_missing_subset)} "
            f"({'satisfied' if exp_missing_subset.issubset(got_missing) else 'NOT satisfied'}; "
            f"actual={sorted(got_missing)})"
        )
        (passes if ok else failures).append(line)

    print(f"[bridge_filename_fallback_fixture] cases = {len(manual)}")
    print(f"[bridge_filename_fallback_fixture] PASS  = {len(passes)}")
    print(f"[bridge_filename_fallback_fixture] FAIL  = {len(failures)}")
    for ln in passes:
        print(ln)
    for ln in failures:
        print(ln)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
