# estimate_table_fixtures

Synthetic Korean text fixtures that exercise `extract_report_estimate_table.py`.
Each `.txt` mimics what a deterministic post-`pdfplumber`-cleanup pass would
hand the parser. **No real WiseReport content.**

## Per-fixture expected outcome

`target_price_secondary.json` is **independent of primary emission**: every
PDF whose 목표주가 line yields a parseable numeric pair is recorded as
`secondary_reference` for audit, regardless of whether a primary row was
also emitted. Target price NEVER becomes a primary estimate row.

| File | Expected primary metric | structured_extraction.json | target_price_secondary.json | Reason |
| --- | --- | --- | --- | --- |
| `broker_a_op_up.txt` | `operating_profit` (up) | ✅ emit | ✅ recorded (`primary_metric_present=True`) | sales / OP / EPS all present; OP wins priority. Target price 80→95 (up) audited. |
| `broker_b_op_only_up_sales_flat.txt` | `operating_profit` (up) | ✅ emit | ✅ recorded (`primary_metric_present=True`) | OP up, sales flat — OP still primary. Target price 240→260 audited. |
| `broker_c_net_income_down.txt` | `net_income` (down) | ✅ emit | ✅ recorded (`primary_metric_present=True`) | NI down, EPS down; NI > EPS in priority. Target price flat (50→50) still audited. |
| `target_price_only.txt` | _none_ | ❌ NOT emit | ✅ recorded (`primary_metric_present=False`) | no metric table; primary must NOT be emitted. Target price 220→250 audited. |
| `malformed_no_numeric.txt` | _none_ | ❌ NOT emit | ❌ NOT recorded | every metric value is a sentinel; target price line is `N/A → N/A` so no numeric pair → secondary builder skips it. |
| `horizon_missing.txt` | `operating_profit` (with empty horizon → build --strict rejects) | ✅ emit | ✅ recorded (`primary_metric_present=True`) | metrics extractable but horizon token absent. Target price 600→650 still audited. |

Expected counts:
- `structured_extraction.json` rows: **4** (broker_a, broker_b, broker_c, horizon_missing)
- `estimate_table_breakdown.json` rows: **6** (one per fixture, audit-only)
- `target_price_secondary.json` rows: **5** (every fixture above except `malformed_no_numeric`)

## Hard guarantees

- `direct_trade_signal` is **always `false`** on every emitted row, in every
  output file, in every mode. main() refuses to write (exit 3) on any leak.
- `target_price_only.txt` must NEVER appear in `structured_extraction.json`.
  It only appears in `target_price_secondary.json` (audit-only).
- `target_price_secondary.json` is **audit-only**. `merge_meta.py` /
  `build_report_estimate_v132.py` / `rolling_append.py` do NOT consume it.
- `estimate_table_breakdown.json` records ALL parsed records (one per
  fixture), regardless of whether the primary path emitted them. Audit-only.

## Notes

- shas in `inventory.json` are deterministic placeholders (`aaaa…`, `bbbb…`, …),
  not real PDF hashes. Real-data shas come from PR #11's selector.
- These fixtures intentionally use only post-cleanup text. PR #12 does not
  parse PDF body bytes; that path lands in a later commit on this branch
  (when `--pdf` is wired up via `pdfplumber`).
