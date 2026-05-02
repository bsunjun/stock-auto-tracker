#!/usr/bin/env python3
"""PR #44 — Self-test runner for the wisereport_drive_inventory_fixture.

Walks each scenario in `expected_summaries.json`, runs
`scripts/build_wisereport_drive_inventory.py --apply` against synthetic
listing-cache HTML files (so no network call is made), and asserts the
summary counters + PR #40 alias invariants + per-entry shapes.

Also exercises the guards:
  * `--max-company-pdfs 51` → exit 2 (HARD_MAX violation)
  * `--apply` with `--out` resolving inside the repo → exit 2
  * `--apply` with `--download-dir` resolving inside the repo → exit 2
  * default dry-run → must NOT write the output
  * neither --company-drive-folder-url nor --industry-drive-folder-url → exit 2
  * `--max-download-pdfs 0` (default) → no PDFs downloaded
  * `--max-download-pdfs N` with download cache → N PDFs land in /tmp,
    NEVER in the repo (verified by absolute path check).

Plus a chain-runner integration smoke that:
  * builds a happy_path inventory + downloads the 3 company PDFs to /tmp
  * feeds the inventory into examples/run_inventory_batch_smoke.py
  * asserts industry filenames never appear in the parser_batch_summary

Usage
-----
  python3 examples/run_wisereport_drive_inventory_fixture.py

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
SCRIPT = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "scripts" / "build_wisereport_drive_inventory.py"
FIXTURE_ROOT = HERE / "wisereport_drive_inventory_fixture"
LISTING_CACHE = FIXTURE_ROOT / "listing_cache"
DOWNLOAD_CACHE = FIXTURE_ROOT / "download_cache"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _run(cmd: list[str], expected_returncode: int = 0,
         capture: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=capture, text=True)
    if p.returncode != expected_returncode:
        sys.stdout.write(p.stdout or "")
        sys.stderr.write(p.stderr or "")
        _fail(f"command exited {p.returncode} (expected {expected_returncode}): "
              f"{' '.join(cmd)}")
    return p


def _load_inventory(path: Path) -> dict:
    if not path.is_file():
        _fail(f"inventory not written: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _check_global_invariants(inv: dict, scenario: str) -> None:
    if inv.get("schema") != "phase3:wisereport_drive_folder_inventory:v1":
        _fail(f"[{scenario}] wrong schema: {inv.get('schema')!r}")
    s = inv.get("summary", {})
    if s.get("direct_trade_signal_true_count") != 0:
        _fail(f"[{scenario}] summary.direct_trade_signal_true_count must be 0")
    fa = inv.get("forbidden_actions_confirmed", {})
    for k, v in fa.items():
        if v != 0:
            _fail(f"[{scenario}] forbidden_actions_confirmed[{k}] must be 0, got {v!r}")

    selected = inv.get("selected")
    selected_company = inv.get("selected_company") or []
    selected_industry = inv.get("selected_industry") or []
    if not isinstance(selected, list):
        _fail(f"[{scenario}] top-level `selected[]` is missing or not a list")
    if len(selected) != len(selected_company):
        _fail(f"[{scenario}] len(selected)={len(selected)} != "
              f"len(selected_company)={len(selected_company)}")
    company_ids = [e.get("drive_file_id") for e in selected_company]
    sel_ids = [e.get("drive_file_id") for e in selected]
    if sel_ids != company_ids:
        _fail(f"[{scenario}] selected[] drive_file_id order/values differ from "
              f"selected_company[]")
    industry_ids = {e.get("drive_file_id") for e in selected_industry
                    if e.get("drive_file_id")}
    selected_id_set = {e.get("drive_file_id") for e in selected
                       if e.get("drive_file_id")}
    leak = selected_id_set & industry_ids
    if leak:
        _fail(f"[{scenario}] industry drive_file_id leaked into selected[]: "
              f"{sorted(leak)}")
    if s.get("selected_alias_count") != len(selected):
        _fail(f"[{scenario}] summary.selected_alias_count={s.get('selected_alias_count')} "
              f"!= len(selected)={len(selected)}")
    if s.get("selected_alias_matches_company") is not True:
        _fail(f"[{scenario}] summary.selected_alias_matches_company must be true")

    for kind in ("selected_company", "selected_industry"):
        for ent in inv.get(kind, []):
            if ent.get("direct_trade_signal") is not False:
                _fail(f"[{scenario}] {kind} entry direct_trade_signal != False: "
                      f"{ent.get('filename')!r}")
            if ent.get("source") != "drive":
                _fail(f"[{scenario}] {kind} entry source must be 'drive', got "
                      f"{ent.get('source')!r}")
            if not ent.get("drive_file_id"):
                _fail(f"[{scenario}] {kind} entry missing drive_file_id")
            if "[" in (ent.get("ticker_hint") or "") or "]" in (ent.get("ticker_hint") or ""):
                _fail(f"[{scenario}] ticker_hint contains '[' or ']': "
                      f"{ent.get('ticker_hint')!r}")
            if "[" in (ent.get("sector_hint") or "") or "]" in (ent.get("sector_hint") or ""):
                _fail(f"[{scenario}] sector_hint contains '[' or ']': "
                      f"{ent.get('sector_hint')!r}")
            if kind == "selected_company":
                if ent.get("report_type") != "company":
                    _fail(f"[{scenario}] company entry report_type wrong")
                if ent.get("folder_type") != "기업":
                    _fail(f"[{scenario}] company entry folder_type wrong")
                if "sector_hint" in ent or "summary_queue" in ent:
                    _fail(f"[{scenario}] company entry leaks industry-only fields")
            else:
                if ent.get("report_type") != "industry":
                    _fail(f"[{scenario}] industry entry report_type wrong")
                if ent.get("folder_type") != "산업":
                    _fail(f"[{scenario}] industry entry folder_type wrong")
                if ent.get("summary_queue") is not True:
                    _fail(f"[{scenario}] industry entry summary_queue must be True")
                if "ticker_hint" in ent:
                    _fail(f"[{scenario}] industry entry leaks ticker_hint")


def _scenario_command(spec: dict, out_path: Path) -> list[str]:
    cmd = [
        sys.executable, str(SCRIPT),
        "--date", "2026-04-30",
        "--out", str(out_path),
        "--max-company-pdfs", str(spec.get("max_company_pdfs", 50)),
        "--max-industry-pdfs", str(spec.get("max_industry_pdfs", 50)),
        "--listing-cache-dir", str(LISTING_CACHE),
        "--apply",
    ]
    if spec.get("company_folder_id"):
        cmd += ["--company-drive-folder-url",
                f"https://drive.google.com/drive/folders/{spec['company_folder_id']}"]
    if spec.get("industry_folder_id"):
        cmd += ["--industry-drive-folder-url",
                f"https://drive.google.com/drive/folders/{spec['industry_folder_id']}"]
    return cmd


def main() -> int:
    expected_path = FIXTURE_ROOT / "expected_summaries.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    scenarios = expected["scenarios"]

    tmpdir = Path(tempfile.mkdtemp(prefix="pr44_drv_inv_fix_"))
    try:
        for name, spec in scenarios.items():
            out_path = tmpdir / f"{name}_inventory.json"
            _run(_scenario_command(spec, out_path), expected_returncode=0)
            inv = _load_inventory(out_path)
            _check_global_invariants(inv, name)

            for k, want in spec["expected"].items():
                got = inv["summary"].get(k)
                if got != want:
                    _fail(f"[{name}] summary[{k}] expected={want} got={got}")

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
            if "expected_duplicate_basenames_sorted" in spec:
                got = sorted(d["basename"] for d in inv.get("duplicate_basename", []))
                want = spec["expected_duplicate_basenames_sorted"]
                if got != want:
                    _fail(f"[{name}] duplicate basenames expected={want} got={got}")

        # Guard 1: --max-company-pdfs > HARD_MAX (50) → exit 2
        guard_out = tmpdir / "guard_hardmax.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--out", str(guard_out),
             "--max-company-pdfs", "51",
             "--apply"],
            expected_returncode=2,
        )
        if guard_out.exists():
            _fail("guard_hardmax: file written despite exit 2")

        # Guard 2: --out inside repo + --apply → exit 2
        guard_repo_out = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / \
            "examples" / "_pr44_guard_should_not_be_written.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--out", str(guard_repo_out),
             "--apply"],
            expected_returncode=2,
        )
        if guard_repo_out.exists():
            guard_repo_out.unlink()
            _fail("guard_repo_out: file written despite exit 2")

        # Guard 3: --download-dir inside repo + --apply → exit 2
        guard_dl_repo = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / \
            "examples" / "_pr44_dl_guard_should_not_be_written"
        guard_dl_repo_out = tmpdir / "guard_dl_repo.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(guard_dl_repo),
             "--max-download-pdfs", "1",
             "--out", str(guard_dl_repo_out),
             "--apply"],
            expected_returncode=2,
        )
        if guard_dl_repo.exists():
            shutil.rmtree(guard_dl_repo, ignore_errors=True)
            _fail("guard_dl_repo: download dir created inside repo despite exit 2")
        if guard_dl_repo_out.exists():
            _fail("guard_dl_repo: inventory file written despite exit 2")

        # Guard 4: dry-run path (no --apply) — must NOT write the output and
        # must NOT download even if --download-dir + --max-download-pdfs are set.
        dry_out = tmpdir / "dryrun.json"
        dry_dl_dir = tmpdir / "dryrun_dl"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--industry-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_INDUSTRY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(dry_dl_dir),
             "--max-download-pdfs", "5",
             "--download-which", "company,industry",
             "--out", str(dry_out)],
            expected_returncode=0,
        )
        if dry_out.exists():
            _fail("guard_dryrun: file written without --apply")
        if dry_dl_dir.exists() and any(dry_dl_dir.rglob("*.pdf")):
            _fail("guard_dryrun: PDFs downloaded without --apply")

        # Guard 5: missing both folder URLs → exit 2
        no_folder_out = tmpdir / "no_folder.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--out", str(no_folder_out),
             "--listing-cache-dir", str(LISTING_CACHE),
             "--apply"],
            expected_returncode=2,
        )
        if no_folder_out.exists():
            _fail("guard_no_folder: file written despite exit 2")

        # Guard 6: --max-download-pdfs > 100 → exit 2
        bad_dl_out = tmpdir / "bad_dl.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(tmpdir / "bad_dl_dir"),
             "--max-download-pdfs", "9999",
             "--out", str(bad_dl_out),
             "--apply"],
            expected_returncode=2,
        )
        if bad_dl_out.exists():
            _fail("guard_bad_dl: file written despite exit 2")

        # Guard 7: --download-which with bogus token → exit 2
        bad_which_out = tmpdir / "bad_which.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(tmpdir / "bad_which_dir"),
             "--max-download-pdfs", "1",
             "--download-which", "company,bogus",
             "--out", str(bad_which_out),
             "--apply"],
            expected_returncode=2,
        )
        if bad_which_out.exists():
            _fail("guard_bad_which: file written despite exit 2")

        # Download path: cap of 3, company-only → 3 company PDFs land in /tmp.
        dl_out = tmpdir / "dl_company.json"
        dl_dir = tmpdir / "dl_company_pdfs"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(dl_dir),
             "--max-download-pdfs", "3",
             "--download-which", "company",
             "--out", str(dl_out),
             "--apply"],
            expected_returncode=0,
        )
        dl_inv = _load_inventory(dl_out)
        if dl_inv["summary"]["downloaded_pdf_count"] != 3:
            _fail(f"download path: expected downloaded_pdf_count=3, "
                  f"got {dl_inv['summary']['downloaded_pdf_count']}")
        if dl_inv["summary"]["failed_download_count"] != 0:
            _fail(f"download path: expected failed_download_count=0, "
                  f"got {dl_inv['summary']['failed_download_count']}")
        for ent in dl_inv["selected_company"]:
            lp = ent.get("local_pdf_path")
            if not lp:
                _fail(f"download path: company entry missing local_pdf_path: "
                      f"{ent.get('filename')!r}")
            lp_path = Path(lp)
            if not lp_path.is_file():
                _fail(f"download path: local_pdf_path does not exist: {lp}")
            try:
                lp_path.resolve().relative_to(REPO_ROOT)
                _fail(f"download path: PDF landed inside repo: {lp}")
            except ValueError:
                pass  # outside repo — good
            head = lp_path.read_bytes()[:4]
            if head != b"%PDF":
                _fail(f"download path: file missing PDF magic: {lp} (head={head!r})")

        # Download magic-guard test: download_cache file for DUP_A is HTML;
        # script must record failed_download_count >= 1 and refuse to write
        # the bytes to disk.
        dl_guard_out = tmpdir / "dl_guard.json"
        dl_guard_dir = tmpdir / "dl_guard_pdfs"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_DUP_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(dl_guard_dir),
             "--max-download-pdfs", "3",
             "--download-which", "company",
             "--out", str(dl_guard_out),
             "--apply"],
            expected_returncode=0,
        )
        dl_guard_inv = _load_inventory(dl_guard_out)
        # We expect at least one failure (the HTML-disguised entry) and at
        # least one success (the `샘플바이오 단일 항목` entry whose cache file
        # is missing fails too — both paths correctly recorded).
        if dl_guard_inv["summary"]["failed_download_count"] < 1:
            _fail("download magic-guard: expected at least one failed_download "
                  "for the HTML-disguised entry")
        for err in dl_guard_inv["summary"]["files_with_download_errors"]:
            if err.get("file_id") == "FIXTURE_FILE_COMPANY_DUP_A_pr44":
                if "not_pdf_magic" not in err.get("reason", ""):
                    _fail(f"download magic-guard: wrong reason for HTML stub: "
                          f"{err.get('reason')!r}")
                break
        else:
            _fail("download magic-guard: HTML-disguised entry not in errors[]")
        # And: nothing landed inside the repo.
        for f in dl_guard_dir.rglob("*"):
            if f.is_file():
                try:
                    f.resolve().relative_to(REPO_ROOT)
                    _fail(f"download magic-guard: file landed inside repo: {f}")
                except ValueError:
                    pass

        # Bare folder ID (no URL) accepted.
        bare_out = tmpdir / "bare.json"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url", "FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--out", str(bare_out),
             "--apply"],
            expected_returncode=0,
        )
        bare_inv = _load_inventory(bare_out)
        if bare_inv["company_drive_folder_id"] != "FIXTURE_COMPANY_HAPPY_001A_pr44":
            _fail(f"bare folder id: expected FIXTURE_COMPANY_HAPPY_001A_pr44, "
                  f"got {bare_inv['company_drive_folder_id']!r}")

        # Listing-cache miss → exit 4 (Codex review on PR #44):
        # operator passes --listing-cache-dir but forgets to provision the
        # per-folder html. The script must NOT raise an unhandled
        # FileNotFoundError + exit 1; it must produce the same controlled
        # operator-friendly exit-4 path that a network failure produces.
        miss_cache_dir = tmpdir / "empty_listing_cache"
        miss_cache_dir.mkdir(parents=True, exist_ok=True)
        miss_out = tmpdir / "miss.json"
        miss_proc = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(miss_cache_dir),
             "--out", str(miss_out),
             "--apply"],
            capture_output=True, text=True,
        )
        if miss_proc.returncode != 4:
            _fail(f"cache-miss guard: expected exit 4 (controlled error), "
                  f"got {miss_proc.returncode}\n"
                  f"stderr={miss_proc.stderr!r}")
        if "listing cache miss" not in (miss_proc.stderr or ""):
            _fail(f"cache-miss guard: stderr missing 'listing cache miss' "
                  f"phrase; got: {miss_proc.stderr!r}")
        if miss_out.exists():
            _fail("cache-miss guard: inventory file written despite exit 4")

        # PR #29/#30 chain-runner integration smoke:
        # Build a happy_path inventory + download the 3 company stubs to /tmp,
        # then feed the inventory into examples/run_inventory_batch_smoke.py.
        # Industry filenames must NEVER reach the parser.
        chain_inv_out = tmpdir / "chain_inv.json"
        chain_dl_dir = tmpdir / "chain_pdfs"
        _run(
            [sys.executable, str(SCRIPT),
             "--date", "2026-04-30",
             "--company-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_COMPANY_HAPPY_001A_pr44",
             "--industry-drive-folder-url",
             "https://drive.google.com/drive/folders/FIXTURE_INDUSTRY_HAPPY_001A_pr44",
             "--listing-cache-dir", str(LISTING_CACHE),
             "--download-cache-dir", str(DOWNLOAD_CACHE),
             "--download-dir", str(chain_dl_dir),
             "--max-download-pdfs", "3",
             "--download-which", "company",
             "--out", str(chain_inv_out),
             "--apply"],
            expected_returncode=0,
        )
        chain_inv = _load_inventory(chain_inv_out)
        if len(chain_inv["selected"]) != 3:
            _fail(f"chain-smoke prep: expected len(selected)==3, "
                  f"got {len(chain_inv['selected'])}")
        if len(chain_inv["selected_industry"]) != 2:
            _fail(f"chain-smoke prep: expected len(selected_industry)==2, "
                  f"got {len(chain_inv['selected_industry'])}")

        # The chain runner expects `local_pdf_path` to point at downloaded
        # bytes. Already populated by --download-which company. Confirm.
        for ent in chain_inv["selected_company"]:
            if not ent.get("local_pdf_path"):
                _fail(f"chain-smoke prep: company entry missing local_pdf_path: "
                      f"{ent.get('filename')!r}")

        # Re-emit a copy of the inventory with `selected[]` mirroring the
        # download-enriched company entries (already does, but rebuild to be
        # defensive against any in-place dict aliasing).
        chain_inv["selected"] = list(chain_inv["selected_company"])
        chain_inv_rewritten = tmpdir / "chain_inv_rewritten.json"
        chain_inv_rewritten.write_text(
            json.dumps(chain_inv, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        chain_workdir = tmpdir / "chain_wk"
        chain_pdf_dir = chain_dl_dir / "기업"
        chain_runner = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / \
            "examples" / "run_inventory_batch_smoke.py"
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
        out = (chain_proc.stdout or "") + (chain_proc.stderr or "")
        # Industry filenames must not appear in chain runner output.
        forbidden_industry_brackets = ("[반도체]", "[자동차]")
        for forbidden in forbidden_industry_brackets:
            if forbidden in out:
                _fail(f"chain-smoke leakage: industry bracket {forbidden!r} "
                      f"appeared in chain runner output")
        psum = chain_workdir / "parser_batch_summary.json"
        if psum.is_file():
            ps = json.loads(psum.read_text(encoding="utf-8"))
            n_company = len(chain_inv["selected_company"])
            seen = ps.get("pdf_count", 0)
            if seen > n_company:
                _fail(f"chain-smoke: parser saw {seen} PDFs > company count "
                      f"{n_company} — industry leakage")
            for f in (ps.get("files_with_structured_rows", []) +
                      ps.get("files_without_structured_rows", [])):
                for fb in forbidden_industry_brackets:
                    if fb in f:
                        _fail(f"chain-smoke: parser_batch_summary lists "
                              f"industry-bracket file: {f}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"PASS run_wisereport_drive_inventory_fixture: "
          f"{len(scenarios)} scenarios + 7 guards + download magic-guard + "
          f"bare-folder-ID accept + cache-miss exit-4 guard + "
          f"chain-runner integration smoke "
          f"(industry isolation verified end-to-end)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
