# PBKR Quant Feature Screener v1

Skeleton for the **PBKR Future Buyer Momentum OS v3.2** quantitative
candidate-compression layer.

> **Scope:** This module is *additive-only*. It produces feature tables,
> screened candidate packs, and filter-IC backtest packs. It does **not**
> emit trade signals. It is a **research / candidate-compression layer**,
> not an order generator.

---

## 1. Position in the OS v3.2 pipeline

```
raw market / weekly / estimate / flow / risk inputs
            │
            ▼
   build_*_features.py  ──►  per-domain feature shards
            │
            ▼
   build_feature_table.py  ──►  feature_table.parquet/csv
            │
            ▼
   screen_candidates.py    ──►  screened_candidate_pack.json
            │
            ▼
   backtest_filter_ic.py   ──►  filter_performance_pack.json
```

The screener runs **before** the human-judgment / playbook layer.
Outputs of this module are inputs to the human review loop, not to
execution.

## 2. Hard non-goals

This PR (and v1 of the screener) **must not**:

- emit `direct_trade_signal=true`
- emit any truthy `trade_signal` field
- represent `PB_READY` / `PB_TRIGGER` as a buy/sell instruction
- recommend "지금 매수", "사라", "팔라", "강력매수" or any directive trade
  language outside of explicit prohibition documentation
- commit real market data, real PDFs, real CSV/JSON outputs, parquet,
  xlsx, or any artifact derived from a real broker feed
- store API keys, tokens, passwords, or secrets
- perform any Drive write / rename / delete
- promote any output to `latest`, `SuperPack`, or `rolling --apply` paths

These are enforced by the forbidden-audit rules in
`scripts/screen_candidates.py` and `scripts/backtest_filter_ic.py`.

## 3. Feature taxonomy

Features are grouped into five domains; one builder per domain.

### 3.1 Price (`build_price_features.py`)

| key | description |
|---|---|
| `close` | latest close (synthetic in fixtures) |
| `ema20`, `ema50`, `ema150` | exponential moving averages |
| `close_vs_ema20_pct` | `(close / ema20 - 1) * 100` |
| `close_vs_ema50_pct` | `(close / ema50 - 1) * 100` |
| `rs_20d`, `rs_60d`, `rs_120d`, `rs_252d` | relative-strength vs. benchmark |
| `sector_rs_20d`, `sector_rs_60d` | RS vs. sector index |
| `ibdrs_approx` | percentile rank of blended RS (0–99) |
| `stop_distance_pct` | distance from `close` to nearest support stop |

### 3.2 Weekly (`build_weekly_features.py`)

| key | description |
|---|---|
| `weekly_return_13w` | 13-week return |
| `weekly_ma10`, `weekly_ma30` | 10w / 30w moving averages |
| `weekly_ma10_slope` | slope of weekly MA10 |

### 3.3 Estimate (`build_estimate_features.py`)

| key | description |
|---|---|
| `latest_sales`, `latest_op`, `latest_eps` | latest quarter actuals |
| `op_revision_pct` | analyst OP revision (% over window) |
| `eps_revision_pct` | analyst EPS revision (% over window) |
| `latest_op_surprise_pct` | actual vs. consensus OP surprise (%) |
| `sales_guidance_delta` | management sales guidance delta |
| `op_guidance_delta` | management OP guidance delta |

### 3.4 Flow (`build_flow_features.py`)

| key | description |
|---|---|
| `institution_flow_score` | 0–100 score of institutional accumulation |
| `financial_investment_consecutive_days` | consecutive days of net buying by 금융투자 |
| `private_fund_flow_strength` | normalized private-fund flow strength |

### 3.5 Risk (`build_risk_features.py`)

| key | description |
|---|---|
| `official_risk_hard_exclude` | bool — KRX 관리종목 / 거래정지 / 감사의견 거절 / 상장폐지 후보 |

A `true` value here forces a hard exclude regardless of any other score.

## 4. Filter v1 (illustrative)

The default screen, encoded in `config/feature_screen_v1.yaml`:

```yaml
hard_excludes:
  - official_risk_hard_exclude == false
soft_filters:
  - ibdrs_approx >= 80
  - rs_60d_percentile >= 80
  - op_revision_pct > 0 OR latest_op_surprise_pct >= 15
  - institution_flow_score >= 70 OR financial_investment_consecutive_days >= 3
  - stop_distance_pct <= 5
```

`screen_candidates.py` computes a per-row `pass_count` and a
`screen_score` (sum of soft-filter scores), but **does not** label any
row as `BUY` / `SELL` / `direct_trade_signal`.

## 5. Outputs

### 5.1 `feature_table`

Wide table; one row per `(ticker, asof_date)`. Schema:
`schemas/feature_table.schema.json`.

### 5.2 `screened_candidate_pack`

JSON pack with:
- `asof_date`
- `universe_size`
- `hard_exclude_count`
- `candidates[]` — list of survivors with `pass_count`, `screen_score`,
  feature snapshot, and reason strings.

Schema: `schemas/screened_candidate_pack.schema.json`.

### 5.3 `filter_performance_pack`

JSON pack of forward-IC and hit-rate diagnostics per soft filter:
- `filter_id`
- `ic_5d`, `ic_20d`, `ic_60d`
- `hit_rate_pos_fwd_20d`
- `n_obs`

Schema: `schemas/filter_performance_pack.schema.json`.

These are **diagnostic** statistics on filter quality, not trade
recommendations.

## 6. Synthetic fixture

`examples/run_feature_screener_fixture.py` runs the full pipeline on
`examples/synthetic_feature_table.csv` and validates the screened
candidate / filter performance packs against their JSON schemas.

The fixture must produce:
- `direct_trade_signal=true` count == 0
- truthy `trade_signal` count == 0
- real-data artifact count == 0

## 7. Boundaries vs. Future Buyer OS v3.2

| layer | role | this PR |
|---|---|---|
| Screener (this module) | candidate compression, IC diagnostics | ✅ added |
| Future Buyer OS v3.2 prompts / schemas | structured human-judgment layer | unchanged |
| Execution / order layer | order generation | not touched |

No file under `stock_research/05_system_prompts/future_buyer_os_v3_2/`
is modified by this PR. No parser / bridge / merge / build / emit /
ticker_map module is modified.
