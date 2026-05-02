#!/usr/bin/env python3
"""PR #41 — Self-test runner for the industry_summary_pack_stub fixture.

Runs `scripts/build_industry_summary_pack_stub.py` against the four fixture
inventories under `examples/industry_summary_pack_stub_fixture/` and asserts:

  1. company_and_industry inventory  → 3 stubs emitted, selected_company /
     selected alias counts both 2, missing_verification_total = 33,
     all stubs `pending_llm_summary` + `direct_trade_signal=false`.
  2. industry_only inventory         → 1 stub, ignored counts both 0.
  3. company_only inventory          → 0 stubs, both ignored counts 1,
     missing_verification_total = 0.
  4. with_signal_true inventory      → exit 3, no files written.

Plus three guards:
  * `--out-dir` resolving inside repo + `--apply` → exit 2.
  * `--max-stubs > 50` → exit 2 (HARD_MAX).
  * Inventory schema mismatch → exit 2.

The runner also asserts that each emitted stub keeps `trade_signal: null`,
`direct_trade_signal: false`, and that `selected_company[]` /
`selected_industry[]` symbol grep on the new script does NOT show the
script reading `selected_company[]` (industry-only by construction).

Usage
-----
  python3 examples/run_industry_summary_pack_stub_fixture.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
SCRIPT = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "scripts" / "build_industry_summary_pack_stub.py"
FIXTURE = HERE / "industry_summary_pack_stub_fixture"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _run(cmd: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != expected_returncode:
        sys.stdout.write(p.stdout or "")
        sys.stderr.write(p.stderr or "")
        _fail(f"command exited {p.returncode} (expected {expected_returncode}): {' '.join(cmd)}")
    return p


def _check_stub_invariants(stubs: list[dict], scenario: str) -> None:
    for s in stubs:
        if s.get("schema") != "phase3:industry_summary_pack_stub:v1":
            _fail(f"[{scenario}] stub schema wrong: {s.get('schema')!r}")
        if s.get("direct_trade_signal") is not False:
            _fail(f"[{scenario}] stub direct_trade_signal != False: {s!r}")
        if s.get("trade_signal") is not None:
            _fail(f"[{scenario}] stub trade_signal must be None, got {s.get('trade_signal')!r}")
        if s.get("status") != "pending_llm_summary":
            _fail(f"[{scenario}] stub status != 'pending_llm_summary'")
        mv = s.get("missing_verification") or []
        if not isinstance(mv, list):
            _fail(f"[{scenario}] missing_verification must be a list")
        # The stub must list ALL 11 mandatory analytic fields.
        expected_mv = [
            "sub_sector", "broker_hint", "core_thesis",
            "demand_signal", "supply_signal", "price_signal",
            "policy_signal", "capex_signal",
            "value_chain", "beneficiary_candidates", "risk_flags",
        ]
        if mv != expected_mv:
            _fail(f"[{scenario}] missing_verification != expected: got={mv}")


def main() -> int:
    if not SCRIPT.is_file():
        _fail(f"script missing: {SCRIPT}")

    tmpdir = Path(tempfile.mkdtemp(prefix="pr41_stub_fix_"))
    try:
        # Scenario 1: company_and_industry
        s1_out = tmpdir / "s1"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_company_and_industry.json"),
              "--out-dir", str(s1_out),
              "--apply"], 0)
        s1_dir = s1_out / "2026-04-30"
        s1_pack = json.loads((s1_dir / "industry_summary_pack_stub.json").read_text(encoding="utf-8"))
        s1_summary = json.loads((s1_dir / "industry_summary_pack_stub_summary.json").read_text(encoding="utf-8"))
        s1_md = (s1_dir / "industry_summary_pack_stub.md").read_text(encoding="utf-8")
        if len(s1_pack) != 3:
            _fail(f"[s1] expected 3 stubs, got {len(s1_pack)}")
        _check_stub_invariants(s1_pack, "s1")
        if s1_summary["industry_pdf_count"] != 3:
            _fail(f"[s1] industry_pdf_count expected 3, got {s1_summary['industry_pdf_count']}")
        if s1_summary["selected_company_ignored_count"] != 2:
            _fail(f"[s1] selected_company_ignored_count expected 2, got {s1_summary['selected_company_ignored_count']}")
        if s1_summary["selected_alias_ignored_count"] != 2:
            _fail(f"[s1] selected_alias_ignored_count expected 2, got {s1_summary['selected_alias_ignored_count']}")
        if s1_summary["missing_verification_total"] != 33:
            _fail(f"[s1] missing_verification_total expected 33 (3 stubs × 11 fields), got {s1_summary['missing_verification_total']}")
        if s1_summary["direct_trade_signal_true_count"] != 0:
            _fail(f"[s1] direct_trade_signal_true_count must be 0")
        # markdown must NOT mention any company sector
        for forbidden_company_bracket in ("[샘플전자]", "[샘플반도체]"):
            if forbidden_company_bracket in s1_md:
                _fail(f"[s1] markdown leaked company bracket {forbidden_company_bracket!r}")
        # markdown must mention all 3 industry sectors
        for sector_bracket in ("[반도체]", "[자동차]", "[화학]"):
            if sector_bracket not in s1_md:
                _fail(f"[s1] markdown missing industry bracket {sector_bracket!r}")

        # Scenario 2: industry_only
        s2_out = tmpdir / "s2"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_industry_only.json"),
              "--out-dir", str(s2_out),
              "--apply"], 0)
        s2_pack = json.loads((s2_out / "2026-04-30" / "industry_summary_pack_stub.json").read_text(encoding="utf-8"))
        s2_summary = json.loads((s2_out / "2026-04-30" / "industry_summary_pack_stub_summary.json").read_text(encoding="utf-8"))
        if len(s2_pack) != 1:
            _fail(f"[s2] expected 1 stub, got {len(s2_pack)}")
        _check_stub_invariants(s2_pack, "s2")
        if s2_summary["selected_company_ignored_count"] != 0:
            _fail(f"[s2] selected_company_ignored_count expected 0")
        if s2_summary["selected_alias_ignored_count"] != 0:
            _fail(f"[s2] selected_alias_ignored_count expected 0")

        # Scenario 3: company_only — should emit 0 stubs.
        s3_out = tmpdir / "s3"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_company_only.json"),
              "--out-dir", str(s3_out),
              "--apply"], 0)
        s3_pack = json.loads((s3_out / "2026-04-30" / "industry_summary_pack_stub.json").read_text(encoding="utf-8"))
        s3_summary = json.loads((s3_out / "2026-04-30" / "industry_summary_pack_stub_summary.json").read_text(encoding="utf-8"))
        if len(s3_pack) != 0:
            _fail(f"[s3] expected 0 stubs, got {len(s3_pack)}")
        if s3_summary["selected_company_ignored_count"] != 1:
            _fail(f"[s3] selected_company_ignored_count expected 1")
        if s3_summary["selected_alias_ignored_count"] != 1:
            _fail(f"[s3] selected_alias_ignored_count expected 1")
        if s3_summary["missing_verification_total"] != 0:
            _fail(f"[s3] missing_verification_total expected 0 (no stubs)")

        # Scenario 4: with_signal_true — exit 3, no files.
        s4_out = tmpdir / "s4"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_with_signal_true.json"),
              "--out-dir", str(s4_out),
              "--apply"], 3)
        if (s4_out / "2026-04-30" / "industry_summary_pack_stub.json").exists():
            _fail("[s4] file written despite exit 3")

        # Guard 1: --out-dir inside repo + --apply → exit 2.
        repo_internal = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "examples" / "_pr41_should_not_exist"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_industry_only.json"),
              "--out-dir", str(repo_internal),
              "--apply"], 2)
        if repo_internal.exists():
            shutil.rmtree(repo_internal, ignore_errors=True)
            _fail("guard1: dir created despite exit 2")

        # Guard 2: --max-stubs > 50 → exit 2.
        g2_out = tmpdir / "g2"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_industry_only.json"),
              "--out-dir", str(g2_out),
              "--max-stubs", "51",
              "--apply"], 2)
        if g2_out.exists():
            _fail("guard2: dir created despite exit 2")

        # Guard 3: dry-run path — must NOT write files.
        g3_out = tmpdir / "g3"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(FIXTURE / "inventory_industry_only.json"),
              "--out-dir", str(g3_out)], 0)
        if g3_out.exists():
            _fail("guard3: dry-run wrote files")

        # Guard 4: wrong inventory schema → exit 2.
        bad_inv = tmpdir / "bad_inv.json"
        bad_inv.write_text(json.dumps({"schema": "wrong:schema:v1"}), encoding="utf-8")
        g4_out = tmpdir / "g4"
        _run([sys.executable, str(SCRIPT),
              "--inventory", str(bad_inv),
              "--out-dir", str(g4_out),
              "--apply"], 2)
        if g4_out.exists():
            _fail("guard4: bad-schema inventory wrote files")

        # Static-grep check: stub generator must NOT iterate over
        # selected_company / selected (it's industry-only by design).
        # We allow the `len(inv.get("selected_company") ...)` reads because
        # they only count for the ignored-count summary; what we forbid
        # is any iteration that would project company entries into the
        # output stubs. Detect via "selected_company" appearing inside a
        # `for` line.
        src = SCRIPT.read_text(encoding="utf-8")
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("for ") and "selected_company" in stripped:
                _fail(f"static-grep: stub generator iterates selected_company in: {stripped!r}")
            if stripped.startswith("for ") and stripped.split()[-2:] == ["in", "selected"]:
                _fail(f"static-grep: stub generator iterates the alias `selected[]` in: {stripped!r}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("PASS run_industry_summary_pack_stub_fixture: 4 scenarios + 4 guards + static-grep "
          "(industry-only invariant verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
