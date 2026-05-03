# Breakout-First-Pullback Playbook v3.3

**Doctrine:** `rulebook/TRADER_HANDBOOK_PRICE_ACTION_DOCTRINE_v3_3.md`
**Patch:** `rulebook/PBKR_MASTER_PATCH_PRICE_ACTION_FIRST_v3_3.md`
**Process:** `runbooks/SNIPE_PRICE_ACTION_DAILY_PROCESS_v3_3.md`

> `direct_trade_signal = false` · `trade_signal = null` ·
> `human_gate_required = true`
>
> The sole core trade of this OS. Read this every session before
> walking the candidate list.

---

## 0. The thesis in one paragraph

After a valid breakout, gapper, or HV-edge event, **smart money has
shown its hand**. The asymmetric edge is not the breakout candle — it
is the **first orderly pullback** into structure that the breakout
created. Buy the chart that *retests* the new strength against a
clearly-defined invalidation. That is the trade. Everything else is
either a derivative of this idea, or it isn't this OS's trade.

## 1. Preconditions (gates 1-4, all required)

### Gate 1 — Market cycle
- Index is in an uptrend, *or* in a healthy stage-1/3 transition with
  participation broadening, *or* an early-stage rebound with quality
  leadership re-asserting.
- In confirmed downtrend, this play is **size-down** or **stand-aside**.

### Gate 2 — Institutional character
- Volume profile shifting toward accumulation
  (advances on higher volume, declines on lower volume).
- No distribution candles into resistance during the prior week.
- Sector and peer leadership intact.

### Gate 3 — Setup integrity
- One of: HVE, HV1, HVIPO, gapper, launch pad, base breakout has
  been **confirmed** (closing basis), within a recent window
  (typically last 1–10 sessions).
- Pivot is declared and has held on a closing basis since the breakout.

### Gate 4 — Pullback character
- Pullback is **orderly**: lower-volume bars, narrow ranges, no high
  volume reversal candles into key support.
- Pullback retraces into a **structural anchor**: pivot, EMA20,
  EMA50, prior consolidation, or the breakout-day's low.

If any of Gate 1–4 fail, **the trade is not on**. The name may still
be `PB_SCOUT`; it is **not** `PB_READY`.

## 2. Entry tactics (choose one, declare it)

| code | name | trigger | stop |
|---|---|---|---|
| **KSR** | Key Support Reclaim | reclaim of lost key support on volume | below the reclaim low |
| **CPB** | Consolidation Pivot Breakout | close above pivot with volume | below pivot or last consolidation low |
| **KMA** | Key Moving Average Pullback | reversal off EMA20 / EMA50 (occasionally EMA150 early-stage) | below MA test low |
| **HVCP** | High Volume Close Pivot | next-day reclaim of HV-close-day high | below HV-close-day low |
| **IBE** | Intraday Base Entry | intraday-pivot reclaim with volume | below intraday base low |

**Exactly one** entry tactic must be selected and recorded in the
plan. Hybrid entries are not authorized.

## 3. Plan template (every candidate)

```yaml
ticker: SYN_XXX                  # tickers SYN_NNN are synthetic only
asof_date: YYYY-MM-DD
doctrine_version: "v3.3"
direct_trade_signal: false
trade_signal: null
human_gate_required: true

setup:
  code: HVE | HV1 | HVIPO | GAPPER | LAUNCH_PAD | BASE_BREAKOUT
  pivot: <price>
  recent_event: <yyyy-mm-dd>     # the breakout / gap / HV day

narrative:                        # secondary; may be empty
  op_revision_pct: null|number
  eps_revision_pct: null|number
  latest_op_surprise_pct: null|number
  wisereport_note: null|string
  news_note: null|string
  telegram_corroboration: null|boolean

indicator:
  rs_60d_percentile: <0..100>
  ema20: <price>
  ema50: <price>
  ema150: <price>
  pivot_intact: true|false
  institutional_character: "accumulation" | "neutral" | "distribution"

plan:
  entry_tactic: KSR | CPB | KMA | HVCP | IBE
  trigger_description: <one sentence>
  stop_price: <price>
  stop_distance_pct: <0..>
  invalidation_condition: <one sentence>
  review_milestones:
    - "first 3-day tight after entry"
    - "test of EMA20"

risk:
  official_risk_hard_exclude: false
  stop_distance_pct_within_doctrine: true|false
  total_portfolio_risk_ok: true|false   # set by the operator

human_gate:
  completed: false
  reviewer: null
  notes: null
```

A candidate without all of the above at `PB_READY` is downgraded to
`PB_SCOUT`.

## 4. Hard-veto cases

- `official_risk_hard_exclude == true` → veto, regardless of structure.
- Pivot lost on a closing basis after breakout → veto until a fresh
  setup forms.
- Distribution day at resistance during pullback → veto until
  character resets.
- Stop distance > doctrine bound (default `> 5%`) and structure cannot
  be tightened → either size-down materially or veto.

## 5. The five entry tactics, in detail

### 5.1 Key Support Reclaim (KSR)
**When:** after a flush into demand that violates a clearly-marked
support, then closes back above it on rising volume.
**Why:** the flush traps weak hands; the reclaim is the chart's
verdict that demand is in control.
**Entry:** the close above the reclaimed level, ideally in the upper
third of the bar's range, with volume above the 20-day average.
**Stop:** below the reclaim bar's low, or below the deepest wick of
the flush (whichever is structurally cleaner).

### 5.2 Consolidation Pivot Breakout (CPB)
**When:** after multi-week tight consolidation with a clean pivot.
**Why:** sponsorship is patient — tight ranges on declining volume
mean weak hands have already exited.
**Entry:** close above pivot with volume materially above the
consolidation average.
**Stop:** below the pivot, or below the last consolidation low.

### 5.3 Key Moving Average Pullback (KMA)
**When:** an established uptrend pulls back to its primary trend MA
(EMA20 / EMA50; occasionally EMA150 in early-stage names) with
character intact.
**Why:** the trend MA is where institutional buyers reload.
**Entry:** the reversal bar off the MA — ideally a tight-range bar
that closes near the high.
**Stop:** below the MA test low.

### 5.4 High Volume Close Pivot (HVCP)
**When:** intraday range with a close at or near the high on volume
materially above 20-day average.
**Why:** late-session strength on volume is sponsorship printing its
intent.
**Entry:** the next session's high-of-day reclaim.
**Stop:** below the HV-close-day's low.

### 5.5 Intraday Base Entry (IBE)
**When:** intraday consolidation forming inside a constructive daily
structure (e.g., flat range above a daily pivot or above a key MA).
**Why:** intraday tightening above structure is high-timeframe
strength condensed.
**Entry:** the intraday-pivot reclaim with volume confirmation.
**Stop:** below the intraday base low.

## 6. After the trigger

- Mark `PB_TRIGGER`. **This is still not an order.**
- Operator executes manually, out-of-band.
- The plan's `review_milestones` are the only sanctioned check-in
  points before invalidation.
- A milestone failure that breaks structure escalates to a written
  re-review. Do not extend stops to "give it room"; tighten or exit.

## 7. Audit invariants

```yaml
playbook_invariants:
  direct_trade_signal: false
  trade_signal: null
  human_gate_required: true
  setup.code in {HVE, HV1, HVIPO, GAPPER, LAUNCH_PAD, BASE_BREAKOUT}
  plan.entry_tactic in {KSR, CPB, KMA, HVCP, IBE}
  plan.stop_price is set
  plan.stop_distance_pct is set
  plan.invalidation_condition is set
  risk.official_risk_hard_exclude == false
forbidden:
  - direct_trade_signal=true
  - trade_signal truthy
  - "지금 매수" / "사라" / "팔라" / "강력매수"
  - PRE_BREAKOUT_WATCH treated as buy
  - latest / SuperPack / rolling --apply
  - committed real PDFs / outputs / parquet / xlsx
  - Drive write / rename / delete
  - API keys / tokens / passwords / secrets
  - parser / bridge / merge / build / emit / ticker_map edits
```
