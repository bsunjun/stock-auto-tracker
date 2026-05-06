# PBKR v4 — Screening Builder

> Educational doctrine support tooling. **Not a trade signal.**
> `screening_only = true`. `candidate_generation_only = true`.
> `direct_trade_signal = false`. `automatic_execution_allowed = false`.
> `trade_ticket_generation_allowed = false`. `human_gate_required = true`.

This module implements the **first stage** of PBKR v4: a candidate
generation engine that combines

1. A **primary** Kiwoom REST feature pack (daily OHLCV + flows + MAs +
   ATR) and the locally computed **`pbkr_rs_rank`** (0–100 percentile)
   sourced from the **Kiwoom daily-OHLCV universe**, and
2. An **auxiliary** TradingView MCP scan supplying EMA / price-action /
   pullback / RS-proxy *labels* only, plus
3. KRX / KIND / DART **official risk-flag taxonomy**,

into a single `DAILY_INPUT_PACKET` that the GPT Orchestrator consumes.

This stage **never** produces `PB_READY`, `PB_SCOUT`, `PB_TRIGGER`,
`trade_ticket`, `order_intent`, `order_preparation`,
`execution_artifact`, `automatic_alert`, or
`automatic_execution_hook`.

---

## 1. Layout

```
pbkr_v4_screening_builder/
  builder.py                  # end-to-end orchestrator
  cli.py                      # CLI entry point
  pbkr_rs_rank.py             # 1M/3M/6M/12M weighted percentile
  state_classifier.py         # 5-state classification + state_reason
  screening_filters.py        # filter rules + label generators
  packet_emitter.py           # DAILY_INPUT_PACKET (.json + .md)
  validator.py                # output safety + schema validation
  adapters/
    tradingview_mcp.py        # AUXILIARY scan normalization
    kiwoom_rest.py            # PRIMARY feature normalization
    official_risk.py          # KR designation taxonomy mapping
  schemas/
    tradingview_scan_pack.schema.json
    kiwoom_feature_pack.schema.json
    official_risk_flags_pack.schema.json
    screening_candidates_pack.schema.json
    daily_input_packet.schema.json
  fixtures/                   # synthetic-only; no real tickers/data
```

## 2. Hard rules (enforced)

* `screening_only = true` and `candidate_generation_only = true` on
  every output pack.
* `direct_trade_signal = false`, `trade_signal = false|null`,
  `automatic_execution_allowed = false`,
  `trade_ticket_generation_allowed = false`,
  `human_gate_required = true`.
* The screening builder **never** emits any of:
  `PB_TRIGGER`, `PB_READY`, `PB_SCOUT`, `trade_ticket`,
  `order_intent`, `order_preparation`, `execution_artifact`,
  `automatic_alert`, `automatic_execution_hook`. The post-write
  verifier counts each of these and asserts zero.
* Outputs land in a local/private directory; the default is
  `$PBKR_SCREENING_OUT` or `/tmp/pbkr_v4_screening_out/<date>`. The
  CLI refuses `--out-dir` paths inside the repo.
* Repo contains code, schemas, docs, and **synthetic** fixtures only.
  No real OHLCV / no real ticker name / no real designation row /
  no broker response / no API key may be committed.
* `account_no`, `order_no`, `api_key`, `token`, `password`,
  `broker_response` are rejected by `validator.py::sanitize_payload`.

## 3. Inputs

### 3.1 TradingView MCP scan — **AUXILIARY**
TradingView's free Screener does not always expose `RS_SCORE`, so the
engine **never requires** RS_SCORE / RS_PROXY. The adapter normalizes
each row into four auxiliary fields:

| Field | Meaning |
|---|---|
| `tv_ema_state` | categorical (`above_21ema`, `at_21ema`, `below_21ema`, `alignment_up`, `alignment_down`, `mixed`) |
| `tv_price_action_label` | short label (≤ 64 chars) |
| `tv_pullback_state` | categorical (`none`, `shallow`, `deep`, `broken`) |
| `tv_rs_proxy_label` | categorical (`high`, `mid`, `low`, `absent`) |

`tv_rs_proxy_label` is **never** used as a hard filter. If the MCP
server provides a numeric RS_SCORE, the adapter buckets it
(`>=80 → "high"`, `>=50 → "mid"`, `<50 → "low"`); otherwise the label
is `"absent"`.

### 3.2 Kiwoom REST features — **PRIMARY**
Per ticker: daily OHLCV, `trading_value`, `volume_ratio`,
`investor_flow`, `foreigner_flow`, `institution_flow`,
`financial_investment_flow`, `ma9`, `ma21`, `ma50`, `ma120`,
`atr14`, `recent_low`, `stop_distance`. Plus a separate universe
close-series file used by the RS calculator.

### 3.3 PBKR_RS_RANK — **PRIMARY relative-strength feature**
Computed locally from the Kiwoom daily-OHLCV universe.
`pbkr_rs_rank_source = "kiwoom_daily_universe"` is asserted on every
output that carries the rank.

| Horizon | Weight |
|---|---|
| 1M  | 0.20 |
| 3M  | 0.30 |
| 6M  | 0.30 |
| 12M | 0.20 |

Optional benchmark-relative blend when a benchmark close-series is
supplied. The first relative-strength condition is
`pbkr_rs_rank >= 80`. There is no `RS_SCORE >= 80` filter and the
engine refuses to gate on TradingView RS_SCORE.

### 3.4 Official risk flags
KRX / KIND / DART taxonomy. See `adapters/official_risk.py`. Risk
buckets at the input layer:

* `HARD_EXCLUDE` — administrative / delisting / halt / unfaithful
  disclosure / non-standard audit / capital impairment.
* `EXTREME_RISK_FLAG_WATCH` — `투자위험` / `투자위험 지정예고`.
* `REGULAR_PB_EXCLUDE` — `투자주의` / `투자경고` / `단기과열`.
* `RISK_FLAG_PULLBACK_WATCH` — same designations as
  `REGULAR_PB_EXCLUDE` but the tape is constructive enough to *watch*
  (still **not** a `PB_TRIGGER`).

Market-structure events (sidecar / circuit breaker / opening-or-closing
auction window) feed the `SCREENING_EXCLUDE` state at the screening
layer (reason: `market_structure`).

## 4. Screening filters

A candidate must satisfy:

* `pbkr_rs_rank >= 80`
* `trading_value >= min_trading_value` (configurable; default 5e9 KRW)
* `close >= ma21` **or** `ma9 >= ma21 >= ma50` (alignment)
* `ma50 >= ma120` (long trend up)
* recent strong trend / breakout / first-pullback evidence
  (price action or pullback label is non-empty, or close near 20–60d high)

Generated labels:

* `volume_state_label`  — `dry`, `normal`, `expansion`, `climax`
* `pullback_state_label` — `none`, `shallow`, `deep`, `broken`
* `stop_distance_label` — `tight`, `normal`, `wide`

## 5. Screening-layer states (5-state contract)

The candidate's `state` field is **always** one of:

| State | Meaning |
|---|---|
| `WATCH_CANDIDATE` | clean, all five filters pass |
| `WATCH_ONLY` | clean, partial filters |
| `RISK_FLAG_PULLBACK_WATCH` | `REGULAR_PB_EXCLUDE` designation + constructive tape (rs_pass + trend_pass + ema_pass). **Watch only.** Never promotes to `PB_TRIGGER`. |
| `REGULAR_PB_EXCLUDE` | `투자주의` / `투자경고` / `단기과열` without constructive tape |
| `SCREENING_EXCLUDE` | hard designation, market structure active, or extreme risk flag |

A separate `state_reason` enum (`hard_designation`, `market_structure`,
`extreme_risk_flag`, `regular_pb_designation_watch`,
`regular_pb_designation`, `all_filters_pass`, `partial_filters`)
preserves traceability without expanding the state set.

The risk-flag bucket taxonomy at the input layer
(`HARD_EXCLUDE` / `EXTREME_RISK_FLAG_WATCH` / `REGULAR_PB_EXCLUDE` /
`RISK_FLAG_PULLBACK_WATCH`) is preserved on the official-risk pack
and on each candidate's `risk.buckets` field.

## 6. Outputs

Written to `$PBKR_SCREENING_OUT/<YYYY-MM-DD>/`:

* `tradingview_scan_pack.json`    (auxiliary)
* `kiwoom_feature_pack.json`      (primary)
* `official_risk_flags_pack.json`
* `screening_candidates_pack.json`
* `daily_input_packet.json`       (canonical for GPT Orchestrator)
* `daily_input_packet.md`         (human-readable summary)

Both the JSON and the MD assert
`screening_only=true`, `candidate_generation_only=true`,
`direct_trade_signal=false`, `automatic_execution_allowed=false`,
`trade_ticket_generation_allowed=false`. The post-write verifier
asserts zero counts for every forbidden artifact token.

## 7. Run

The CLI exposes two subcommands.

### 7.1 `screen` — offline / fixture / dev

```bash
python -m stock_research.pbkr_v4_screening_builder.cli screen \
    --tradingview stock_research/pbkr_v4_screening_builder/fixtures/tradingview_scan_synthetic.json \
    --kiwoom-features stock_research/pbkr_v4_screening_builder/fixtures/kiwoom_features_synthetic.json \
    --kiwoom-universe stock_research/pbkr_v4_screening_builder/fixtures/kiwoom_universe_synthetic.json \
    --official-risk stock_research/pbkr_v4_screening_builder/fixtures/official_risk_synthetic.json \
    --asof 2026-05-06 \
    --out-dir /tmp/pbkr_v4_screening_out
```

(For backward compatibility, omitting the `screen` subcommand and
passing the flags directly is still accepted.)

### 7.2 `live-screen` — real live inputs (read-only)

```bash
python -m stock_research.pbkr_v4_screening_builder.cli live-screen \
    --date 2026-05-06 \
    --kiwoom-features /Users/bsunjun/trading/phase3/input/kiwoom_features_latest.json \
    --kiwoom-universe /Users/bsunjun/trading/phase3/input/kiwoom_universe_latest.json \
    --tradingview    /Users/bsunjun/trading/phase3/input/tradingview_scan_latest.json \
    --official-risk  /Users/bsunjun/trading/phase3/input/official_risk_flags_latest.json \
    --output-dir     /Users/bsunjun/trading/phase3/output/pbkr_screening/20260506 \
    --no-execution
```

Runner contract (enforced):

* `--no-execution` is **required**. There is no execution mode; the
  flag is a forcing function.
* `--output-dir` defaults to `${PBKR_LIVE_SCREENING_OUT_BASE}/<YYYYMMDD>`
  (default base `/Users/bsunjun/trading/phase3/output/pbkr_screening`)
  and **must** resolve outside the repository.
* Every input source must be an existing, non-empty file. The runner
  **never** silently substitutes a synthetic / mock input on missing
  source — it fails loudly.
* In addition to the four standard packs and the
  `daily_input_packet.{json,md}`, a `verification_report.json` is
  emitted that records every doctrinal counter and asserts
  `pass: true`. The schema for the report
  (`schemas/verification_report.schema.json`) constrains every
  forbidden-token counter to `const: 0`.

In production the four input JSONs come from real adapters
(TradingView MCP server, Kiwoom OpenAPI REST, KRX / KIND / DART feeds).
Real input files **stay outside the repo**.
