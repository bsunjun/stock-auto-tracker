# Industry Catalyst Pack — `phase3:industry_catalyst_pack_stub:v1`

The PR #43 validator (`scripts/validate_industry_summary_pack.py`) reads
a PR #41 `industry_summary_pack_stub:v1` pack (still-empty stubs OR
LLM-filled stubs), runs hard / soft validation per record, and projects
ONLY the records that pass every check into a catalyst pack stub.

The catalyst pack is **review-only sector-rotation context**. It carries
NO directional verb, NO recommendation, NO target-price, NO
position-size, NO `top_pick`, NO `trade_signal`. Downstream consumers
must NEVER convert it into a trading directive.

## Per-row schema

```json
{
  "schema": "phase3:industry_catalyst_pack_stub:v1",
  "report_date": "YYYY-MM-DD",
  "sector": "<from filename bracket>",
  "sub_sector": "<LLM-filled in input>",
  "report_title": "<from filename>",
  "broker_hint": "<LLM-filled in input>",
  "source_file_basename": "<from filename>",
  "sha256_prefix_12": "<12-hex>",
  "core_thesis": "<LLM-filled in input>",
  "catalyst_topology": [
    {"signal": "demand_signal", "summary": "..."},
    {"signal": "supply_signal", "summary": "..."},
    {"signal": "price_signal",  "summary": "..."},
    {"signal": "policy_signal", "summary": "..."},
    {"signal": "capex_signal",  "summary": "..."}
  ],
  "value_chain": [...],
  "beneficiary_candidates": [...],
  "risk_flags": [...],
  "earnings_revision_link_possible": true | false | null,
  "source_confidence": 0.0..1.0 | null,
  "status": "catalyst_pack_emitted",
  "direct_trade_signal": false,
  "trade_signal": null
}
```

### Fields the schema deliberately does NOT include

By construction the per-row schema **does not contain any of**:

- `recommendation`
- `top_pick`
- `target_price` (any spelling)
- `position_size`
- `buy_at` / `sell_at`
- `cut_loss` / `take_profit`

The PR #43 fixture self-test asserts none of these names appear as keys
on any emitted catalyst row.

## Validation classifications (per input record)

| classification | trigger | catalyst pack? |
|---|---|---|
| `valid` | passes every check below | ✓ projected |
| `rejected_pending_summary` | `status == "pending_llm_summary"` (LLM hasn't filled) | ✗ |
| `rejected_missing_verification` | `len(missing_verification) > 0` even with status `llm_summary_filled` | ✗ |
| `rejected_trade_signal_truthy` | `trade_signal` is anything other than `null` or `false` | ✗ |
| `rejected_forbidden_trade_language` | any analytic field contains a phrase from `_FORBIDDEN_TRADE_PATTERNS` | ✗ |
| `rejected_empty_required_field` | `status == "llm_summary_filled"` AND any of the 11 mandatory analytic fields is empty | ✗ |
| `rejected_unknown_status` | `status` is neither `pending_llm_summary` nor `llm_summary_filled`, OR input schema mismatch | ✗ |
| `hard_fail_direct_trade_signal_true` | `direct_trade_signal: true` on any record | exit 3, no files written |

## Forbidden-language patterns

`_FORBIDDEN_TRADE_PATTERNS` (regex; Korean + English; word-boundaried):

- `매수`, `매도` (word-boundaried)
- `비중\s*확대` / `비중\s*축소` / `비중\s*상향` / `비중\s*하향`
- `매수\s*추천`, `매도\s*권고`, `매매\s*신호`, `목표\s*주가`
- `Top\s*Pick`, `Bottom\s*Pick` (case-insensitive)
- `target[\s_]?price`, `cut[\s_]?loss`, `take[\s_]?profit`,
  `position[\s_]?size`, `buy\s+at`, `sell\s+at`,
  `buy\s+now`, `sell\s+now` (case-insensitive)
- `PB[_\s]?READY`, `PB[_\s]?SCOUT`, `PB[_\s]?TRIGGER`
  (case-insensitive — explicitly forbid the legacy Phase 2 broker
  trigger surface from leaking into industry summaries)

## CLI

```
python3 scripts/validate_industry_summary_pack.py \
    --pack    /tmp/industry_summary_pack/<date>/industry_summary_pack_stub.json \
    --out-dir /tmp/industry_catalyst_pack \
    [--date YYYY-MM-DD]      # default: today
    [--apply]
```

Output (apply mode, under `<out-dir>/<date>/`):

| file | schema |
|---|---|
| `industry_catalyst_pack_stub.json` | list of `phase3:industry_catalyst_pack_stub:v1` rows (valid only) |
| `industry_catalyst_pack_stub.md` | paste-in markdown rendering |
| `industry_catalyst_pack_stub_summary.json` | `phase3:industry_catalyst_pack_stub_summary:v1` |
| `validation_summary.json` | `phase3:industry_summary_validation:v1` (per-record verdicts + global counts) |

## Hard invariants

- `--out-dir` resolving inside the repo + `--apply` → exit 2.
- Any input record with `direct_trade_signal: true` → exit 3, no files
  written.
- Default dry-run; `--apply` is the only path that writes files.
- Every emitted catalyst row carries `direct_trade_signal: false`,
  `trade_signal: null`, `status: "catalyst_pack_emitted"`.
- The validator records `forbidden_actions_confirmed.*` all-zero on
  every output, including a dedicated
  `buy_or_sell_recommendation_emitted` counter.
- The validator does not call any LLM, does not touch PDF body text,
  does not modify the input pack file. It is purely a validator +
  projection.

## Self-test

```
python3 stock_research/phase3_report_pipeline/examples/run_industry_summary_validation_fixture.py
```

5 input records (1 valid + 4 distinct rejection buckets) + 1 hard-fail
adversarial pack + 3 guards (repo-out + apply / dry-run no-write /
malformed JSON). PASS only on full coverage.

## Position in the pipeline

```
build_wisereport_inventory.py (PR #39/#40)
    ↓ inventory.selected_industry[]
build_industry_summary_pack_stub.py (PR #41)
    ↓ industry_summary_pack_stub.json   (pending_llm_summary)
LLM (Claude / Gemini / GPT)              ← per docs/INDUSTRY_REPORT_HANDOFF_PROMPTS.md
    ↓ industry_summary_pack_stub.json   (llm_summary_filled)
validate_industry_summary_pack.py (PR #43)
    ↓ industry_catalyst_pack_stub.json  (valid only)
   review-only consumer (NOT rolling_append.py, NOT emit_revision_trend,
                         NOT any --apply path with trade-signal effect)
```
