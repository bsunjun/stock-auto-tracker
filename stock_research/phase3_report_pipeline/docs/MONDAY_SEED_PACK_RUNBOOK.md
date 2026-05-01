# Monday Seed Pack — Runbook

A short, end-of-week runbook for producing **the minimum operating pack ChatGPT
will read before Monday's open**, given only the last N days of:

- WiseReport raw PDFs (`<wisereport-root>/<YYYY-MM-DD>/{기업|산업}/*.pdf`)
- Telegram raw attachments (`<telegram-root>/<YYYY-MM-DD>/<channel>/attachments/*`)

It does NOT make buy/sell calls. It does NOT promote anything to `output/latest/`,
the Super Pack, or the rolling-history CSVs. Every emitted row carries
`signal_use=0`.

## What it produces

Under `--out`:

| File | Purpose |
| --- | --- |
| `RAW_SOURCE_INDEX_<YYYYMMDD>.md` | Every source file with date, category, kind, sha256, size |
| `NEWS_REPORT_PACK_<YYYYMMDD>.md` | Per-category narrative summary (company / industry / telegram_event) |
| `MONDAY_SEED_CANDIDATES_<YYYYMMDD>.csv` | Seed candidate rows (no signal). 28 columns; see schema below |
| `MONDAY_SEED_CANDIDATES_latest.csv` | Copy of the dated CSV (created if missing) |
| `DATA_GAP_REPORT_<YYYYMMDD>.md` | Per-row `missing_fields`, `parsed_status` histogram, dry-run log |

## CSV schema (`MONDAY_SEED_CANDIDATES_*.csv`)

```
ticker,name_kr,sector,broker,report_date,title,
category,parsed_status,
sales_old,sales_new,
op_profit_old,op_profit_new,
net_income_old,net_income_new,
eps_old,eps_new,
target_old,target_new,
horizon,confidence,
source_kind,source_path,source_sha256,
missing_fields,signal_use,notes,
as_of,source_key
```

`category` ∈ `{company, industry, telegram_event}`.

`parsed_status` values:

| Value | Meaning |
| --- | --- |
| `estimate_revision_parsed` | pdfplumber + deterministic 표3 regex extracted at least one of `매출/영업이익/순이익/EPS` (old, new) |
| `data_insufficient` | filename meta only; body parse missing or unanchored |
| `industry_meta_only` | industry report — no per-company estimate row by design |
| `event_only` | telegram raw — name + sector + event line, no financials |
| `filename_only_by_flag` | `--no-pdf-parse` was passed |

## Local prerequisites

1. `pip install pdfplumber` for body parse. The script gracefully degrades to
   `data_insufficient` rows when pdfplumber is unavailable.
2. Local `.env` with the Drive paths for your machine. The script honors
   environment fallbacks `WISE_REPORT_ROOT`, `TELEGRAM_ROOT`,
   `PHASE3_OUTPUT_ROOT`. See `.env.example`.

## Standard run (Monday pre-open)

Invoke from the repo root on the operator host where Drive is mounted:

```bash
# As-of Friday close. days_back=4 covers Tue–Wed–Thu–Fri (incl. as-of).
AS_OF=2026-05-01
OUT="$STOCK_RESEARCH_ROOT/03_daily_reports/$AS_OF/monday_seed_pack"

# 1) Dry-run first — no files written.
python3 stock_research/phase3_report_pipeline/scripts/build_monday_seed_pack.py \
  --wisereport-root "$WISE_REPORT_ROOT" \
  --telegram-root   "$TELEGRAM_ROOT" \
  --as-of "$AS_OF" \
  --days-back 4 \
  --out "$OUT"

# 2) Inspect the dry-run summary. Re-run with --apply when satisfied.
python3 stock_research/phase3_report_pipeline/scripts/build_monday_seed_pack.py \
  --wisereport-root "$WISE_REPORT_ROOT" \
  --telegram-root   "$TELEGRAM_ROOT" \
  --as-of "$AS_OF" \
  --days-back 4 \
  --out "$OUT" \
  --apply
```

Then upload all 5 files in `$OUT` to the ChatGPT thread for Monday pre-open.

## Smoke against the synthetic fixture

To verify the schema and CLI shape without touching Drive, see
[`../examples/monday_seed_fixture/README.md`](../examples/monday_seed_fixture/README.md).
The expected outputs are committed under `examples/monday_seed_fixture/expected_outputs/`
so you can `git diff` against your local re-run.

## Invariants

- **Read-only on inputs.** PDFs and telegram files are never modified, moved,
  or copied. Only their bytes are read for sha256 + (optionally) text extraction.
- **`--dry-run` is the default.** `--apply` is required for any file write.
- **No tradeable signal.** Every row's `signal_use=0`. Telegram rows additionally
  carry `notes="telegram event metadata only; explicitly NOT a buy/sell signal"`.
- **`latest` is a copy, not a symlink.** Cross-platform safe.
- **No promotion.** This script does NOT touch `output/latest/`, the rolling
  CSVs in `templates/`, the Super Pack, or any downstream estimate-revision
  rolling pipeline. Promotion remains a separate, double-gated step.
- **`data_insufficient` is preserved verbatim.** The runner never guesses
  `매출 / 영업이익 / 순이익 / EPS` values.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `pdfplumber_available = False` in the gap report | pdfplumber not installed | `pip install pdfplumber` |
| Many rows tagged `parse_error:...` | PDF locked / scanned / non-text | Try Vision OCR via `vision_ocr_pdf.py --extract-mode estimate` (separate cost gate) |
| `ticker_unmapped` in missing_fields | Korean name not in ticker map | Add the row to your `ticker_map` CSV (see `examples/ticker_map.example.csv`) |
| No rows at all | Roots missing or wrong date window | Check `WISE_REPORT_ROOT` / `TELEGRAM_ROOT` and `--as-of` / `--days-back` |
| CSV has my ChatGPT-host paths instead of my Mac paths | Run was on a different host | Re-run on the operator host where Drive is mounted |

## What this runbook does NOT cover

- Body-parse extraction for non-WiseReport PDFs (use `extract_report_estimate_table.py`).
- Estimate-revision rolling history accumulation (use `rolling_append.py --strict-estimate`).
- Promotion to `output/latest/` (use `promote_report_outputs.py --apply --confirm-promote`).
- Kiwoom 수급 CSV / TradingView 차트 CSV / SUPER_PACK_latest.md (out of scope here;
  the user notes those are not yet available — that's expected).
