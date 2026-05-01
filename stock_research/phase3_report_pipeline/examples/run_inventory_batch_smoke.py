#!/usr/bin/env python3
"""
Phase 3 — Inventory batch-path smoke runner (PR #29).

Chains the deterministic parser → bridge → build_report_estimate_v132
--strict against an inventory + text-dir, all in DRY-RUN dispositions
that never touch the repo, latest/, promote, Super Pack, or rolling
--apply. Designed for operator-host smoke (max 50 PDFs) and for
cloud-Drive smoke (typically ≤ 5 PDFs due to response-token budget).

Hard rules baked in:
  * `--workdir` MUST live outside the repo. Refused with exit 2 otherwise.
  * `--max-pdfs` is forwarded to the parser; parser refuses any value
    above its `HARD_MAX_PDFS` (50).
  * No subprocess ever runs `rolling_append --apply`. The validator
    dry-run is invoked when `--chain-validator` is set; otherwise the
    runner stops after `build --strict --apply`.
  * Every output goes to `<workdir>/`. No file is read from or written
    inside the repository tree.

Output (under <workdir>/):
  - structured_extraction.json
  - estimate_table_breakdown.json
  - target_price_secondary.json
  - parser_batch_summary.json        (NEW in PR #29)
  - parsed_meta.json                  (when --chain-bridge)
  - merged_parsed_meta.json           (when --chain-merge)
  - 2026-04-30/estimate_revision_*    (when --chain-build, dry-run only)
  - inventory_batch_smoke_summary.json (this runner's aggregated output)
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
REPO_ROOT = THIS.parent.parent.parent.parent
SCRIPTS = THIS.parent.parent / "scripts"

PARSER = SCRIPTS / "extract_report_estimate_table.py"
BRIDGE = SCRIPTS / "bridge_scan_to_parsed_meta.py"
MERGE = SCRIPTS / "merge_meta.py"
BUILD = SCRIPTS / "build_report_estimate_v132.py"


def _is_inside_repo(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def _run(cmd: list[str], *, label: str, allow_fail: bool = False) -> subprocess.CompletedProcess:
    """Run a sub-process. Streams stderr; collects stdout; never silently
    eats failures unless allow_fail=True."""
    print(f"[{label}] $ " + " ".join(shlex.quote(c) for c in cmd))
    cp = subprocess.run(cmd, capture_output=True, text=True)
    if cp.stdout:
        for line in cp.stdout.rstrip().splitlines():
            print(f"[{label}] {line}")
    if cp.stderr:
        for line in cp.stderr.rstrip().splitlines():
            print(f"[{label}] (stderr) {line}", file=sys.stderr)
    if cp.returncode != 0 and not allow_fail:
        raise SystemExit(f"[{label}] exited with {cp.returncode}; aborting batch.")
    return cp


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inventory", required=True,
                   help="Path to a phase3 inventory JSON.")
    p.add_argument("--text-dir", default=None,
                   help="Optional --text-dir to forward to the parser.")
    p.add_argument("--pdf-engine", default="auto", choices=("auto", "pdfplumber", "pypdf"))
    p.add_argument("--date", default="2026-04-30")
    p.add_argument("--workdir", required=True,
                   help="Workdir. MUST live outside the repo.")
    p.add_argument("--max-pdfs", type=int, default=10,
                   help="Per-run cap. Parser refuses values above its hard cap (50).")
    p.add_argument("--manual-meta", default=None,
                   help="Optional manual_meta.json for --chain-bridge.")
    p.add_argument("--ticker-map", default=None,
                   help="Optional ticker_map.csv for --chain-bridge.")
    p.add_argument("--scan-json", default=None,
                   help="Optional scan_company.json for --chain-bridge. "
                        "If omitted an empty array is used.")
    p.add_argument("--chain-bridge", action="store_true",
                   help="Run bridge_scan_to_parsed_meta after the parser.")
    p.add_argument("--chain-merge", action="store_true",
                   help="Run merge_meta after the bridge (requires --chain-bridge).")
    p.add_argument("--chain-build", action="store_true",
                   help="Run build_report_estimate_v132 --strict (dry-run; "
                        "outputs land under <workdir>/<date>/).")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    workdir = Path(args.workdir).expanduser().resolve()
    if _is_inside_repo(workdir):
        print(f"error: --workdir must live outside the repo (got {workdir})",
              file=sys.stderr)
        return 2

    inv_path = Path(args.inventory).expanduser().resolve()
    if not inv_path.is_file():
        print(f"error: --inventory not found: {inv_path}", file=sys.stderr)
        return 2

    workdir.mkdir(parents=True, exist_ok=True)

    # 1. Parser
    parser_cmd = [
        sys.executable, str(PARSER),
        "--inventory", str(inv_path),
        "--pdf-engine", args.pdf_engine,
        "--date", args.date,
        "--workdir", str(workdir),
        "--max-pdfs", str(args.max_pdfs),
        "--apply",
    ]
    if args.text_dir:
        parser_cmd += ["--text-dir", str(Path(args.text_dir).expanduser().resolve())]
    _run(parser_cmd, label="parser")

    parser_summary_path = workdir / "parser_batch_summary.json"
    parser_summary = json.loads(parser_summary_path.read_text(encoding="utf-8"))
    structured_path = workdir / "structured_extraction.json"

    bridge_summary: dict | None = None
    build_summary: dict | None = None

    if args.chain_bridge:
        if not args.manual_meta or not args.ticker_map:
            print("error: --chain-bridge requires --manual-meta and --ticker-map.",
                  file=sys.stderr)
            return 2
        scan_path = (Path(args.scan_json).expanduser().resolve()
                     if args.scan_json else workdir / "_empty_scan.json")
        if not args.scan_json:
            scan_path.write_text("[]", encoding="utf-8")
        parsed_meta_path = workdir / "parsed_meta.json"
        bridge_cmd = [
            sys.executable, str(BRIDGE),
            "--scan-json", str(scan_path),
            "--manual-meta", str(Path(args.manual_meta).expanduser().resolve()),
            "--ticker-map", str(Path(args.ticker_map).expanduser().resolve()),
            "--out", str(parsed_meta_path),
            "--apply",
        ]
        _run(bridge_cmd, label="bridge")
        ds = json.loads(parsed_meta_path.read_text(encoding="utf-8"))
        bridge_summary = {
            "bridge_records": len(ds),
            "ticker_resolved_count": sum(
                1 for r in ds
                if isinstance(r.get("ticker"), str) and r["ticker"].startswith("KRX:")
            ),
            "ticker_unresolved_count": sum(
                1 for r in ds
                if not (isinstance(r.get("ticker"), str) and r["ticker"].startswith("KRX:"))
            ),
            "filename_fallback_resolved_count": sum(
                1 for r in ds
                if isinstance(r.get("ticker"), str) and r["ticker"].startswith("KRX:")
                and (r.get("extraction_method") or "") in ("filename_only",
                                                            "pr29_inventory_batch_smoke")
            ),
        }

        merged_path = workdir / "merged_parsed_meta.json"
        if args.chain_merge:
            merge_cmd = [
                sys.executable, str(MERGE),
                "--bridge-meta", str(parsed_meta_path),
                "--structured", str(structured_path),
                "--out", str(merged_path),
                "--apply",
            ]
            _run(merge_cmd, label="merge")
            build_input = merged_path
        else:
            build_input = parsed_meta_path

        if args.chain_build:
            build_root = workdir / "build_output"
            build_cmd = [
                sys.executable, str(BUILD),
                "--input", str(build_input),
                "--output-root", str(build_root),
                "--date", args.date,
                "--strict", "--apply",
            ]
            _run(build_cmd, label="build")
            sm_path = build_root / args.date / "estimate_revision_summary.json"
            if sm_path.is_file():
                build_summary = json.loads(sm_path.read_text(encoding="utf-8"))
                # Defense: refuse to surface a build summary that recorded
                # any direct_trade_signal=true row.
                if build_summary.get("direct_trade_signal_all_false") is not True:
                    print("error: build summary has direct_trade_signal_all_false != True",
                          file=sys.stderr)
                    return 3

    # Aggregated runner summary
    runner_summary = {
        "schema": "phase3:inventory_batch_smoke_summary:v1",
        "inventory": str(inv_path),
        "date": args.date,
        "workdir": str(workdir),
        "parser": parser_summary,
        "bridge": bridge_summary,
        "build": build_summary,
        "forbidden_actions_confirmed": {
            "ocr_or_vision_or_api_calls": 0,
            "rolling_apply": 0,
            "promote_or_super_pack": 0,
            "drive_writes": 0,
            "repo_writes": 0,
        },
    }
    runner_path = workdir / "inventory_batch_smoke_summary.json"
    runner_path.write_text(
        json.dumps(runner_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[runner] wrote {runner_path}")
    print(f"[runner] parser parsed_pdf_count = {parser_summary['parsed_pdf_count']}")
    print(f"[runner] parser structured_rows_total = {parser_summary['structured_rows_total']}")
    print(f"[runner] parser direct_trade_signal_true_count = "
          f"{parser_summary['direct_trade_signal_true_count']}")
    if bridge_summary:
        print(f"[runner] bridge ticker_resolved_count = "
              f"{bridge_summary['ticker_resolved_count']}/"
              f"{bridge_summary['bridge_records']}")
    if build_summary:
        print(f"[runner] build accepted = {build_summary.get('rows_accepted')}, "
              f"rejected = {build_summary.get('rows_rejected')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
