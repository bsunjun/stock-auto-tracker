# Phase 3 — Real-data sample dry-run procedure (PR #11)

This document describes the **exact local-execution procedure** for the
"WiseReport 10-PDF sample dry-run" deliverable of PR #11. The procedure
is intentionally **executed by the operator on a Drive-mounted host**
(usually the macOS workstation where Google Drive File Stream is
present), NOT inside the Claude sandbox. None of the steps below write
to Drive, modify originals, or trigger any cost.

## Where each part runs

| Environment | What runs there | Real PDFs processed |
| --- | --- | --- |
| **Claude sandbox** (the environment that opened this PR) | mock-tree verification only — proves the selector and the chain handle realistic Korean filenames; uses synthetic fake PDFs in `/tmp/mock_drive_*`. | **0** |
| **Operator host / Mac with Google Drive mounted** | The real 10-PDF sample execution: steps 1–6 below against `$GOOGLE_DRIVE_ROOT/01_data_inbox/wisereport_company/<date>/기업/`. | **up to 10** |

The sandbox cannot reach Drive, so the operator must run the substantive
pass on the Drive-mounted host. **Real-data results are never committed
to the repo.** The `.gitignore` patterns added in PR #11 are a
defense-in-depth backstop; the primary discipline is:

> Paste `pipeline_summary.json` and `reject_reason_counts` as a **PR
> comment or ChatGPT message summary only** — never in a tracked file.

> **PR #11 is not a PDF body parser.** It is the safe sampling step plus
> the operator-run procedure for the later real-data test. The blocking
> fields (`broker / old_target / new_target / horizon`) require a future
> parser PR.

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

## PR #14 — Real-PDF pdfplumber smoke (1–3 PDFs)

After PR #12/#13 the parser supports a `--pdf` single-file path via
`pdfplumber`. The realistic next step on the operator host is a
**very small** smoke test against 1–3 real WiseReport PDFs to confirm
that the deterministic Korean text extraction actually fills the four
blocking fields (`broker / old_target / new_target / horizon`) on real
broker templates, and that nothing leaks out as `direct_trade_signal=true`
or as a primary target-price row.

> Hard cap: **`pdf_count <= 3`** in PR #14. The selector caps at 10 for
> sample runs (PR #11); this smoke is intentionally tighter. If the
> first 3 PDFs reveal parser gaps, fix them in a follow-up PR before
> scaling.

> Real PDF bytes / extracted text / output JSON are NEVER committed to
> the repo. Only the schema-aligned counters in
> [`REAL_PDF_SMOKE_RESULT_TEMPLATE.md`](REAL_PDF_SMOKE_RESULT_TEMPLATE.md)
> get pasted back, and only into a PR comment or chat — not a tracked
> file. The `.gitignore` patterns from PR #11 are a defense-in-depth
> backstop.

> Independently, if a Claude Code **cloud** session needs to find out
> whether it can fetch a single PDF directly from Drive (instead of
> relying on the operator's Mac), follow the
> [`CLOUD_DRIVE_PDF_FETCH_PROBE.md`](CLOUD_DRIVE_PDF_FETCH_PROBE.md)
> runbook (PR #15). It is capped at **`pdf_count == 1`** and is a
> capability probe, not a sample run; PR #14 and PR #15 are independent.

### Where each part runs

| Environment | What runs | Real PDFs processed |
|---|---|---|
| **Claude sandbox** (this PR's CI environment) | docs / template only — no parser execution | **0** |
| **Operator host / Mac with Google Drive mounted** | `pip install pdfplumber`, then PR #14 steps below against 1–3 PDFs | **1–3** |

### Pre-flight (operator host)

1. Ensure the workdir is OUTSIDE the repo:
   ```
   export PR14_WORKDIR=/tmp/pr14_smoke
   rm -rf "$PR14_WORKDIR" && mkdir -p "$PR14_WORKDIR"
   ```
2. Install pdfplumber if missing (deterministic-only, no API cost):
   ```
   python3 -m pip install --user pdfplumber
   python3 -c "import pdfplumber; print(pdfplumber.__version__)"
   ```
   **Or** install the lighter `pypdf` fallback (PR #16) when pdfplumber's
   native dep stack is broken on the host (cffi / cryptography panics on
   some cloud sandboxes):
   ```
   python3 -m pip install --user pypdf
   python3 -c "import pypdf; print(pypdf.__version__)"
   ```
   Either is sufficient. Both are deterministic-only, no OCR/Vision/API.
3. `git status` is clean. The repo's `.gitignore` already blocks
   `_realdata/` / `tmp_workdir/` / `pr11_realdata/` / `_pipeline_workdir/`
   patterns; do not add real-data paths to staging.

### Step 1 — Pick 1–3 PDFs (PR #11 selector reused)

```
python3 stock_research/phase3_report_pipeline/scripts/wisereport_sample_select.py \
  --root "$GOOGLE_DRIVE_ROOT/01_data_inbox/wisereport_company" \
  --date 2026-04-30 \
  --include-folder 기업 \
  --max 3 \
  --copy-pdfs \
  --out "$PR14_WORKDIR"
```

Note `--max 3`: the selector hard-caps at 10 in general but you must
self-cap to 3 here. `--copy-pdfs` materializes the bytes under
`$PR14_WORKDIR/pdfs/` so step 2 can point `--pdf` at a local copy
instead of a Drive path. The selector inventory still records sha256
prefixes for the result template.

### Step 2 — Run the parser per PDF

```
for pdf in "$PR14_WORKDIR"/pdfs/*.pdf; do
  python3 stock_research/phase3_report_pipeline/scripts/extract_report_estimate_table.py \
    --pdf "$pdf" \
    --date 2026-04-30 \
    --workdir "$PR14_WORKDIR/_extract_$(basename "$pdf" .pdf)" \
    --apply
done
```

Optional inspection (text only; **MUST live outside the repo**):

```
python3 stock_research/phase3_report_pipeline/scripts/extract_report_estimate_table.py \
  --pdf "$PR14_WORKDIR/pdfs/<one>.pdf" \
  --date 2026-04-30 \
  --workdir "$PR14_WORKDIR/_extract_dbg" \
  --debug-text-out "$PR14_WORKDIR/_extract_dbg/extracted.txt" \
  --apply
```

If pdfplumber is missing, the parser exits with code 2 and a
`pip install pdfplumber` directive — record this in the result
template's `pdfplumber_installed: false` field instead of forcing the
run.

### Step 3 — Merge each parser output into the chain (per PDF, dry-run)

Build a synthetic single-record bridge_meta per PDF (same shape as
`examples/estimate_table_fixtures/bridge_meta.synthetic.json`) and feed
the per-PDF `structured_extraction.json` through the existing PR #9/#10
runner. Repeat for each of the 1–3 PDFs.

```
python3 stock_research/phase3_report_pipeline/scripts/run_estimate_revision_dryrun.py \
  --date 2026-04-30 \
  --bridge-meta "$PR14_WORKDIR/_extract_<stem>/bridge_meta_for_one.json" \
  --structured  "$PR14_WORKDIR/_extract_<stem>/structured_extraction.json" \
  --workdir     "$PR14_WORKDIR/_pipeline_<stem>" \
  --keep-workdir
```

(The chain itself never calls `--apply` against the real rolling CSV —
PR #8's `--strict-estimate` is dry-run-only inside the runner.)

### Step 4 — Fill `REAL_PDF_SMOKE_RESULT_TEMPLATE.md`, paste, then delete locally

Open
[`REAL_PDF_SMOKE_RESULT_TEMPLATE.md`](REAL_PDF_SMOKE_RESULT_TEMPLATE.md),
fill the YAML block from each step's outputs (sha **prefixes only**, no
verbatim PDF body, no broker/target pairs), and paste the result into a
PR comment or chat. Delete the local filled copy afterwards. The
template's "What NOT to paste" section enumerates the redactions.

### Step 5 — Cleanup

```
rm -rf "$PR14_WORKDIR"
```

### Forbidden-action checklist (operator self-confirms)

| Forbidden | Method that prevents it |
|---|---|
| Processing more than **3** PDFs | Operator self-caps at `--max 3`; selector inventory `selected_count <= 3` after cap. |
| OCR / Vision / API calls | `extract_report_estimate_table.py --ocr` refused (exit 2). pdfplumber is local-only. |
| Drive original modify / move / delete | Selector is read-only; `--copy-pdfs` writes to `$PR14_WORKDIR/pdfs/` only. |
| `latest` updates / promote / Super Pack rebuild | Not invoked by any PR #11/#12/#13/#14 script. |
| `rolling_append.py --apply` | Runner forces `--strict-estimate --dry-run`. |
| Generating `direct_trade_signal=true` rows | Build-step gate (PR #7), runner (PR #9/#10), and parser (PR #12) all refuse to write or proceed if violated. |
| Committing real PDF / extracted text / output JSON | `.gitignore` from PR #11 + operator self-check `git status`. |

## Proposed follow-ups (for separate PRs, with explicit cost gates)

- **PR #12 (parser, MERGED)** — adds `extract_report_estimate_table.py`,
  a deterministic-first parser for `broker / old_target / new_target /
  horizon` operating on PDF body TEXT (not bytes). The synthetic-fixture
  path (`--text` / `--inventory`) is fully verified.
  **Design constraints**:
    - primary metric priority: `operating_profit > net_income > sales > eps`;
    - every PDF with a parseable 목표주가 numeric pair is recorded to
      `target_price_secondary.json` (audit) regardless of primary
      emission; target price NEVER becomes a primary estimate row.
      `merge_meta.py` / `build_report_estimate_v132.py` /
      `rolling_append.py` do NOT consume this file;
    - `direct_trade_signal=false` on every emitted row.
- **PR #13 (pdfplumber path, MERGED)** — wires the `--pdf` single-file
  input through `pdfplumber` (lazy import, no-cost, no OCR/Vision/API).
  Operator must `pip install pdfplumber` before using `--pdf`. Adds
  `--debug-text-out` for inspection, with hard repo-path refusal.
  Inventory-driven batch (`--inventory` selected[] entries → PDFs)
  remains a follow-up; for PR #13 the deterministic batch loop still
  goes through `--text-dir` so the synthetic fixture chain remains the
  single source of truth for regression.
- **PR #16 (pypdf fallback engine, MERGED)** — adds
  `--pdf-engine {auto,pdfplumber,pypdf}` so cloud sandboxes that can't
  import `pdfplumber` (cffi/cryptography native panics) can still run
  via the lighter `pypdf` engine. `auto` (default) tries pdfplumber
  first then falls back to pypdf; both deterministic-only.
- **PR #17 (real WiseReport table layout, MERGED)** — extends the
  parser with a "표3. 실적 전망 / 수정 후 / 수정 전 / 변동률" layout
  reader. Compact + split-line forms both handled; horizon header
  prefers forward-year `YYYYE`. Still deterministic — no OCR. PR #12's
  arrow-pair scanner runs first; PR #17's layout fills only the
  metrics PR #12 missed, so synthetic regression is byte-identical.
- **PR #18 (additional broker-template variants, MERGED)** — adds
  `기존/변경`, `변경 전/변경 후`, `직전/현재` column-header readers
  plus a `<metric>(<year>) <new> <old> ▲|▼|-` side-anchor scanner
  (the indicator is REQUIRED so growth-rate rows without ▲/▼ don't
  produce false positives). Adds an additive `gap_reason` audit
  field on breakdown records: `parsed_metric_pair` /
  `no_revision_anchor` / `no_metric_pair` / `ambiguous_year_pivot` (PR
  #31 sub-categories: `year_pivot_forecast_only_no_revision`,
  `year_pivot_initiation_no_revision`,
  `year_pivot_positional_revision_candidate`,
  `year_pivot_revision_labels_too_far`,
  `year_pivot_has_metric_headers_no_old_new`) /
  `target_price_only` / `empty_text`. Still deterministic — no OCR.
  PR #12 + PR #17 regression byte-identical.
- **PR #19 (side-anchor precision fix, MERGED)** — restricts the
  side-anchor metric scanner to only match within ~15 lines of a
  recognized revision header (직전/현재, 기존/변경, 변경 전/후,
  수정 전/후, 추정치 변경, 추정 변경). Side-anchor patterns far from
  any header are rejected with `gap_reason='side_anchor_no_near_header'`
  to prevent growth-rate / YoY rows from producing false-positive
  primary rows. Adds a new gap_reason
  `side_anchor_header_found_no_metric_pair` for the case where a
  header is found but no eligible metric row sits in its proximity
  window. Target-price side-anchor remains unrestricted (audit-only,
  never primary). PR #12/#17/#18 regression byte-identical.
- **PR #20 (variant column-window precision fix, MERGED)** — applies
  the same precision tightening to the PR #18 variant column-window
  scanner (직전/현재, 기존/변경, 변경 전/후). The scan window is
  capped at 15 lines past the header (down from 40), terminates
  early when a `목표주가` line is hit inside the window, and
  rejects any candidate metric row whose `old`/`new` both have
  `abs<100` for sales/operating_profit/net_income (EPS exempt
  because 원-단위 EPS values can legitimately be small). Rejected
  rows surface as `gap_reason='variant_rejected_growth_rate'`.
  Eliminates the cloud-smoke false positive observed on the real
  대덕전자 PDF where the 40-line window captured an unrelated
  growth-rate row (op `1.9 → -6.2`). Post-fix the same PDF either
  yields the correct revision (op `201 → 251`) or zero structured
  rows. PR #12/#17/#18/#19 regression byte-identical.
- **PR #26 (parser gap follow-up after real-PDF smoke, MERGED)** —
  adds three conservative parser gap helpers triggered by the
  post-PR-#22 5-PDF cloud smoke. (a) Natural-language revision
  regex (`<metric> X에서 Y로 상향/하향`) requires direction word
  + numeric direction match; ambiguity rejects with
  `gap_reason='natural_language_revision_ambiguous'`. (b) Inline
  KV side-anchor (`<metric>(year): 기존 X / 변경 Y`) requires both
  labels inline so PR #18 table-layout does not double-fire.
  (c) Flat duplicate-column audit: when the variant column-window
  scanner reads two byte-identical numeric tokens on the same row,
  the breakdown's metric entry carries
  `audit_flags=['flat_possible_duplicate_column']`. PR #26 also
  introduces `gap_reason='year_pivot_no_revision_pair'` (PR #31
  renamed the surface label to `year_pivot_forecast_only_no_revision`;
  the underlying detector function and truth table are unchanged) for
  the strict forecast-only year-pivot case (no
  목표주가/가이던스/추정치 변경/변동률/revision keywords); the
  legacy PR #18 `ambiguous_year_pivot` path remains for texts with
  those keywords (preserves fixture byte-identity). The 5-PDF
  cloud smoke surfaced `flat_possible_duplicate_column` on LG전자
  (sales 23,733/23,733 AND op 1,673.6/1,673.6) — operator review
  flag without changing primary emission. PR #12/#17/#18/#19/#20/
  #21/#22/#25 regression byte-identical.
- **PR #27 (duplicate-column flat disambiguation, MERGED)** —
  promotes the PR #26 audit flag into a hard rejection in the
  variant column-window scanner. ANY byte-identical `old`/`new`
  raw token pair is now rejected unless the same line carries an
  explicit flat-context marker (`유지 / 동일 / 변동 없음 /
  unchanged / flat / no change`). Rejected rows never enter the
  breakdown's `metrics` dict; when no metric survives the variant
  scan, `gap_reason='duplicate_column_flat_rejected'` fires. The
  PR #26 audit flag is removed. PR #12 arrow-pair flat
  (`<metric> X → X`) is unaffected — it goes through a different
  scanner that does not invoke `validate_flat_revision_pair`. The
  5-PDF cloud smoke drops LG전자 from the structured rows
  (`structured_rows_total`: 2 → 1); 대덕전자 op 201→251 still
  emits cleanly. Three new helpers added: `has_explicit_flat_context`,
  `is_duplicate_column_flat_candidate`, `validate_flat_revision_pair`.
  Four new fixtures
  (`real_layout_duplicate_column_flat_rejected`,
  `real_layout_explicit_flat_allowed`,
  `real_layout_arrow_pair_flat_legacy_allowed`,
  `real_layout_mixed_duplicate_sales_valid_op`) cover the rejected,
  context-allowed, arrow-pair-legacy, and mixed cases. PR #12-#26
  regression byte-identical (PR #26 flat fixture's structured row
  unchanged; only its breakdown changes by intent).
- **PR #32 (ticker resolution improvement for real-PDF batch smoke,
  IN REVIEW)** — bridge / ticker_map enhancement only; parser code is
  not touched. (a) `resources/ticker_map.csv` 3rd expansion adds
  `LX인터내셔널 → KRX:001120` (KOSPI; renamed from LG상사 in 2021,
  ticker code unchanged) and `LG이노텍 → KRX:011070` (KOSPI), each
  with verified KRX-listing governance and aliases. (b)
  `bridge_scan_to_parsed_meta.project_record` learns to consult
  `row.ticker_hint` BEFORE the PR #22 filename-bracket fallback. The
  resolver lookup order is now: `row.ticker(KRX) → ticker_hint →
  row.ticker(legacy) → filename bracket → ticker_unmapped`.
  Conservative: when neither `ticker_hint` nor the bracket appears in
  `ticker_map` the row stays unresolved by design — `대한조선` is
  intentionally absent (private / non-KRX-listed per governance) and
  PR #32 keeps it unresolved. PR #12-#31 parser inventories produce
  identical structured / breakdown / gap_reason outputs (no parser
  code changed). `ticker_resolver_fixture` 31 → 37 PASS; new
  `bridge_filename_fallback_fixture` cases 8 → 13 PASS, including the
  ticker_hint priority paths (`pr32_ticker_hint_lg_innotek_with_bracket`,
  `pr32_ticker_hint_lx_international_no_bracket`,
  `pr32_ticker_hint_daehan_shipyard_excluded`,
  `pr32_existing_krx_preserved_against_hint`,
  `pr32_ticker_hint_alias_lg_sangsa_legacy`). Post-PR-#32 20-PDF
  official `--pdf-dir` runner smoke (same cohort as PR #31 baseline):
  `ticker_resolved_count` 16 → 19, `ticker_unresolved_count` 4 → 1
  (only `대한조선` remains as governance-excluded), `ticker_not_krx`
  build reject 4 → 1, structured_rows / accepted unchanged
  (`대덕전자 op 201→251 up`), `direct_trade_signal_all_false=True`,
  templates md5 unchanged.
- **PR #31 (year-pivot gap taxonomy refinement, IN REVIEW)** — refines
  the legacy `ambiguous_year_pivot` bucket (10/20 PDFs in the PR #30
  20-PDF smoke) into 4 specific sub-categories via a new classifier
  `classify_year_pivot_gap(text)`. Adds gap_reasons:
  `year_pivot_initiation_no_revision`,
  `year_pivot_positional_revision_candidate`,
  `year_pivot_revision_labels_too_far`,
  `year_pivot_has_metric_headers_no_old_new`. Renames PR #26 surface
  label `year_pivot_no_revision_pair` → `year_pivot_forecast_only_no_revision`
  (function `parse_year_pivot_no_revision_pair` and its truth table
  unchanged; only the gap_reason string is renamed). Classifier
  invariants: (a) returns `None` when no year-pivot table is
  detected, (b) returns `None` when no
  `_YEAR_PIVOT_NEUTRAL_KEYWORDS` keyword is present (so PR #26 path
  fires unchanged for the existing forecast-only fixture), (c) PR
  #18 synthetic fixture
  `real_layout_variant_ambiguous_year_pivot.txt` matches no
  sub-category and stays at `ambiguous_year_pivot`. False-positive
  prevention beats recall: the conservative parser refuses to fabricate
  old/new pairs from forecast-only year columns
  (`2024A 2025A 2026E 2027F`); only an explicit `기존(YYYY)` /
  `변경(YYYY)` paired column header (which the existing PR #18
  variant scanner already handles) yields a structured row. Five
  new fixtures live under
  `examples/estimate_table_fixtures/texts/real_layout_year_pivot_*`
  and a new inventory
  `examples/estimate_table_fixtures/inventory.year_pivot_taxonomy.json`
  exercises them through the standard parser CLI. PR #12-#30
  regression: ticker_resolver_fixture 31/31 PASS,
  bridge_filename_fallback_fixture 8/8 PASS, all earlier inventories
  produce identical structured / breakdown counts; only the surface
  gap_reason string changes from `year_pivot_no_revision_pair` →
  `year_pivot_forecast_only_no_revision` for the PR #26 forecast-only
  fixture (rename only). Templates md5 unchanged
  (`6090bfeb9242b17f0fdf653c792d82d7`).
- **PR #30 (real-PDF inventory batch path, MERGED)** — promotes
  the per-PDF Python loop used in the PR #29 operator-host smoke
  into a first-class parser feature. New CLI: `--pdf-dir <DIR>`.
  Per-entry source resolution priority is
  `selected[].local_pdf_path / pdf_path → --pdf-dir/<filename> →
  --text-dir/<stem>.txt`; PR #12-#29 synthetic-text fixtures
  preserve byte-identical structured / breakdown /
  target_price_secondary outputs (verified 24/24 files across
  PR #12-#28 inventories + PR #29 batch_smoke fixture). Missing
  files under `--pdf-dir` are recorded as `source_mode='missing'`
  in the batch summary and surface in
  `files_with_missing_pdf` — the batch never aborts. PDF parse
  failures (both pdfplumber and pypdf exhaust) surface as
  `source_mode='error'` and `files_with_pdf_parse_errors`.
  `selected[].pdf_path` pointing inside the repo is refused at
  entry level so PDF bytes never enter the worktree.
  `parser_batch_summary.json` schema extended additively with
  `source_mode_counts`, `files_with_pdf_parse_errors`,
  `files_with_missing_pdf`. Chain runner gains `--pdf-dir`
  passthrough; cap (`--max-pdfs > 50`) and workdir-in-repo guards
  unchanged. PR #30 is **batch plumbing only** — no new template
  recognition, no SK증권 / 삼성물산 column-positional template,
  no parser rule changes beyond the source-resolution gate.

  Operator-host real-PDF batch smoke recipe (PR #30 official path):
  ```
  python3 stock_research/phase3_report_pipeline/examples/run_inventory_batch_smoke.py \\
      --inventory <real_inventory.json> \\
      --pdf-dir   /tmp/phase3_batch_pdfs \\
      --pdf-engine auto \\
      --workdir   /tmp/phase3_batch_smoke \\
      --max-pdfs  20 \\
      --manual-meta <manual_meta.json> \\
      --ticker-map  stock_research/phase3_report_pipeline/resources/ticker_map.csv \\
      --chain-bridge --chain-merge --chain-build
  ```
  Paste-back: ONLY parser_batch_summary.json +
  inventory_batch_smoke_summary.json counters; never PDF body /
  extracted text / full sha256.

- **PR #29 (inventory batch path for estimate parser smoke, MERGED)** —
  raises the parser's `HARD_MAX_PDFS` from 10 to 50 and adds a
  fourth `--apply` output `parser_batch_summary.json`
  (counter/file-name only — no PDF body / extracted text leaks).
  Schema = `phase3:parser_batch_summary:v1`. Includes a
  `forbidden_actions_confirmed` block that materializes the parser's
  runtime invariants (OCR/Vision/API, direct_trade_signal=true,
  target_price-as-primary, repo writes, drive writes, rolling
  --apply, promote/Super Pack — all 0). `--max-pdfs` default stays
  at 10 so single-PDF smokes are byte-identical to PR #12+ baselines;
  values above 50 exit 2. PR #12-#28 inventories produce 0 diffs on
  structured / breakdown / target_price_secondary (the new summary
  is additive). New chain runner
  `examples/run_inventory_batch_smoke.py` orchestrates parser →
  bridge → merge → build_report_estimate_v132 --strict (dry-run
  friendly; outputs land in `/tmp/<workdir>` only). The runner's
  `--chain-build` checks build summary's
  `direct_trade_signal_all_false=True` and aborts with exit 3
  otherwise. rolling --apply is **never** invoked; workdir-in-repo
  is refused with exit 2. Recommended operator-host smoke:
  `--max-pdfs 20-50` against a real-PDF inventory; cloud smoke caps
  effectively at ≤ 10 due to response-token budget on
  `download_file_content`.

  Operator-host batch smoke recipe:
  ```
  python3 stock_research/phase3_report_pipeline/examples/run_inventory_batch_smoke.py \\
      --inventory <inv.json> \\
      --pdf-engine auto \\
      --workdir   /tmp/phase3_batch_smoke \\
      --max-pdfs  20 \\
      --manual-meta <manual_meta.json> \\
      --ticker-map  stock_research/phase3_report_pipeline/resources/ticker_map.csv \\
      --chain-bridge --chain-merge --chain-build
  ```
  Paste-back: report ONLY `inventory_batch_smoke_summary.json`
  counters; never PDF body / extracted text / full sha.

- **PR #28 (additional side-anchor template variant, MERGED)** —
  adds three conservative side-anchor template guards driven by
  the post-PR-#27 5-PDF cloud smoke residuals (삼성물산
  `side_anchor_header_found_no_metric_pair` and 두산퓨얼셀
  `ambiguous_year_pivot`). Confirmed by anonymized inspection that
  neither PDF has the simpler A/B/C/D sub-forms PR #28 supports
  (삼성물산 = SK증권 multi-column-positional template; 두산퓨얼셀 =
  narrative). PR #28 helpers therefore intentionally do NOT fire
  on the cohort (false-positive prevention beats recall). New
  helpers (`parse_side_anchor_multiline_kv_revision`,
  `collect_metric_context_window`, `extract_labeled_old_new_pair`,
  `reject_percentage_or_margin_context`) handle the multi-line KV
  form (`<metric>(year)?\\n기존 X\\n변경 Y`) and the reversed-
  inline KV form (`<metric>(year): 변경 Y / 기존 X`). PR #26
  inline KV regex now also runs a row-level margin / yoy / (%)
  reject. Four new fixtures
  (`real_layout_side_anchor_multiline_metric_then_values`,
  `real_layout_side_anchor_values_then_metric_rejected`,
  `real_layout_side_anchor_target_price_only_rejected`,
  `real_layout_side_anchor_margin_row_rejected`) cover the admit,
  rejected-no-labels, target-price-only, and margin/yoy reject
  cases. PR #12-#27 regression byte-identical. 5-PDF cloud smoke
  unchanged (structured_rows_total = 1, ticker resolution 5/5,
  direct_trade_signal=true count = 0).
- **PR #14 (OCR cost gate)**: When PR #12+#13's deterministic parser
  fails on a real PDF, fall back to `vision_ocr_pdf.py --extract-mode
  estimate` per page-1 only (PR #5 already restricts payload to page 1)
  — but require explicit per-PDF approval, never bulk.
- **PR #15 (ticker_map expansion)**: Replace
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
