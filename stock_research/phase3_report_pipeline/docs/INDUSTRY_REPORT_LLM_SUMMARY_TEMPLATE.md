# Industry Report LLM Summary Template — `phase3:industry_summary_pack_stub:v1`

**Audience.** Claude / Gemini / GPT instances asked to read a single
WiseReport 산업 (industry) PDF and fill a structured stub. The stub
itself is generated deterministically by
`scripts/build_industry_summary_pack_stub.py` (PR #41) from the
`selected_industry[]` block of a
`phase3:wisereport_date_folder_inventory:v1` inventory (PR #39 / PR #40).

**Hard rule.** Industry reports are NOT trade signals. The LLM must
**never** emit buy/sell/long/short suggestions, target prices, position
sizes, or any artifact that could be ingested as a tradable directive.
Every returned stub must keep `direct_trade_signal: false` and
`trade_signal: null`. If the LLM cannot honor those invariants, it must
refuse the request and return the stub unmodified.

## Required fields

| field | type | notes |
| --- | --- | --- |
| `report_date` | `YYYY-MM-DD` | Pre-filled from inventory. **Do not modify.** |
| `sector` | string | Pre-filled from `[bracket]` in filename. **Do not modify.** |
| `sub_sector` | string | LLM-filled (e.g. `메모리`, `EV 배터리`, `정유`, `복합화력`). |
| `report_title` | string | Pre-filled from filename. **Do not modify.** |
| `broker_hint` | string | LLM-filled. Document author / publishing broker if visible in the PDF. Free-form; no resolver. |
| `source_file_basename` | string | Pre-filled. **Do not modify.** |
| `sha256_prefix_12` | 12-hex | Pre-filled. **Do not modify.** |
| `core_thesis` | string (≤ 3 sentences) | LLM-filled. The single dominant claim of the report. |
| `demand_signal` | string | LLM-filled. End-demand commentary (volume, mix, end-customer). |
| `supply_signal` | string | LLM-filled. Capacity, utilization, inventory, lead-time. |
| `price_signal` | string | LLM-filled. Spot / contract / spread / margin direction. |
| `policy_signal` | string | LLM-filled. Regulation, tariff, subsidy, IRA / EU CBAM / KRX rule changes. |
| `capex_signal` | string | LLM-filled. Announced or implied investment, M&A, divestiture. |
| `value_chain` | array of strings | LLM-filled. Up- / mid- / down-stream tiers mentioned. |
| `beneficiary_candidates` | array of strings | LLM-filled. Bare company names ONLY. **No tickers, no buy/sell verbs**. The downstream pipeline (PR #29 chain runner + PR #38 emitter) is the authoritative source for trade-signal-adjacent data on those companies; this list is a topology hint only. |
| `risk_flags` | array of strings | LLM-filled. Downside risks explicitly raised by the report (e.g. `중국 수요 둔화`, `유가 급등`, `환율 약세`). |
| `earnings_revision_link_possible` | `true` / `false` / `null` | LLM-filled. `true` only if the report explicitly forecasts EPS / OP / sales revisions for ≥ 1 named company; otherwise `false`. `null` only if the LLM did not reach a conclusion. |
| `source_confidence` | `0.0–1.0` (float) or `null` | LLM-filled. Subjective confidence in the LLM's own extraction (NOT the report's own confidence). |
| `missing_verification` | array of strings | LLM-filled. List the analytic fields the LLM was unable to populate from the PDF. A downstream filter requiring `len(missing_verification) == 0` will refuse to promote this stub. |
| `direct_trade_signal` | always `false` | **Hard invariant. Never modify.** |
| `trade_signal` | always `null` | **Hard invariant. Never modify.** |
| `status` | `pending_llm_summary` → `llm_summary_filled` | LLM may set to `llm_summary_filled` ONLY when `len(missing_verification) == 0` AND every analytic field is non-empty. |

## What the LLM must NOT include

- Any `target_price`, `buy_at`, `sell_at`, `cut_loss`, `take_profit`,
  position size, or directional verb such as `매수` / `매도` / `비중확대` / `비중축소` /
  `매수 추천` / `Top Pick` / `Bottom Pick`.
- `direct_trade_signal: true` or any non-`null` `trade_signal` value.
- The original PDF body verbatim. Quote at most short phrases for
  attribution.
- Any speculation about non-listed companies as trade candidates.
- Any modification to the pre-filled metadata fields
  (`report_date`, `sector`, `report_title`, `source_file_basename`,
  `sha256_prefix_12`).

## Acceptance test

A filled stub is acceptable iff:

1. `direct_trade_signal == false` AND `trade_signal == null`.
2. All 5 pre-filled metadata fields are byte-identical to the stub.
3. `status` is either `pending_llm_summary` (still in flight) or
   `llm_summary_filled` (complete).
4. If `status == llm_summary_filled`, then `missing_verification == []`
   AND every required analytic field is non-empty (lists may be empty
   only if the LLM explicitly states "n/a" in `core_thesis`).
5. `beneficiary_candidates` and `risk_flags` contain NO directional
   verbs. (A simple grep on `매수|매도|비중확대|비중축소|Top Pick|Bottom Pick`
   returning matches → reject.)

## Downstream

Filled stubs are consumed by:

- An out-of-band sector-rotation review (human + LLM hybrid) that ranks
  sectors by signal density. **Not** by the PR #29 chain runner, **not**
  by `emit_revision_trend.py`, **not** by any `rolling_append.py`
  invocation.
- The `earnings_revision_link_possible == true` flag may be used as a
  *hint* to look at the company-side PR #38 `report_estimate_high_table_candidates`
  for the named tickers — but the link itself is not a trade signal.

## Schema versioning

`phase3:industry_summary_pack_stub:v1`. Backward-incompatible changes
require a new schema version (`v2`) and a separate PR.
