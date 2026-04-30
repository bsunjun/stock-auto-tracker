# estimate_table_fixtures

Synthetic Korean text fixtures that exercise `extract_report_estimate_table.py`.
Each `.txt` mimics what a deterministic post-`pdfplumber`-cleanup pass would
hand the parser. **No real WiseReport content.**

## Per-fixture expected outcome

| File | Expected primary metric (after parser) | structured_extraction.json | target_price_secondary.json | Reason |
| --- | --- | --- | --- | --- |
| `broker_a_op_up.txt` | `operating_profit` (up) | ✅ emit | (also recorded — target price is up) | sales / OP / EPS all present; OP wins priority |
| `broker_b_op_only_up_sales_flat.txt` | `operating_profit` (up) | ✅ emit | (recorded) | OP up, sales flat — OP still primary |
| `broker_c_net_income_down.txt` | `net_income` (down) | ✅ emit | (target price flat — recorded) | NI down, EPS down; NI > EPS in priority |
| `target_price_only.txt` | _none_ | ❌ NOT emit | ✅ recorded as `secondary_reference` | no metric table; primary must NOT be emitted |
| `malformed_no_numeric.txt` | _none_ | ❌ NOT emit | (target price malformed — not recorded) | every metric value is a sentinel |
| `horizon_missing.txt` | `operating_profit` | ✅ emit (with empty horizon → build --strict will reject) | (recorded) | metrics extractable but horizon token absent |

## Hard guarantees

- `direct_trade_signal` is **always `false`** on every emitted row, in every
  output file, in every mode.
- `target_price_only.txt` must NEVER appear in `structured_extraction.json`.
  It only appears in `target_price_secondary.json` (audit-only).
- `estimate_table_breakdown.json` records ALL parsed records (one per
  fixture), regardless of whether the primary path emitted them. It is
  audit-only — `merge_meta.py` does not consume it.

## Notes

- shas in `inventory.json` are deterministic placeholders (`aaaa…`, `bbbb…`, …),
  not real PDF hashes. Real-data shas come from PR #11's selector.
- These fixtures intentionally use only post-cleanup text. PR #12 does not
  parse PDF body bytes; that path lands in a later commit on this branch
  (when `--pdf` is wired up via `pdfplumber`).
