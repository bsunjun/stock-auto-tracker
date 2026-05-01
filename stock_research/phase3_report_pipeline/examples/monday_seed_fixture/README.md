# Monday Seed Pack — synthetic fixture

This directory holds **fully synthetic** placeholder files used to dry-run /
smoke-test `phase3_report_pipeline/scripts/build_monday_seed_pack.py` without
needing access to a Drive-mounted WiseReport / Telegram tree.

The "PDFs" are **not real PDFs** — they are tiny ASCII placeholders with a
`.pdf` extension. The point of this fixture is to exercise:

1. The 4-day window date walker (`2026-04-28` … `2026-05-01`)
2. The `기업` vs `산업` category split under `<root>/<YYYY-MM-DD>/`
3. The Telegram event extractor under `<root>/<YYYY-MM-DD>/<channel>/attachments/`
4. The filename → `name_kr` / `broker` / `report_date` / `krx_code` heuristic
5. The `data_insufficient` / `event_only` / `industry_meta_only` paths
   (since pdfplumber will refuse to open a non-PDF, those rows correctly
   fall back to `data_insufficient` with `missing_fields=parse_error:...`)

It is NOT a body-parse fixture. To exercise the deterministic body parser
(`매출/영업이익/순이익/EPS`, `수정 후 / 수정 전`), feed real WiseReport PDFs
on the operator host where pdfplumber is installed.

## Layout

```
monday_seed_fixture/
├── README.md
├── ticker_map.fixture.csv             # local map for the synthetic names
├── wisereport/
│   ├── 2026-04-28/기업/...pdf
│   ├── 2026-04-29/{기업,산업}/...pdf
│   ├── 2026-04-30/기업/...pdf
│   └── 2026-05-01/{기업,산업}/...pdf
├── telegram/
│   └── <date>/<channel>/attachments/*.txt
└── expected_outputs/                  # what `--apply` produces against this fixture
    ├── RAW_SOURCE_INDEX_20260501.md
    ├── NEWS_REPORT_PACK_20260501.md
    ├── MONDAY_SEED_CANDIDATES_20260501.csv
    ├── MONDAY_SEED_CANDIDATES_latest.csv
    └── DATA_GAP_REPORT_20260501.md
```

## How to reproduce `expected_outputs/`

```bash
cd <repo-root>
FIX=stock_research/phase3_report_pipeline/examples/monday_seed_fixture
python3 stock_research/phase3_report_pipeline/scripts/build_monday_seed_pack.py \
  --wisereport-root "$FIX/wisereport" \
  --telegram-root   "$FIX/telegram" \
  --ticker-map      "$FIX/ticker_map.fixture.csv" \
  --as-of 2026-05-01 \
  --days-back 4 \
  --out "$FIX/expected_outputs" \
  --apply
```

The same command without `--apply` is the dry-run smoke test.

## Invariants guaranteed by the script

- Source files under `wisereport/` and `telegram/` are read-only — no rename,
  no copy, no delete.
- Every row in the CSV carries `signal_use=0`. Telegram rows additionally
  carry `notes="telegram event metadata only; explicitly NOT a buy/sell signal"`.
- `MONDAY_SEED_CANDIDATES_latest.csv` is a copy of the dated CSV (created
  fresh if missing).
- `data_insufficient` is preserved verbatim; the runner does NOT guess values.
