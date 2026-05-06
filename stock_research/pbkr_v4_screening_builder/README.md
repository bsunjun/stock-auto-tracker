# PBKR v4 — Screening Builder

> Educational doctrine support tooling. **Not a trade signal.**
> `screening_only = true`. `direct_trade_signal = false`.
> `automatic_execution_allowed = false`. Human gate is required.

This module implements the **first stage** of PBKR v4: a candidate
generation engine that combines

1. TradingView (MCP / Screener) scan results,
2. Kiwoom REST API daily features (OHLCV, flows, MAs, ATR…),
3. KRX / KIND / DART **official risk-flag taxonomy**, and
4. A locally computed **PBKR_RS_RANK** (0–100 percentile rank),

into a single `DAILY_INPUT_PACKET` that the GPT Orchestrator consumes.

This stage **does not** produce `PB_READY`, `PB_SCOUT`, `PB_TRIGGER`, or
trade tickets. It produces *candidates that may, on a given session,
satisfy `ENTRY_TACTICS_SPEC.md`* (see
`05_system_prompts/pbkr_v4_price_action_os/SCREENING_WATCHLIST_SYSTEM.md`).

---

## 1. Layout

```
pbkr_v4_screening_builder/
  builder.py                  # end-to-end orchestrator
  cli.py                      # CLI entry point
  pbkr_rs_rank.py             # 1M/3M/6M/12M weighted percentile
  state_classifier.py         # 7-state classification
  screening_filters.py        # filter rules + label generators
  packet_emitter.py           # DAILY_INPUT_PACKET (.json + .md)
  validator.py                # output safety + schema validation
  adapters/
    tradingview_mcp.py        # TradingView scan normalization
    kiwoom_rest.py            # Kiwoom feature normalization
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

* `screening_only = true` on every output.
* `direct_trade_signal = false`, `trade_signal = false|null`,
  `automatic_execution_allowed = false`, `human_gate_required = true`.
* No `PB_TRIGGER` / `PB_READY` / `PB_SCOUT` is ever emitted by this stage.
* No trade ticket is emitted by this stage.
* Outputs land in a local/private directory; the default is
  `$PBKR_SCREENING_OUT` or `/tmp/pbkr_v4_screening_out/<date>`.
* Repo contains code, schemas, docs, and **synthetic** fixtures only.
  No real OHLCV / no real ticker name / no real designation row /
  no broker response / no API key may be committed.
* `account_no`, `order_no`, `api_key`, `token`, `password`, and
  broker-response fields are rejected by `validator.py`.

## 3. Inputs

### 3.1 TradingView MCP scan
Per row: `ticker`, `name` (anonymized in fixtures), `TARGET_EMA`,
`ema_state`, `price_action_label`, `pullback_label`, optional
`rs_proxy`. RS_PROXY is *optional* — TradingView's free Screener does
not always expose RS_SCORE, so the engine never assumes it.

### 3.2 Kiwoom REST features
Per ticker: daily OHLCV, `trading_value`, `volume_ratio`,
`investor_flow`, `foreigner_flow`, `institution_flow`,
`financial_investment_flow`, `ma9`, `ma21`, `ma50`, `ma120`,
`atr14`, `recent_low`, `stop_distance`.

### 3.3 PBKR_RS_RANK (computed locally)
See `pbkr_rs_rank.py`. 0–100 percentile rank from Kiwoom OHLCV
universe. Default weights:

| Horizon | Weight |
|---|---|
| 1M  | 0.20 |
| 3M  | 0.30 |
| 6M  | 0.30 |
| 12M | 0.20 |

Optional benchmark-relative return is added when a `benchmark_close`
series is supplied. Threshold for the first relative-strength
condition is `pbkr_rs_rank >= 80`. TradingView `rs_proxy` is only
used as a secondary field when present.

### 3.4 Official risk flags
KRX / KIND / DART taxonomy. See `adapters/official_risk.py` for the
mapping between Korean designation strings and the four risk buckets.

## 4. Screening filters

A candidate must satisfy:

* `pbkr_rs_rank >= 80`
* `trading_value >= min_trading_value` (configurable; default 5e9 KRW)
* `price >= ma21` **or** `ma9 >= ma21 >= ma50` (alignment)
* `ma50 >= ma120` (long trend up)
* recent strong trend / breakout / first-pullback evidence
  (price action or pullback label set, and 20–60d high proximity)

Generated labels:

* `volume_state_label`  — `dry`, `normal`, `expansion`, `climax`
* `pullback_state_label` — `none`, `shallow`, `deep`, `broken`
* `stop_distance_label` — `tight`, `normal`, `wide`

## 5. State classification (priority order)

1. `HARD_EXCLUDE`  — administrative / delisting / halt / unfaithful
   disclosure / non-standard audit opinion.
2. `NO_ENTRY_MARKET_STRUCTURE_ACTIVE` — sidecar / circuit breaker /
   limit-up·down compression / opening or closing auction window.
3. `EXTREME_RISK_FLAG_WATCH` — `투자위험` / `투자위험 지정예고`
   (watch only; **no new entry**).
4. `REGULAR_PB_EXCLUDE` — `투자주의` / `투자경고` / `단기과열`
   (regular pullback excluded; high-risk-watch may still apply).
5. `RISK_FLAG_PULLBACK_WATCH` — same designations as above, but the
   tape is constructive enough to *watch* (still **not** a PB_TRIGGER).
6. `WATCH_CANDIDATE` — all clean, all filters pass.
7. `WATCH_ONLY` — most filters pass, RS or trend not yet aligned.

`HARD_EXCLUDE` and `NO_ENTRY_MARKET_STRUCTURE_ACTIVE` short-circuit
all further processing.

## 6. Outputs

Written to `$PBKR_SCREENING_OUT/<YYYY-MM-DD>/`:

* `tradingview_scan_pack.json`
* `kiwoom_feature_pack.json`
* `official_risk_flags_pack.json`
* `screening_candidates_pack.json`
* `daily_input_packet.json`
* `daily_input_packet.md`

`daily_input_packet.md` is the human-readable summary. Both the JSON
and the MD assert `screening_only=true`,
`direct_trade_signal=false`, `automatic_execution_allowed=false`.

## 7. Run (dev / synthetic)

```bash
python -m stock_research.pbkr_v4_screening_builder.cli \
    --tradingview stock_research/pbkr_v4_screening_builder/fixtures/tradingview_scan_synthetic.json \
    --kiwoom-features stock_research/pbkr_v4_screening_builder/fixtures/kiwoom_features_synthetic.json \
    --kiwoom-universe stock_research/pbkr_v4_screening_builder/fixtures/kiwoom_universe_synthetic.json \
    --official-risk stock_research/pbkr_v4_screening_builder/fixtures/official_risk_synthetic.json \
    --asof 2026-05-06 \
    --out-dir /tmp/pbkr_v4_screening_out
```

In production the four input JSONs come from real adapters
(TradingView MCP server, Kiwoom OpenAPI REST, KRX / KIND / DART feeds).
Real input files **stay outside the repo**.
