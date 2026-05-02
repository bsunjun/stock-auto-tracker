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

    # PR #40 alias invariants.
    selected = inv.get("selected")
    selected_company = inv.get("selected_company") or []
    selected_industry = inv.get("selected_industry") or []
    if not isinstance(selected, list):
        _fail(f"[{scenario}] PR #40: top-level `selected[]` is missing or not a list: {type(selected).__name__}")
    if len(selected) != len(selected_company):
        _fail(f"[{scenario}] PR #40: len(selected)={len(selected)} != len(selected_company)={len(selected_company)}")
    company_shas = [e.get("source_pdf_sha256_prefix") or e.get("sha256_prefix_12") for e in selected_company]
    sel_shas = [e.get("source_pdf_sha256_prefix") or e.get("sha256_prefix_12") for e in selected]
    if sel_shas != company_shas:
        _fail(f"[{scenario}] PR #40: selected[] sha order/values differ from selected_company[]")
    industry_shas = {e.get("sha256_prefix_12") for e in selected_industry if e.get("sha256_prefix_12")}
    selected_sha_set = {e.get("sha256_prefix_12") for e in selected if e.get("sha256_prefix_12")}
    leak = selected_sha_set & industry_shas
    if leak:
        _fail(f"[{scenario}] PR #40: industry sha leaked into selected[]: {sorted(leak)}")
    if s.get("selected_alias_count") != len(selected):
        _fail(f"[{scenario}] PR #40: summary.selected_alias_count={s.get('selected_alias_count')} != len(selected)={len(selected)}")
    if s.get("selected_alias_matches_company") is not True:
        _fail(f"[{scenario}] PR #40: summary.selected_alias_matches_company must be true, got {s.get('selected_alias_matches_company')!r}")

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

        # PR #40 chain-runner integration smoke:
        # Build a happy_path inventory with BOTH company AND industry, then
        # feed it into the existing PR #29 chain runner. The parser MUST
        # consume only the company entries via the new top-level `selected[]`
        # alias; `selected_industry[]` MUST NOT reach the parser.
        chain_inv_out = tmpdir / "chain_inv.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--root", str(FIXTURE_ROOT / "happy_path"),
             "--date", "2026-04-30",
             "--include-company", "--include-industry",
             "--out", str(chain_inv_out),
             "--apply"],
            expected_returncode=0,
        )
        chain_inv = _load_inventory(chain_inv_out)
        if len(chain_inv["selected"]) != 3:
            _fail(f"chain-smoke prep: expected len(selected)==3, got {len(chain_inv['selected'])}")
        if len(chain_inv["selected_industry"]) != 2:
            _fail(f"chain-smoke prep: expected len(selected_industry)==2, got {len(chain_inv['selected_industry'])}")

        # Parser refuses pdf_path inside the repo by design (PR #29 safety).
        # To exercise the chain runner end-to-end against the alias, copy
        # the company stub PDFs to a /tmp mirror tree and rewrite the
        # inventory's local_pdf_path entries to point there. Industry
        # entries are NOT copied (they should never reach the parser).
        chain_pdf_dir = tmpdir / "chain_pdfs" / "2026-04-30" / "기업"
        chain_pdf_dir.mkdir(parents=True, exist_ok=True)
        for ent in chain_inv["selected_company"]:
            src = Path(ent["local_pdf_path"])
            dst = chain_pdf_dir / src.name
            dst.write_bytes(src.read_bytes())
            ent["local_pdf_path"] = str(dst.resolve())
        # Mirror the rewrite into the alias too (selected[] entries share
        # the same dicts as selected_company[] in build output, but rebuild
        # defensively).
        chain_inv["selected"] = list(chain_inv["selected_company"])
        chain_inv_rewritten = tmpdir / "chain_inv_rewritten.json"
        chain_inv_rewritten.write_text(
            json.dumps(chain_inv, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        chain_workdir = tmpdir / "chain_wk"
        chain_runner = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "examples" / "run_inventory_batch_smoke.py"
        chain_proc = subprocess.run(
            [sys.executable, str(chain_runner),
             "--inventory", str(chain_inv_rewritten),
             "--pdf-dir", str(chain_pdf_dir),
             "--workdir", str(chain_workdir),
             "--max-pdfs", "50",
             "--date", "2026-04-30",
             "--pdf-engine", "pypdf"],
            capture_output=True, text=True,
        )
        # Acceptable outcomes:
        #   (a) Parser processes all 3 company stubs (parsed_pdf_count == 3).
        #   (b) pypdf rejects the synthetic stub bytes and reports
        #       failed_pdf_count > 0 — that's still fine, the relevant
        #       invariant is "industry filenames never reach the parser".
        # In BOTH cases assert:
        #   - pdf_count <= len(selected_company)
        #   - no INDUSTRY filename appears in parser_batch_summary's
        #     files_with_structured_rows / files_without_structured_rows
        #     (we use the exact `[반도체]` / `[자동차]` bracket form so
        #     `[샘플반도체]` company names do NOT false-trigger).
        out = (chain_proc.stdout or "") + (chain_proc.stderr or "")
        forbidden_industry_brackets = ("[반도체]", "[자동차]")
        for forbidden in forbidden_industry_brackets:
            if forbidden in out:
                _fail(f"chain-smoke leakage: industry bracket {forbidden!r} appeared in chain runner output")
        # Look at the parser_batch_summary if it was written.
        psum = chain_workdir / "parser_batch_summary.json"
        if psum.is_file():
            ps = json.loads(psum.read_text(encoding="utf-8"))
            n_company = len(chain_inv["selected_company"])
            seen = ps.get("pdf_count", 0)
            if seen > n_company:
                _fail(f"chain-smoke: parser saw {seen} PDFs > company count {n_company} — industry leakage")
            for f in ps.get("files_with_structured_rows", []) + ps.get("files_without_structured_rows", []):
                for fb in forbidden_industry_brackets:
                    if fb in f:
                        _fail(f"chain-smoke: parser_batch_summary lists industry-bracket file: {f}")
            ind = ps.get("ticker_hint_counts", {}) or {}
            if any(k in ind for k in ("반도체", "자동차")):
                _fail(f"chain-smoke: parser ticker_hint_counts has bare-sector hint: {ind}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"PASS run_wisereport_inventory_fixture: "
          f"{len(scenarios)} scenarios + 4 guards + 1 chain-runner integration smoke "
          f"(industry isolation verified end-to-end)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
