# Phase 3 — Real-data sample dry-run procedure (PR #11)

This document describes the **exact local-execution procedure** for the
"WiseReport 10-PDF sample dry-run" deliverable of PR #11. The procedure
is intentionally **executed by the operator on a Drive-mounted host**
(usually the macOS workstation where Google Drive File Stream is
present), NOT inside the Claude sandbox. None of the steps below write
to Drive, modify originals, or trigger any cost.

## Boundary conditions (read first)

| Forbidden in this PR | Allowed in this PR |
| --- | --- |
| Processing more than **10** PDFs | Read-only Drive scan of one date folder |
| OCR / Vision / API calls | sha256 / size / mtime / filename inventory |
| Modifying / moving / deleting any Drive original | Copying selected PDF bytes into `/tmp/...` (opt-in: `--copy-pdfs`) |
| Updating `latest`, running promote, rebuilding Super Pack | Running `scan_wisereport_company.py` against real Drive (read-only) |
| `rolling_append.py --apply` | `rolling_append.py --strict-estimate --dry-run` |
| Generating `direct_trade_signal=true` rows | The strict gate validating that no such rows ever exist |
| Committing real PDF / CSV / JSON contents to the repo | `.gitignore` patterns that defend against accidental commits |

The strict-mode runner (PR #9 + Codex P2 fix in PR #10) plus the
strict-estimate validator (PR #8) plus the templates-apply guard already
prevent every "forbidden" case above. PR #11 does NOT change those
guards; it only adds a read-only sample selector and this runbook.

## Pre-flight

1. Confirm Drive is mounted and `$GOOGLE_DRIVE_ROOT` resolves to the
   real WiseReport tree, e.g.:
   ```
   echo "$GOOGLE_DRIVE_ROOT"
   # /Users/.../GoogleDrive-.../내 드라이브/stock_research
   ls "$GOOGLE_DRIVE_ROOT/01_data_inbox/wisereport_company/2026-04-30/기업/" | wc -l
   ```
2. Pick the workdir. **Always outside the repo.** Convention: `/tmp/pr11_realdata`.
   ```
   export PR11_WORKDIR=/tmp/pr11_realdata
   rm -rf "$PR11_WORKDIR" && mkdir -p "$PR11_WORKDIR"
   ```
3. `git status` should be clean. The `.gitignore` blocks `_realdata/`,
   `tmp_workdir/`, `pr11_realdata/`, `_pipeline_workdir/` patterns
   inside the repo as a defense in depth.

## Step 1 — Sample select (PR #11 entry point)

```
python3 stock_research/phase3_report_pipeline/scripts/wisereport_sample_select.py \
  --root "$GOOGLE_DRIVE_ROOT/01_data_inbox/wisereport_company" \
  --date 2026-04-30 \
  --include-folder 기업 \
  --max 10 \
  --out "$PR11_WORKDIR"
```

Output: `$PR11_WORKDIR/sample_inventory.json` containing up to 10
records under `selected[]` and any duplicates / overflow under
`skipped[]`. Each record has `filename`, `source_path`, `size_bytes`,
`mtime_iso`, `source_pdf_sha256`, `ticker_hint`, `dup_suspect`.

Hard guarantees:
- `--max` is clamped to 10 (script refuses higher with exit 2).
- `--out` is refused if it lives inside the repo (exit 2).
- `--copy-pdfs` is off by default. Pass it ONLY if you need PDF bytes
  in the workdir for downstream OCR work; even then, the destination
  must remain outside the repo.

## Step 2 — Scan (existing script, read-only)

```
python3 stock_research/phase3_report_pipeline/scripts/scan_wisereport_company.py \
  --report-root "$GOOGLE_DRIVE_ROOT/01_data_inbox/wisereport_company" \
  --output-root "$PR11_WORKDIR" \
  --date 2026-04-30 \
  --apply
# → $PR11_WORKDIR/2026-04-30/scan_company.json
```

Note: `scan_company.json` lists ALL PDFs in the folder (not just the 10
sample). The bridge step joins by sha256 on the manual_meta you supply,
so it naturally restricts to your 10.

## Step 3 — Build a `manual_meta.json` from the inventory

PR #11 does NOT include a PDF body parser. Until one exists (proposed
follow-up below), `manual_meta` rows must be `extraction_method =
"filename_only"` with `broker / old_target / new_target / horizon` left
blank — exactly as `examples/parsed_meta.example.json` shows for the
filename-only case. A minimal generator:

```python
# Run this snippet inside Python; writes a 10-row manual_meta to the workdir.
import json, os
inv = json.load(open(f"{os.environ['PR11_WORKDIR']}/sample_inventory.json"))
manual = [{
    "ticker": r["ticker_hint"],          # bridge's ticker_map will normalize
    "broker": "",
    "report_date": "2026-04-30",
    "old_target": None,
    "new_target": None,
    "horizon": "",
    "filename": r["filename"],
    "confidence": 0.0,
    "extraction_method": "filename_only",
    "source_pdf_sha256": r["source_pdf_sha256"],
    "notes": "pr11_realdata_sample_chain_readiness_test",
} for r in inv["selected"]]
open(f"{os.environ['PR11_WORKDIR']}/manual_meta.json","w").write(
    json.dumps(manual, ensure_ascii=False, indent=2)
)
```

## Step 4 — Bridge → parsed_meta.json (existing script)

```
python3 stock_research/phase3_report_pipeline/scripts/bridge_scan_to_parsed_meta.py \
  --scan-json "$PR11_WORKDIR/2026-04-30/scan_company.json" \
  --manual-meta "$PR11_WORKDIR/manual_meta.json" \
  --ticker-map stock_research/phase3_report_pipeline/examples/ticker_map.example.csv \
  --out "$PR11_WORKDIR/2026-04-30/parsed_meta.json" \
  --apply
```

If a ticker hint isn't in the ticker_map, bridge records
`ticker_unmapped` in `missing_fields` — that's correct, not a failure.
Expand the ticker_map in a separate PR (proposed below).

## Step 5 — Empty `structured_extraction.json`

PR #11 does not run OCR/Vision. Hand the merge step an empty array so
`merge_meta.py` falls back to bridge-only data:

```
echo "[]" > "$PR11_WORKDIR/2026-04-30/structured_extraction.empty.json"
```

## Step 6 — Run the dry-run pipeline runner (PR #9 / #10)

```
python3 stock_research/phase3_report_pipeline/scripts/run_estimate_revision_dryrun.py \
  --date 2026-04-30 \
  --bridge-meta "$PR11_WORKDIR/2026-04-30/parsed_meta.json" \
  --structured  "$PR11_WORKDIR/2026-04-30/structured_extraction.empty.json" \
  --workdir "$PR11_WORKDIR/_pipeline_workdir" \
  --keep-workdir
```

Inspect the result:

```
cat "$PR11_WORKDIR/_pipeline_workdir/pipeline_summary.json"
cat "$PR11_WORKDIR/_pipeline_workdir/2026-04-30/estimate_revision_summary.json"
```

## Expected result on filename-only input (no body parser yet)

`pipeline_summary.json` should look like:
```
strict_enabled                = True
merge_meta_status             = ok
build_status                  = ok
rolling_append_status         = ok
rows_in / accepted / rejected = 10 / 0 / 10
direct_trade_signal_all_false = True
rolling validated/rejected/dup/to_add = 0 / 0 / 0 / 0
forbidden_actions_confirmed   = all 0
```

`estimate_revision_summary.json[reject_reason_counts]` will look like:
```
broker_empty: 10
old_target_invalid: 10
new_target_invalid: 10
horizon_empty: 10
direction_unknown: 10
missing_fields_nonempty: 10
complete_not_true: 10
ticker_not_krx: <8 or fewer once ticker_map is expanded>
```

That is the **correct outcome for PR #11 scope**:
- `accepted = 0` because the strict gate requires `broker / old_target /
  new_target / horizon` (which are NOT present in PDF filenames).
- `direct_trade_signal_all_false = True` (vacuously: nothing accepted,
  nothing can violate the invariant).
- The `reject_reason_counts` enumerate exactly which fields a future
  body parser must fill before accepted ≠ 0 is reachable.

## Auto-extractable today vs. blocked

| Field | Auto-extractable from filename / metadata? | Source |
| --- | --- | --- |
| `ticker` (KRX code) | Partial — needs `ticker_map.csv` lookup on the inferred Korean name | `[..]` bracket in filename |
| `report_date` | Yes | filename `YYYYMMDD` prefix or folder name |
| `filename` | Yes | trivially |
| `source_pdf_sha256` | Yes | bytes |
| `extraction_method=filename_only` | Yes | by definition |
| **`broker`** | **No** | requires PDF body |
| **`old_target`** | **No** | requires PDF body table |
| **`new_target`** | **No** | requires PDF body table |
| **`horizon`** | **No** | requires PDF body |

The four blocked fields are precisely the ones counted in
`reject_reason_counts` above.

## Proposed follow-ups (for separate PRs, with explicit cost gates)

- **PR #12 (parser)**: Implement a deterministic-first PDF body table
  extractor for `broker / old_target / new_target / horizon`. Try
  `pdfplumber` (no API cost) before falling back to `vision_ocr_pdf
  --extract-mode estimate` (which already exists with a cost gate from
  PR #5). Add a fixture covering 5–10 broker template variants.
- **PR #13 (ticker_map expansion)**: Replace
  `examples/ticker_map.example.csv` with a fuller CSV covering the most
  common WiseReport tickers, or fetch it from KRX once and snapshot.
  ticker_map currently has 3 entries — that's why ~80% of the 10-PDF
  sample reports `ticker_not_krx`.
- **PR #14 (OCR cost gate)**: When PR #12's deterministic parser fails,
  fall back to `vision_ocr_pdf.py --extract-mode estimate` per page-1
  only (PR #5 already restricts payload to page 1) — but require
  explicit per-PDF approval, never bulk.

## Forbidden-action verification (run after Step 6)

```
python3 - <<'PY'
import json, os
ps = json.load(open(f"{os.environ['PR11_WORKDIR']}/_pipeline_workdir/pipeline_summary.json"))
inv = json.load(open(f"{os.environ['PR11_WORKDIR']}/sample_inventory.json"))
assert inv["selected_count"] <= 10, "PR #11 hard cap violated"
assert ps["direct_trade_signal_all_false"] is True, "Phase3 invariant violated"
assert all(v == 0 for v in ps["forbidden_actions_confirmed"].values()), \
    f"forbidden_actions_confirmed has non-zero entries: {ps['forbidden_actions_confirmed']}"
assert all(v == 0 for v in inv["forbidden_actions_confirmed"].values() if not isinstance(v, str)), \
    f"selector forbidden_actions_confirmed has non-zero: {inv['forbidden_actions_confirmed']}"
print("PR #11 forbidden-action checks: PASS")
PY
```

If all assertions pass, paste the four blocks below into the PR
verification section:
1. `sample_inventory.json` (selected[] only — never paste source_path
   if it leaks personal directory layout you don't want public)
2. The runner's final summary banner
3. `pipeline_summary.json`
4. `estimate_revision_summary.json[reject_reason_counts]`
