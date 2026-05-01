#!/usr/bin/env python3
"""Run the PR #21 ticker resolver fixture against the authoritative ticker_map.csv.

Loads `ticker_resolver_fixture.json` (sibling to this file) and asserts each
case's `expected` matches `ticker_resolver.resolve(value, filename=..., ticker_map=...)`.

This is a smoke runner — not a pytest harness — so it has no third-party deps
and runs cleanly on any Python ≥ 3.10. Exit 0 = all cases PASS, 1 = any failure.

It is also called by the PR #21 verification block in CLAUDE_CODE_RUNBOOK.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
SCRIPTS = THIS.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import ticker_resolver  # noqa: E402

REPO_ROOT = THIS.parent.parent.parent.parent


def main() -> int:
    fixture_path = THIS.parent / "ticker_resolver_fixture.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    rel = fixture["ticker_map_path"]
    tmap_path = (REPO_ROOT / rel).resolve()
    if not tmap_path.is_file():
        print(f"error: ticker_map not found: {tmap_path}", file=sys.stderr)
        return 2
    tmap = ticker_resolver.load_ticker_map(tmap_path, strict_market=True)

    cases = fixture["cases"]
    passes, failures = [], []
    for c in cases:
        got = ticker_resolver.resolve(
            c.get("value") or "",
            filename=c.get("filename") or "",
            ticker_map=tmap,
        )
        ok = got == c["expected"]
        line = (
            f"  [{'PASS' if ok else 'FAIL'}] {c['case']:50s} "
            f"value={c.get('value','')!r:30s} file={c.get('filename','')!r}  →  "
            f"got={got!r}  expected={c['expected']!r}"
        )
        (passes if ok else failures).append(line)

    print(f"[ticker_resolver_fixture] cases = {len(cases)}")
    print(f"[ticker_resolver_fixture] PASS  = {len(passes)}")
    print(f"[ticker_resolver_fixture] FAIL  = {len(failures)}")
    for ln in passes:
        print(ln)
    for ln in failures:
        print(ln)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
