# Industry Summary Stub — Real-Data Smoke Template

A counter-only smoke procedure that runs the PR #39 / PR #40 scanner
(`scripts/build_wisereport_inventory.py`) and the PR #41 stub generator
(`scripts/build_industry_summary_pack_stub.py`) against an actual
WiseReport `<root>/<YYYY-MM-DD>/산업/` cohort, then reports the
top-level counters only. **No PDF body is read, no Drive content is
mutated, and no inventory / stub / summary file lands inside the
repo.** All artifacts live under `/tmp/...`.

This template is operator-runnable on any host that has the WiseReport
folder mounted (locally or via rclone). For cloud sessions where the
folder is only reachable via the Drive MCP, the procedure also covers
the `/tmp` mirror approach (stub PDFs synthesized from Drive titles —
metadata only).

---

## Procedure (operator host with mounted Drive)

```bash
# 1. Build the wisereport inventory (industry-only).
python3 stock_research/phase3_report_pipeline/scripts/build_wisereport_inventory.py \
    --root /mnt/wisereport \
    --date YYYY-MM-DD \
    --include-industry \
    --out /tmp/wisereport_inventory.json \
    --apply

# 2. Build the LLM summary pack stub from the inventory.
python3 stock_research/phase3_report_pipeline/scripts/build_industry_summary_pack_stub.py \
    --inventory /tmp/wisereport_inventory.json \
    --out-dir   /tmp/industry_summary_pack \
    --apply

# 3. Inspect the top-level counters only.
jq '.summary' /tmp/wisereport_inventory.json
jq '.' /tmp/industry_summary_pack/YYYY-MM-DD/industry_summary_pack_stub_summary.json

# 4. Cleanup. Confirm git status clean.
rm -rf /tmp/wisereport_inventory.json /tmp/industry_summary_pack
git status
```

## Procedure (cloud session with `/tmp` mirror)

For sessions that have only Drive MCP access (no filesystem mount), the
smoke can be exercised against a /tmp mirror that holds same-named stub
files (small ASCII placeholders that are NOT broker PDF body) so the
filesystem-scanner runs end-to-end:

```bash
# 1. Use the Drive MCP to list the parent date folder's 산업 child
#    folder and capture (id, title) pairs. This step is metadata-only;
#    no PDF body downloaded, no Drive mutation.

# 2. Synthesize a /tmp filesystem mirror with the SAME filenames.
mkdir -p /tmp/smoke/wisereport/YYYY-MM-DD/산업
for fn in <list-from-step-1>; do
    printf "REAL-SMOKE STUB BYTES — not real PDF body. fn=%s\n" "$fn" \
        > "/tmp/smoke/wisereport/YYYY-MM-DD/산업/$fn"
done

# 3. Run the scanner + stub generator exactly as in the operator-host
#    procedure above, with `--root /tmp/smoke/wisereport`.

# 4. The reported counters are filename-shape based, so they match
#    the real cohort: industry_pdf_count, sector distribution,
#    malformed/duplicate/non-pdf counts. sha256_prefix_12 will differ
#    from the real cohort (it is the sha of the stub bytes), but that
#    is metadata — no PDF body fingerprint leakage.
```

## Required reporting fields

For every smoke run, surface these counters (and only these):

| field | source | notes |
|---|---|---|
| main HEAD | `git rev-parse HEAD` | so the smoke is reproducible against a fixed scanner / stub-generator |
| `industry_pdf_count` | inventory.summary | # of industry PDFs scanned |
| `selected_company_ignored_count` | stub-pack summary | should be ≥ 0; smoke is industry-only so usually 0 |
| `selected_alias_ignored_count` | stub-pack summary | mirrors `selected_company_ignored_count` (PR #40 alias) |
| `stubs_emitted_count` | stub-pack summary `industry_pdf_count` | should equal inventory.summary `industry_pdf_count` (or be capped at `--max-stubs`) |
| `sector_hint distribution` | stub pack rows | per-sector count, sorted descending then alphabetically |
| `missing_verification_total` | stub-pack summary | exactly `stubs_emitted_count × 11` for an unmodified pack |
| `direct_trade_signal_true_count` | stub-pack summary | **MUST be 0** |
| `trade_signal_truthy_emitted` | stub-pack summary `forbidden_actions_confirmed` | **MUST be 0** |
| `capped_count` | stub-pack summary | non-zero only if cohort > `--max-stubs` |
| `malformed_filename_count` | inventory.summary | filename-regex misses |
| `duplicate_basename_count` | inventory.summary | POSIX-impossible by construction; reported as defensive sanity check |
| `skipped_non_pdf_count` | inventory.summary | non-`.pdf` files in the folder |
| `forbidden_actions_confirmed.*` | both summaries | **all 11 / 10 fields MUST be 0** |
| cleanup confirmed | `ls /tmp/...` empty + `git status` clean | smoke leaves no on-disk or in-repo artifact |

## What the smoke must NEVER produce

- `direct_trade_signal: true` on any stub.
- `trade_signal: <non-null>` on any stub.
- A stub filename pattern with directional verbs (`매수`, `매도`, etc.).
- A stub written into the repo (only `/tmp/...` allowed).
- A modification to any Drive file (read-only listing only).
- A call to OCR / Vision / API / network during stub generation.
- Any change to parser / bridge / merge / build / emit / ticker_map /
  broker autodetect / `build_wisereport_inventory.py` /
  `build_industry_summary_pack_stub.py` source code.

If any of the above appears in the smoke output, **the smoke is
considered failed**, the operator must report the exact violating
record, and the downstream LLM-summary workflow (per
`docs/INDUSTRY_REPORT_HANDOFF_PROMPTS.md`) must NOT be invoked on the
emitted pack until the violation is resolved.

## Result log

Record each completed smoke run as a row in
`docs/INDUSTRY_SUMMARY_REAL_SMOKE_RESULT_LOG.md`. The row carries the
date, main HEAD, and the verified counter values. Older rows are
preserved unchanged so the operator can audit drift over time.
