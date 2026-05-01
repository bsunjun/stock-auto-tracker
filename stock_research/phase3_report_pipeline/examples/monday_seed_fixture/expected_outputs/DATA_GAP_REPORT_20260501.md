# DATA_GAP_REPORT — 2026-05-01

- schema: `monday_seed_pack:v1`
- as_of: `2026-05-01`
- date_window: `2026-04-28` … `2026-05-01`
- pdfplumber_available: `False`
- pdf_parse_skipped_by_flag: `False`
- wisereport_root: `stock_research/phase3_report_pipeline/examples/monday_seed_fixture/wisereport`
- telegram_root: `stock_research/phase3_report_pipeline/examples/monday_seed_fixture/telegram`
- output_dir: `/home/user/stock-auto-tracker/stock_research/phase3_report_pipeline/examples/monday_seed_fixture/expected_outputs`
- latest_csv_was_missing_before_run: `False`

## Missing fields by row

### parsed_status histogram

| parsed_status | count |
| --- | --: |
| `data_insufficient` | 6 |
| `event_only` | 3 |
| `industry_meta_only` | 2 |

### Per-row missing_fields

| date | category | name | parsed_status | missing_fields |
| --- | --- | --- | --- | --- |
| 2026-04-28 | company | 삼성전자 | `data_insufficient` | `pdfplumber_unavailable` |
| 2026-04-29 | company | NAVER | `data_insufficient` | `pdfplumber_unavailable` |
| 2026-04-29 | company | SK하이닉스 | `data_insufficient` | `pdfplumber_unavailable` |
| 2026-04-29 | industry | (none) | `industry_meta_only` | `industry_no_per_company_metrics` |
| 2026-04-29 | telegram_event | 삼성전자 | `event_only` | `financials_not_applicable` |
| 2026-04-30 | company | LG전자 | `data_insufficient` | `pdfplumber_unavailable` |
| 2026-04-30 | telegram_event | 카카오 | `event_only` | `financials_not_applicable` |
| 2026-05-01 | company | HD현대중공업 | `data_insufficient` | `pdfplumber_unavailable` |
| 2026-05-01 | company | 대한조선 | `data_insufficient` | `pdfplumber_unavailable;ticker_unmapped` |
| 2026-05-01 | industry | (none) | `industry_meta_only` | `industry_no_per_company_metrics` |
| 2026-05-01 | telegram_event | 현대차 | `event_only` | `financials_not_applicable` |

## Dry-run / runner log

```
[APPLY] schema=monday_seed_pack:v1  as_of=2026-05-01  days_back=4
[APPLY] date_window = 2026-04-28 ... 2026-05-01
[APPLY] wisereport_root = stock_research/phase3_report_pipeline/examples/monday_seed_fixture/wisereport
[APPLY] telegram_root   = stock_research/phase3_report_pipeline/examples/monday_seed_fixture/telegram
[APPLY] ticker_map = stock_research/phase3_report_pipeline/examples/monday_seed_fixture/ticker_map.fixture.csv (entries=10)
[APPLY] pdfplumber_available = False
[APPLY] total_rows = 11
  telegram:txt: 3
  wisereport_company_pdf: 6
  wisereport_industry_pdf: 2
  parsed_status=data_insufficient: 6
  parsed_status=event_only: 3
  parsed_status=industry_meta_only: 2
[APPLY] out_dir = /home/user/stock-auto-tracker/stock_research/phase3_report_pipeline/examples/monday_seed_fixture/expected_outputs
[APPLY] wrote /home/user/stock-auto-tracker/stock_research/phase3_report_pipeline/examples/monday_seed_fixture/expected_outputs/RAW_SOURCE_INDEX_20260501.md
[APPLY] wrote /home/user/stock-auto-tracker/stock_research/phase3_report_pipeline/examples/monday_seed_fixture/expected_outputs/NEWS_REPORT_PACK_20260501.md
[APPLY] wrote /home/user/stock-auto-tracker/stock_research/phase3_report_pipeline/examples/monday_seed_fixture/expected_outputs/MONDAY_SEED_CANDIDATES_20260501.csv (11 rows)
[APPLY] copied -> /home/user/stock-auto-tracker/stock_research/phase3_report_pipeline/examples/monday_seed_fixture/expected_outputs/MONDAY_SEED_CANDIDATES_latest.csv (replaced existing)
```
