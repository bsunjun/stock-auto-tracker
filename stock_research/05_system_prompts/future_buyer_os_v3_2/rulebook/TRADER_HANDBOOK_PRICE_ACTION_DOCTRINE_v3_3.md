# Trader Handbook — Price-Action Doctrine v3.3

**Status:** ACTIVE — top-of-stack operating doctrine for the
**PBKR Future Buyer Momentum OS v3.2** (rev v3.3 doctrine layer).

This document supersedes the implicit "estimates-first" reading of the
v3.2 thesis. It is **additive**: no v3.2 file is deleted by this patch.
Where v3.2 prompts assume estimates-first ordering, this doctrine wins.

> **Hard rule (whole document):**
> `direct_trade_signal = false`,
> `trade_signal = null`,
> `human_gate_required = true`.
>
> Nothing in this doctrine constitutes a buy or sell instruction.
> Nothing here authorizes auto-execution. PB\_READY / PB\_SCOUT /
> PB\_TRIGGER are **review states**, not orders.

---

## 0. One-paragraph mandate

Price action leads. Estimates and reports follow. The job of the
operator is to recognize **constructive structure under institutional
sponsorship** — breakouts, gappers, launch pads, base completions — and
to enter on the **first low-risk pullback** with a clearly defined
invalidation. Every other input is an *edge booster*, not a primary
signal.

---

## 1. The five doctrines

### Doctrine 1 — Price action is primary

The chart is the verdict. Price, volume, relative strength, and the
geometry of the setup are the **primary signal**. If price action does
not confirm, no estimate revision, no broker upgrade, no Telegram tip,
and no news headline elevates a name above `PB_SCOUT`.

> `primary_signal = { price_action, volume, relative_strength, setup_quality }`
> `trade_signal = null`

### Doctrine 2 — Estimates / reports / news are secondary edge boosters

`op_revision_pct`, `eps_revision_pct`, `latest_op_surprise_pct`,
WiseReport summaries, broker estimates, news-grounder output, and
Telegram channel chatter are **secondary inputs**. They:

- *can* confirm a setup that already passes the price-action gate,
- *cannot* on their own elevate a name to `PB_READY` or higher,
- *cannot* override an invalidation on the chart.

> An earnings beat into a broken chart is **not** a setup. It is a
> liquidity event for someone else.

### Doctrine 3 — Estimate / earnings upgrade is **NOT** a required candidate filter

A name without a positive estimate revision can still be a `PB_READY`
candidate, **provided** it shows a valid breakout / gapper / HV edge
followed by a constructive pullback. The earlier v3.2 narrative that
implied "no estimate upgrade → no candidacy" is **rescinded** by this
patch.

### Doctrine 4 — Market cycle first; institutional character second

Before any name is reviewed:

1. **Market cycle** — is the broad index in an uptrend, in a stage-1/3
   transition, or in a bear leg? Read the index character before
   anything else.
2. **Institutional character change** — is *smart money* (functional
   institutional flow) accumulating or distributing? Watch for:
   - shifts in close-of-day volume profile,
   - tightening base on declining volume,
   - markup on rising volume,
   - the absence of distribution candles at logical resistance.

These two reads gate the entire candidate review. A failing market
cycle reduces position size *and* tightens stops.

### Doctrine 5 — The core strategy is **breakout → first low-risk pullback**

The asymmetric edge of this OS is not "buy the breakout candle." It is:

1. Identify a valid breakout / gapper / HV edge.
2. Wait for the first orderly pullback.
3. Enter against a structural invalidation (key support / key MA /
   pivot reclaim).

Buying the breakout candle is not forbidden, but it is **not** the
PBKR core trade. The first-pullback entry is what this OS is tuned
for.

---

## 2. Setup taxonomy (HVE / HV1 / HVIPO / gappers / launch pads / base breakouts)

| code | name | description |
|---|---|---|
| **HVE** | High-Volume Edge | Initiating volume thrust off a base or pivot, marking institutional interest. |
| **HV1** | Highest-Volume-1 day | Day-1 thrust with the largest volume in the prior N sessions; treated as an *event*, not an entry. |
| **HVIPO** | High-Volume IPO setup | Recent IPO carving a first base on rising volume. |
| **Gapper** | Gap-up edge | Constructive gap that holds; entries taken on the *first* orderly pullback into structure. |
| **Launch Pad** | Tight, low-volatility consolidation under resistance, ready to break. |
| **Base Breakout** | Cup / handle / flat-base / VCP-style breakout from a defined pivot. |

**Each setup must declare a pivot.** No pivot, no setup. The pivot is
what makes invalidation objective.

---

## 3. Five entry tactics (the only entries this OS recognizes)

All five are **price-action confirmations**. They produce the
`PB_TRIGGER` review state when the structural and risk gates pass.

### 3.1 Key Support Reclaim
Price loses key support, then **reclaims it back above** with stronger
than average volume on the reclaim bar. Stop = below the reclaim low.
Best after a flush into demand, not after a slow grind.

### 3.2 Consolidation Pivot Breakout
Tight, multi-week consolidation with a clean pivot. Entry on a
break-of-pivot bar that **closes** above pivot with above-average
volume. Stop = below the pivot or below the last consolidation low.

### 3.3 Key Moving Average Pullback
Pullback to a primary trend MA (commonly EMA20, EMA50, occasionally
EMA150 in early-stage names) **with character intact** (lower
volume on the pullback, supportive lower-timeframe action). Entry on
the reversal bar off MA. Stop = below the MA test low.

### 3.4 High Volume Close Pivot
Tight intraday range that **closes at or near the high** of the
session on volume materially above 20-day average. Entry on the
following session's high-of-day reclaim. Stop = below the HV close
day's low.

### 3.5 Intraday Base Entry
Intraday consolidation forming inside the daily structure (e.g., flat
range above a daily pivot). Entry on the intraday-pivot reclaim with
volume confirmation. Stop = below the intraday base low.

> Any "entry" outside these five is **not** a sanctioned entry tactic
> for this OS. It is a research observation.

---

## 4. Review-state ladder (v3.3 redefinition)

| state | definition (v3.3) |
|---|---|
| `PRE_BREAKOUT_WATCH` | A name is structurally interesting but has **no** entry. Watchlist only. **Not a buy signal.** |
| `PB_SCOUT` | Price action is showing *one of*: key support reclaim, key MA pullback, or pivot reclaim — under acceptable market and institutional character. **Reconnaissance state**, not a position. |
| `PB_READY` | Valid breakout / gapper / HV edge has occurred and a constructive pullback is in progress. Estimates / earnings upgrade are **NOT required**. Risk gates (stop distance, official risk) must already pass. |
| `PB_TRIGGER` | One of the five entry tactics has confirmed *and* the human gate has been completed. **Even here**, no auto-execution: this remains a *review-completed* state, not an order. |

### 4.1 What PB\_READY no longer requires (v3.3 patch)

- ❌ positive `op_revision_pct` is **not** required
- ❌ positive `eps_revision_pct` is **not** required
- ❌ broker target raise is **not** required
- ❌ WiseReport positive coverage is **not** required
- ❌ Telegram corroboration is **not** required

What PB\_READY *does* require:

- ✅ valid breakout / gapper / HV edge in the recent window
- ✅ constructive pullback in progress (volume contraction, structure
  intact)
- ✅ market-cycle gate passed
- ✅ institutional-character gate passed
- ✅ `official_risk_hard_exclude == false`
- ✅ `stop_distance_pct` within doctrine bounds
- ✅ `stop_price` declared
- ✅ `invalidation_condition` declared

### 4.2 PRE\_BREAKOUT\_WATCH is **NOT** a buy signal

This is repeated for emphasis. PRE\_BREAKOUT\_WATCH means "structure
is forming." It does not mean "enter now." Treating
PRE\_BREAKOUT\_WATCH as a buy is a doctrine violation.

## 5. Hard veto: official risk flags

A name with `official_risk_hard_exclude == true` is **vetoed**. No
combination of price-action excellence, estimate upgrades, or
catalysts overrides this.

The hard-exclude tag set (mirrors PBKR Quant Feature Screener v1):

- `managed_stock` (관리종목)
- `trading_halt` (거래정지)
- `audit_opinion_disclaimer` (감사의견 거절)
- `audit_opinion_adverse` (감사의견 부적정)
- `delisting_candidate` (상장폐지 후보)

## 6. Risk skeleton (position sizing — research scope, principles fixed)

> Detailed sizing math is intentionally deferred to a follow-up
> research item. The **principles** below are binding now.

- Every reviewed candidate **must** declare:
  - `stop_distance_pct` — distance from `close` to `stop_price` in %.
  - `stop_price` — the absolute level that invalidates the thesis.
  - `invalidation_condition` — a one-sentence structural description
    of what would invalidate the setup (e.g., "close below EMA50",
    "loss of pivot on volume").
- Risk is bounded **at the portfolio level** by
  `total_portfolio_risk` — the sum of (position notional × stop
  distance) across open names must remain inside a doctrine-defined
  budget. The exact budget % is a research item; the constraint is
  not.
- A name with `stop_distance_pct` outside doctrine bounds (default
  `> 5%`) is downgraded — it does not vanish, but it cannot reach
  `PB_TRIGGER` until structure tightens or sizing is reduced.

> No part of this section authorizes execution. Sizing converts a
> reviewed setup into a *plan*; execution is human and out-of-band.

## 7. S.N.I.P.E. mapping

The S.N.I.P.E. five-letter discipline is the operational form of the
above doctrines. See `runbooks/SNIPE_PRICE_ACTION_DAILY_PROCESS_v3_3.md`
for the daily process; the mapping is:

| letter | meaning | doctrine link |
|---|---|---|
| **S** — Setup | which of the six setups (HVE/HV1/HVIPO/gapper/launch pad/base breakout) | §2 |
| **N** — Narrative | secondary edge: estimates / report / news / Telegram (non-mandatory) | §1 D2/D3 |
| **I** — Indicator | price/volume/RS confirmation | §1 D1, §3 |
| **P** — Plan | entry, stop, invalidation, target review milestones | §6 |
| **E** — Execution | human gate, sizing, out-of-band order entry | §6 (no auto) |

## 8. What is forbidden in any document or pack derived from this doctrine

- `direct_trade_signal = true` → **forbidden**
- truthy `trade_signal` → **forbidden**
- "지금 매수", "사라", "팔라", "강력매수" or any directive trade
  language outside of explicit prohibition documentation → **forbidden**
- emitting `PRE_BREAKOUT_WATCH` as a buy → **forbidden**
- promoting any output to `latest`, `SuperPack`, or `rolling --apply`
  paths → **forbidden**
- writing real market data, real PDFs, output JSON/CSV, parquet, or
  xlsx into the repository → **forbidden**
- storing API keys / tokens / passwords / secrets → **forbidden**
- Drive write / rename / delete from this layer → **forbidden**
- modifying parser / bridge / merge / build / emit / ticker_map
  engines from this doctrine → **forbidden**

Any document or generated pack that violates the above must be
rejected at the human gate.

## 9. Relationship to v3.2 artifacts

- v3.2 prompts and schemas remain in place.
- This doctrine is referenced from:
  - `rulebook/PBKR_MASTER_PATCH_PRICE_ACTION_FIRST_v3_3.md`
  - `runbooks/SNIPE_PRICE_ACTION_DAILY_PROCESS_v3_3.md`
  - `runbooks/BREAKOUT_FIRST_PULLBACK_PLAYBOOK_v3_3.md`
  - `project_prompts_patch/PRICE_ACTION_FIRST_PROJECT_PATCH_v3_3.md`
- Where v3.2 prompts read estimates-first, this doctrine **wins**.
- Where v3.2 prompts already read price-action-first, this doctrine
  is a clarifying amplification.
- The MASTER\_TRADING\_PRINCIPLES concept (wherever instantiated) is
  *superseded* by this v3.3 doctrine, **not deleted**.
