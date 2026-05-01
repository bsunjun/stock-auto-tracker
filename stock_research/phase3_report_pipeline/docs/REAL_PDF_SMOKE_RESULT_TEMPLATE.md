# Real-PDF Smoke Result Template (PR #14)

Use this template when you run `extract_report_estimate_table.py --pdf`
on **1–3 real WiseReport PDFs** from your Drive-mounted operator host
and want to share the result back. Paste the filled template into a
**PR comment or chat — never commit it**, since the values reflect real
PDF metadata (sha256 prefixes, broker/ticker hints, target prices).

This is a result schema, not the runbook. The procedure for actually
running the smoke test lives in
[`REALDATA_SAMPLE_RUN.md`](REALDATA_SAMPLE_RUN.md) under the
"PR #14 — Real-PDF pdfplumber smoke (1–3 PDFs)" section.

---

## Hard rules (operator confirms before paste)

- [ ] `pdf_count <= 3`
- [ ] No PDF bytes / extracted text / structured_extraction.json /
      pipeline_summary.json contents are pasted verbatim — only
      counts, sha256 **prefixes**, and aggregate reject reasons.
- [ ] `direct_trade_signal_true_count == 0`
- [ ] `forbidden_actions_confirmed.*` are all 0.
- [ ] No file from the smoke run was committed to the repo (the
      `.gitignore` patterns from PR #11 should already block this; the
      operator double-checks `git status` is clean before pasting).

---

## Template (fill, paste, then DELETE the local file)

```yaml
run_date:                     "YYYY-MM-DD"        # date of the smoke run
operator_host:                "<short label>"     # e.g. "macbook-1", NEVER full hostname/path
pdf_count:                    0                   # MUST be 1, 2, or 3
pdf_filenames:                                    # basenames only; no full paths
  - ""
  - ""
  - ""
pdf_sha256_prefixes:                              # first 12 hex chars only; never full sha
  - ""
  - ""
  - ""

pdfplumber_installed:         null                # true | false
pdfplumber_version:           ""                  # if installed; e.g. "0.11.0"

parser_exit_codes:                                # one per PDF, in the same order as pdf_filenames
  - 0
  - 0
  - 0

# extract_report_estimate_table.py output counts (sum across the 1–3 PDFs)
structured_rows:              0
breakdown_rows:               0
target_price_secondary_rows:  0
direct_trade_signal_true_count: 0                 # MUST be 0; otherwise STOP and report

# After feeding through merge_meta + build --strict + rolling --dry-run
# via run_estimate_revision_dryrun.py (or per-step):
build_rows_in:                0
build_rows_accepted:          0
build_rows_rejected:          0
reject_reason_counts:                             # the reject_reason_counts dict from estimate_revision_summary.json
  complete_not_true: 0
  missing_fields_nonempty: 0
  direction_unknown: 0
  old_target_invalid: 0
  new_target_invalid: 0
  ticker_not_krx: 0
  broker_empty: 0
  date_empty: 0
  horizon_empty: 0

rolling_validated:            0
rolling_rejected:             0
rolling_dup:                  0
rolling_to_add:               0

forbidden_actions_confirmed:
  ocr_or_vision_or_api_calls: 0                   # MUST be 0
  drive_writes:               0                   # MUST be 0
  drive_renames:              0                   # MUST be 0
  latest_updates:             0                   # MUST be 0
  promote_runs:               0                   # MUST be 0
  super_pack_rebuilds:        0                   # MUST be 0
  rolling_apply_runs:         0                   # MUST be 0
  templates_csv_writes:       0                   # MUST be 0
  real_data_repo_commits:     0                   # MUST be 0

notes: |
  # Free-form short notes. Aggregates only — no PDF body excerpts,
  # no broker/target verbatim, no estimated-table text. Examples of
  # what is OK to write here:
  #   - "all 3 PDFs from 2026-04-30/기업 folder"
  #   - "1 of 3 had empty pdfplumber output (image-only PDF)"
  #   - "ticker_map missed 2 of 3 tickers — handing off to PR #15"

# Concrete blocking gaps that will inform PR #14+ scope (PR #15 ticker_map,
# PR #16 OCR fallback, etc.). Only list what was OBSERVED in the smoke run;
# no speculation.
next_parser_gaps:
  - ""
```

---

## Field reference

| Field | Source | Allowed values |
|---|---|---|
| `run_date` | operator clock | `YYYY-MM-DD` |
| `operator_host` | operator-chosen label | short string, no path/hostname leak |
| `pdf_count` | operator | **1, 2, or 3** (any other value is a smoke-run violation) |
| `pdf_filenames` | each PDF's basename | filename only, never full path |
| `pdf_sha256_prefixes` | `sample_inventory.json[selected[].source_pdf_sha256][:12]` | exactly the first 12 hex chars |
| `pdfplumber_installed` | `pip show pdfplumber` rc | `true` / `false` |
| `pdfplumber_version` | `pdfplumber.__version__` | string or `""` if not installed |
| `parser_exit_codes` | `extract_report_estimate_table.py --pdf <each>` exit code | one int per PDF |
| `structured_rows` | `len(structured_extraction.json)` | int (≤ pdf_count) |
| `breakdown_rows` | `len(estimate_table_breakdown.json)` | int (= pdf_count if every parser run succeeded) |
| `target_price_secondary_rows` | `len(target_price_secondary.json)` | int |
| `direct_trade_signal_true_count` | sum of rows with `direct_trade_signal != False` across all output files | **MUST be 0** — otherwise STOP and escalate |
| `build_rows_in` | `pipeline_summary.json[rows_in]` | int |
| `build_rows_accepted` | `pipeline_summary.json[rows_accepted]` | int |
| `build_rows_rejected` | `pipeline_summary.json[rows_rejected]` | int |
| `reject_reason_counts` | `estimate_revision_summary.json[reject_reason_counts]` | dict; absent keys may be omitted |
| `rolling_validated` / `rolling_rejected` / `rolling_dup` / `rolling_to_add` | `pipeline_summary.json` | ints |
| `forbidden_actions_confirmed` | `pipeline_summary.json` + selector inventory + operator self-attest | each MUST be 0 |
| `notes` | operator | aggregates only |
| `next_parser_gaps` | operator | bulleted observations only |

---

## What NOT to paste

- ❌ Verbatim broker name + target price pairs from the PDF body
- ❌ Estimated-table rows (e.g., "매출액 100,000 → 110,000")
- ❌ The full sha256 (use 12-char prefix only)
- ❌ Full source path on the operator host
- ❌ Ticker hints that aren't already public KRX codes
- ❌ Any `structured_extraction.json` / `pipeline_summary.json` content
  copy-pasted as-is (those carry too much detail). Only the
  schema-aligned counters above belong in the result.

---

## Forbidden actions during the smoke run

| Forbidden | Notes |
|---|---|
| Processing more than **3** PDFs | This is a smoke run, not a sample run. PR #11 selector caps at 10 (sample); PR #14 caps at 3. |
| OCR / Vision / API calls | `extract_report_estimate_table.py --ocr` is refused with exit 2 on PR #12/#13. |
| Drive original modify / move / delete | The smoke procedure copies PDF bytes into `/tmp/` only on opt-in (`--copy-pdfs` from PR #11 selector), and never writes back. |
| Updating `latest`, running promote, rebuilding Super Pack | Out of scope. |
| `rolling_append.py --apply` | Strictly dry-run. PR #8's `--strict-estimate --dry-run` only. |
| Generating `direct_trade_signal=true` rows | Phase3 invariant. The build-step gate (PR #7) and runner (PR #9/#10) both refuse to proceed if violated. |
| Committing real PDF / extracted text / output JSON / CSV | `.gitignore` patterns (PR #11) plus operator discipline. |
