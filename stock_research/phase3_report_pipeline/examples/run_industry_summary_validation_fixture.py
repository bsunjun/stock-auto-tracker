#!/usr/bin/env python3
"""PR #43 — Self-test runner for the industry_summary_validation fixture.

Runs `scripts/validate_industry_summary_pack.py` against the two fixture
packs under `examples/industry_summary_validation_fixture/` and asserts:

  1. five_pack:
     * exit code 0
     * verdict counts match expected_outcomes.json
     * per-case verdict matches (mapped via sha256_prefix_12)
     * exactly 1 catalyst row emitted
     * every emitted catalyst row carries the hard invariants
     * validation_summary.forbidden_actions_confirmed all-zero
  2. hard_fail_pack:
     * exit code 3
     * NO files written

Plus three guards (`/tmp` only):
  * `--out-dir` resolving inside the repo + `--apply` → exit 2.
  * dry-run path (no `--apply`) writes no files.
  * malformed `--pack` JSON → exit 2.

The runner also asserts that the catalyst row schema does NOT contain
any directional field name (`recommendation`, `top_pick`, `target_price`,
`position_size`, `buy_at`, `sell_at`, `cut_loss`, `take_profit`).
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
SCRIPT = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "scripts" / "validate_industry_summary_pack.py"
FIXTURE = HERE / "industry_summary_validation_fixture"

FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset({
    "recommendation", "top_pick", "target_price", "position_size",
    "buy_at", "sell_at", "cut_loss", "take_profit",
})


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


def _check_catalyst_row(row: dict, scenario: str) -> None:
    if row.get("schema") != "phase3:industry_catalyst_pack_stub:v1":
        _fail(f"[{scenario}] catalyst row schema wrong: {row.get('schema')!r}")
    if row.get("direct_trade_signal") is not False:
        _fail(f"[{scenario}] catalyst row direct_trade_signal != False")
    if row.get("trade_signal") is not None:
        _fail(f"[{scenario}] catalyst row trade_signal != None")
    if row.get("status") != "catalyst_pack_emitted":
        _fail(f"[{scenario}] catalyst row status != 'catalyst_pack_emitted'")
    leaks = [k for k in FORBIDDEN_FIELD_NAMES if k in row]
    if leaks:
        _fail(f"[{scenario}] catalyst row leaked forbidden field names: {leaks}")
    topology = row.get("catalyst_topology")
    if not isinstance(topology, list):
        _fail(f"[{scenario}] catalyst_topology must be a list")


def main() -> int:
    if not SCRIPT.is_file():
        _fail(f"validator script missing: {SCRIPT}")

    expected = json.loads((FIXTURE / "expected_outcomes.json").read_text(encoding="utf-8"))
    five_spec = expected["five_pack"]
    hf_spec = expected["hard_fail_pack"]

    five_pack_path = FIXTURE / five_spec["_pack_file"]
    five_pack = json.loads(five_pack_path.read_text(encoding="utf-8"))
    case_to_sha: dict[str, str] = {r["_fixture_case"]: r["sha256_prefix_12"] for r in five_pack}

    tmpdir = Path(tempfile.mkdtemp(prefix="pr43_val_fix_"))
    try:
        # 1. five_pack run.
        five_out = tmpdir / "five_out"
        _run([sys.executable, str(SCRIPT),
              "--pack", str(five_pack_path),
              "--out-dir", str(five_out),
              "--date", "2026-04-30",
              "--apply"], 0)
        date_dir = five_out / "2026-04-30"
        catalyst_path = date_dir / "industry_catalyst_pack_stub.json"
        catalyst_md_path = date_dir / "industry_catalyst_pack_stub.md"
        catalyst_summary_path = date_dir / "industry_catalyst_pack_stub_summary.json"
        validation_path = date_dir / "validation_summary.json"
        for p in (catalyst_path, catalyst_md_path, catalyst_summary_path, validation_path):
            if not p.is_file():
                _fail(f"five_pack: missing {p}")

        catalyst_rows = json.loads(catalyst_path.read_text(encoding="utf-8"))
        catalyst_summary = json.loads(catalyst_summary_path.read_text(encoding="utf-8"))
        validation_summary = json.loads(validation_path.read_text(encoding="utf-8"))

        # records_in
        if validation_summary["records_in"] != five_spec["expected_records_in"]:
            _fail(f"records_in expected {five_spec['expected_records_in']} got {validation_summary['records_in']}")

        # verdict counts
        for k, want in five_spec["expected_verdict_counts"].items():
            got = validation_summary["verdict_counts"].get(k, 0)
            if got != want:
                _fail(f"verdict_counts[{k}] expected {want} got {got}")

        # catalyst rows count
        if len(catalyst_rows) != five_spec["expected_catalyst_rows"]:
            _fail(f"catalyst_rows expected {five_spec['expected_catalyst_rows']} got {len(catalyst_rows)}")

        # per-case verdict
        sha_to_verdict: dict[str, str] = {pr["sha256_prefix_12"]: pr["verdict"] for pr in validation_summary["per_record"]}
        for case, expected_verdict in five_spec["expected_per_case_verdict"].items():
            sha = case_to_sha[case]
            got = sha_to_verdict.get(sha)
            if got != expected_verdict:
                _fail(f"per-case [{case}] sha={sha}: verdict expected {expected_verdict!r} got {got!r}")

        # validation summary invariants
        for k, want in five_spec["expected_validation_summary_invariants"].items():
            got = validation_summary.get(k)
            if got != want:
                _fail(f"validation_summary[{k}] expected {want} got {got}")

        # forbidden_actions_confirmed all zero
        for k, v in validation_summary["forbidden_actions_confirmed"].items():
            if v != 0:
                _fail(f"validation_summary.forbidden_actions_confirmed[{k}] expected 0 got {v}")

        # catalyst summary invariants
        if catalyst_summary["all_direct_trade_signal_false"] is not True:
            _fail("catalyst_summary.all_direct_trade_signal_false != true")
        if catalyst_summary["all_trade_signal_null"] is not True:
            _fail("catalyst_summary.all_trade_signal_null != true")

        # per-row invariants on the 1 emitted catalyst row
        for row in catalyst_rows:
            _check_catalyst_row(row, "five_pack")

        # markdown sanity: contains the valid sector
        md_text = catalyst_md_path.read_text(encoding="utf-8")
        if "[반도체]" not in md_text:
            _fail("five_pack: catalyst markdown missing valid sector [반도체]")
        # markdown should NOT mention the rejected sectors
        for forbidden_md in ("[자동차]", "[화학]", "[조선]", "[방산]", "[악성]"):
            if forbidden_md in md_text:
                _fail(f"five_pack: catalyst markdown leaked rejected sector {forbidden_md}")

        # 2. hard_fail_pack run.
        hf_pack_path = FIXTURE / hf_spec["_pack_file"]
        hf_out = tmpdir / "hf_out"
        _run([sys.executable, str(SCRIPT),
              "--pack", str(hf_pack_path),
              "--out-dir", str(hf_out),
              "--date", "2026-04-30",
              "--apply"], hf_spec["expected_exit_code"])
        if hf_out.exists():
            files = list(hf_out.rglob("*"))
            if files:
                _fail(f"hard_fail_pack: expected 0 files written, got: {[str(f) for f in files]}")

        # Guard A: --apply + repo-internal --out-dir → exit 2.
        repo_internal = REPO_ROOT / "stock_research" / "phase3_report_pipeline" / "examples" / "_pr43_should_not_exist"
        _run([sys.executable, str(SCRIPT),
              "--pack", str(five_pack_path),
              "--out-dir", str(repo_internal),
              "--apply"], 2)
        if repo_internal.exists():
            shutil.rmtree(repo_internal, ignore_errors=True)
            _fail("guard A: dir created despite exit 2")

        # Guard B: dry-run (no --apply) → exit 0, no files.
        dry_out = tmpdir / "dry_out"
        _run([sys.executable, str(SCRIPT),
              "--pack", str(five_pack_path),
              "--out-dir", str(dry_out)], 0)
        if dry_out.exists():
            _fail("guard B: dry-run wrote files")

        # Guard C: malformed JSON --pack → exit 2.
        bad_pack = tmpdir / "bad_pack.json"
        bad_pack.write_text("{not json", encoding="utf-8")
        guard_c_out = tmpdir / "guard_c_out"
        p = subprocess.run([sys.executable, str(SCRIPT),
                            "--pack", str(bad_pack),
                            "--out-dir", str(guard_c_out),
                            "--apply"], capture_output=True, text=True)
        if p.returncode == 0:
            _fail(f"guard C: malformed JSON returned exit 0 (expected non-zero)")
        if guard_c_out.exists():
            _fail("guard C: dir created despite non-zero exit")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("PASS run_industry_summary_validation_fixture: "
          "5-pack (1 valid + 4 rejection buckets) + 1 hard_fail + 3 guards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
