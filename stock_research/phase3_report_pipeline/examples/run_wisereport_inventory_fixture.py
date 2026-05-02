#!/usr/bin/env python3
"""PR #39 — Self-test runner for the wisereport_inventory_fixture.

Walks each scenario sub-tree under
`examples/wisereport_inventory_fixture/<scenario>/2026-04-30/{기업,산업}/`,
runs `scripts/build_wisereport_inventory.py --apply` against a /tmp output
path, and asserts the summary counters + invariants documented in
`expected_summaries.json`.

It also exercises the two output guards in /tmp:

  * `--max-company-pdfs 51` → exit 2 (HARD_MAX violation)
  * `--apply` with `--out` resolving inside the repo → exit 2

Both checks must NOT write any file.

Usage
-----
  python3 examples/run_wisereport_inventory_fixture.py

Exit code: 0 on PASS, 1 on first FAIL with descriptive stderr message.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
SCRIPT = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "scripts" / "build_wisereport_inventory.py"
FIXTURE_ROOT = HERE / "wisereport_inventory_fixture"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _run(cmd: list[str], expected_returncode: int = 0,
         capture: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=capture, text=True)
    if p.returncode != expected_returncode:
        sys.stdout.write(p.stdout or "")
        sys.stderr.write(p.stderr or "")
        _fail(f"command exited {p.returncode} (expected {expected_returncode}): {' '.join(cmd)}")
    return p


def _load_inventory(path: Path) -> dict:
    if not path.is_file():
        _fail(f"inventory not written: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _check_global_invariants(inv: dict, scenario: str) -> None:
    if inv.get("schema") != "phase3:wisereport_date_folder_inventory:v1":
        _fail(f"[{scenario}] wrong schema: {inv.get('schema')!r}")
    s = inv.get("summary", {})
    if s.get("direct_trade_signal_true_count") != 0:
        _fail(f"[{scenario}] summary.direct_trade_signal_true_count must be 0")
    fa = inv.get("forbidden_actions_confirmed", {})
    for k, v in fa.items():
        if v != 0:
            _fail(f"[{scenario}] forbidden_actions_confirmed[{k}] must be 0, got {v!r}")

    sha_re = re.compile(r"^[0-9a-f]{12}$")
    for kind in ("selected_company", "selected_industry"):
        for ent in inv.get(kind, []):
            if ent.get("direct_trade_signal") is not False:
                _fail(f"[{scenario}] {kind} entry direct_trade_signal != False: {ent.get('filename')!r}")
            if not sha_re.match(ent.get("sha256_prefix_12", "")):
                _fail(f"[{scenario}] {kind} entry sha256_prefix_12 not 12-hex: "
                      f"{ent.get('sha256_prefix_12')!r}")
            if "[" in (ent.get("ticker_hint") or "") or "]" in (ent.get("ticker_hint") or ""):
                _fail(f"[{scenario}] ticker_hint contains '[' or ']': {ent.get('ticker_hint')!r}")
            if "[" in (ent.get("sector_hint") or "") or "]" in (ent.get("sector_hint") or ""):
                _fail(f"[{scenario}] sector_hint contains '[' or ']': {ent.get('sector_hint')!r}")
            if kind == "selected_company":
                if ent.get("report_type") != "company":
                    _fail(f"[{scenario}] company entry report_type wrong")
                if ent.get("folder_type") != "기업":
                    _fail(f"[{scenario}] company entry folder_type wrong")
                if "sector_hint" in ent or "summary_queue" in ent:
                    _fail(f"[{scenario}] company entry leaks industry-only fields: {sorted(ent)}")
            else:
                if ent.get("report_type") != "industry":
                    _fail(f"[{scenario}] industry entry report_type wrong")
                if ent.get("folder_type") != "산업":
                    _fail(f"[{scenario}] industry entry folder_type wrong")
                if ent.get("summary_queue") is not True:
                    _fail(f"[{scenario}] industry entry summary_queue must be True")
                if "ticker_hint" in ent:
                    _fail(f"[{scenario}] industry entry leaks ticker_hint")


def main() -> int:
    expected_path = FIXTURE_ROOT / "expected_summaries.json"
    if not expected_path.is_file():
        _fail(f"expected_summaries.json not found at {expected_path}")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    scenarios = expected["scenarios"]

    tmpdir = Path(tempfile.mkdtemp(prefix="pr39_inv_fix_"))
    try:
        for name, spec in scenarios.items():
            sub_root = FIXTURE_ROOT / spec["_root"]
            if not sub_root.is_dir():
                _fail(f"[{name}] fixture sub-tree missing: {sub_root}")

            out_path = tmpdir / f"{name}_inventory.json"
            cmd = [
                sys.executable, str(SCRIPT),
                "--root", str(sub_root),
                "--date", "2026-04-30",
                "--out", str(out_path),
                "--max-company-pdfs", str(spec.get("max_company_pdfs", 50)),
                "--max-industry-pdfs", str(spec.get("max_industry_pdfs", 50)),
                "--apply",
            ]
            if spec.get("include_company"):
                cmd.append("--include-company")
            if spec.get("include_industry"):
                cmd.append("--include-industry")

            _run(cmd, expected_returncode=0)
            inv = _load_inventory(out_path)
            _check_global_invariants(inv, name)

            for k, want in spec["expected"].items():
                got = inv["summary"].get(k)
                if got != want:
                    _fail(f"[{name}] summary[{k}] expected={want} got={got}")

            # Per-scenario optional list checks.
            if "selected_company_ticker_hints_sorted" in spec:
                got = sorted(e.get("ticker_hint", "") for e in inv.get("selected_company", []))
                want = spec["selected_company_ticker_hints_sorted"]
                if got != want:
                    _fail(f"[{name}] company ticker_hints expected={want} got={got}")
            if "selected_industry_sector_hints_sorted" in spec:
                got = sorted(e.get("sector_hint", "") for e in inv.get("selected_industry", []))
                want = spec["selected_industry_sector_hints_sorted"]
                if got != want:
                    _fail(f"[{name}] industry sector_hints expected={want} got={got}")
            if "expected_malformed_filenames_sorted" in spec:
                got = sorted(m["filename"] for m in inv.get("malformed", []))
                want = spec["expected_malformed_filenames_sorted"]
                if got != want:
                    _fail(f"[{name}] malformed filenames expected={want} got={got}")
            if "expected_skipped_non_pdf_filenames_sorted" in spec:
                got = sorted(m["filename"] for m in inv.get("skipped_non_pdf", []))
                want = spec["expected_skipped_non_pdf_filenames_sorted"]
                if got != want:
                    _fail(f"[{name}] skipped_non_pdf filenames expected={want} got={got}")

        # Guard 1: --max-company-pdfs > HARD_MAX (50) → exit 2
        guard_out = tmpdir / "guard_hardmax.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--root", str(FIXTURE_ROOT / "happy_path"),
             "--date", "2026-04-30",
             "--include-company",
             "--out", str(guard_out),
             "--max-company-pdfs", "51",
             "--apply"],
            expected_returncode=2,
        )
        if guard_out.exists():
            _fail("guard_hardmax: file written despite exit 2")

        # Guard 2: --out inside repo + --apply → exit 2
        guard_repo_out = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "examples" / "_pr39_guard_should_not_be_written.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--root", str(FIXTURE_ROOT / "happy_path"),
             "--date", "2026-04-30",
             "--include-company",
             "--out", str(guard_repo_out),
             "--apply"],
            expected_returncode=2,
        )
        if guard_repo_out.exists():
            guard_repo_out.unlink()
            _fail("guard_repo_out: file written despite exit 2")

        # Guard 3: dry-run path (no --apply) — must NOT write the output.
        dry_out = tmpdir / "dryrun.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--root", str(FIXTURE_ROOT / "happy_path"),
             "--date", "2026-04-30",
             "--include-company",
             "--include-industry",
             "--out", str(dry_out)],
            expected_returncode=0,
        )
        if dry_out.exists():
            _fail("guard_dryrun: file written without --apply")

        # Guard 4: missing both --include-company and --include-industry → exit 2
        no_include_out = tmpdir / "no_include.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--root", str(FIXTURE_ROOT / "happy_path"),
             "--date", "2026-04-30",
             "--out", str(no_include_out),
             "--apply"],
            expected_returncode=2,
        )
        if no_include_out.exists():
            _fail("guard_no_include: file written despite exit 2")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"PASS run_wisereport_inventory_fixture: "
          f"{len(scenarios)} scenarios + 4 guards (hardmax, repo_out, dryrun, no_include)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
