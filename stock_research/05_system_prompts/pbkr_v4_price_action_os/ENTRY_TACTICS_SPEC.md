# PBKR v4 — Entry Tactics Specification

> Educational doctrine. Not advice. Not a signal source. Descriptions of
> human decision rules; nothing in this document is intended to be
> consumed as an automated order or as a `direct_trade_signal`-style flag,
> nor to set any `trade_signal` field truthy.

---

## 1. Three Layers: Edges, Setups, Entry Tactics

v4 deliberately separates three concepts that v3 conflated:

- **Edges** — durable sources of advantage that make a name a
  candidate at all (not yet a setup, not yet an entry).
- **Setups** — recognizable structural patterns that *might* produce
  an entry within a defined window.
- **Entry Tactics** — the precise, executable rules that define the
  `trigger_level`, `failure_level`, and `stop_logic` at which a
  position is opened.

Entries require: at least one edge, a recognized setup, and an entry
tactic with all required fields specified before transaction.

---

## 2. Preconditions

Before any entry tactic is evaluated, all of the following must hold:

1. The market cycle stage is one in which entries are doctrinally
   permitted (see `MARKET_CYCLE_SYSTEM_KR.md`).
2. The name is on the active watchlist (see
   `SCREENING_WATCHLIST_SYSTEM.md`).
3. Trade class is assigned per `PBKR_V4_GROWTH_POLICY.md` §4.
4. Liquidity floor is satisfied at the candidate entry size.
5. Total Open Risk has headroom for the new position (see
   `POSITION_SIZING_TOTAL_OPEN_RISK.md`).

If any precondition fails, the candidate is parked.

---

## 3. Edges

The recognized edges in v4. A name needs at least one to be considered.

| Edge | Description |
|---|---|
| HVE — High-Volume Episode | A discrete, recent session of unusually high volume that signals fresh institutional interest. |
| HVIPO — High-Volume IPO | The post-IPO high-volume base/episode characteristic of a fresh listing. |
| HV1 — First High-Volume Move | The first high-volume episode after a long quiet period, often the start of a new trend. |
| Relative Strength | Measurable outperformance versus index and sector over a meaningful trailing window. |
| N-factor / new catalyst | A new product, contract, regulation, customer, or structural change with first-order operating impact. |
| Group move | The issuer's industry group is itself in a constructive structural move. |
| Growth acceleration | Multi-quarter acceleration in growth evidence per `PBKR_V4_GROWTH_POLICY.md` §3. |

Edges are *necessary but not sufficient*. Edges alone do not authorize
an entry.

---

## 4. Setups

Recognized setups, each of which may host one or more entry tactics.

| Setup | Definition |
|---|---|
| Launch Pad | Tight, prolonged sideways consolidation following a high-volume episode; the "coiled spring" base. |
| Gapper | A session that gaps materially up on a catalyst, opening a new structural reference. |
| Base Breakout | Resolution of a multi-week base through its prior high. |
| Breakout → First Pullback | The first orderly retracement after an initial breakout, returning to a defined support reference. |
| Continuation Flag | A short, tight sideways drift after a sharp prior advance. |
| Reversal-of-Trend (restricted) | Exhaustion of a downtrend with higher-low formation; restricted to specific MCS-KR stages. |

A name is on a setup if its tape *currently presents* the setup's
structure. The setup itself does not generate an entry.

---

## 5. Entry Tactics

Each tactic specifies the exact rules that produce an entry. All nine
tactics share a common schema:

- `definition` — the structural condition that defines the tactic.
- `trigger_level` — the precise price reference whose interaction with
  the tape opens the entry consideration.
- `failure_level` — the price reference whose breach invalidates the
  tactic before the stop-out, requiring exit even at small loss.
- `stop_logic` — the rule that places the protective stop relative to
  the tactic's structure.
- `Korean_market_caveat` — KR-specific handling (auctions, daily
  limit, designations, lunch sag, etc.).

### 5.1 Key Support Level Reclaim

- **definition** — Price has lost a key prior support, then reclaims
  that support on a session that closes back above it on volume.
- **trigger_level** — The reclaimed support level itself, on a closing
  basis above the level.
- **failure_level** — A subsequent close back below the reclaimed
  level invalidates the reclaim.
- **stop_logic** — Stop placed beneath the swing low formed during
  the loss-and-reclaim, with a volatility buffer.
- **Korean_market_caveat** — Reclaims printed only inside the opening
  auction window (`09:00`–`09:15`) or during sidecar/circuit-breaker
  conditions are not valid; require continuous-session confirmation.

### 5.2 Consolidation Pivot Breakout

- **definition** — A multi-session tight consolidation forms; price
  resolves through the consolidation's pivot on range-and-volume
  expansion.
- **trigger_level** — The consolidation's defined pivot (its prior
  high), with a small acceptance buffer.
- **failure_level** — Re-entry of price back into the consolidation
  after the pivot was taken, on the same or next session.
- **stop_logic** — Stop beneath the consolidation low, with a
  volatility buffer.
- **Korean_market_caveat** — Pivot breakouts coinciding with
  KOSPI200/KOSDAQ150 rebalance windows must be down-weighted; flow is
  mechanical, not structural.

### 5.3 Key Moving Average Pullback

- **definition** — In an established uptrend, price retraces in
  contraction (lower range, lower volume) to a key moving-average
  reference (commonly the 21EMA for swing or 50SMA for position
  trades).
- **trigger_level** — A reversal session at the MA: a print whose
  range and volume re-expand, closing in the upper portion of the
  session.
- **failure_level** — A close materially below the MA after the
  reversal session.
- **stop_logic** — Stop beneath the swing low of the pullback,
  within a volatility buffer of the MA.
- **Korean_market_caveat** — During AGM-season disclosure clusters
  (Mar/Apr, Aug/Nov), require an explicit event-risk note in the
  journal before entry.

### 5.4 Key Support Level Pullback

- **definition** — Price pulls back to a horizontal prior-support /
  prior-breakout level (not necessarily an MA), then reverses.
- **trigger_level** — A reversal session at the support level with
  range and volume re-expansion.
- **failure_level** — A close materially below the support level.
- **stop_logic** — Stop beneath the support level minus volatility
  buffer.
- **Korean_market_caveat** — Avoid this tactic in names whose recent
  range has been distorted by a daily-limit print until the next clean
  two-sided session.

### 5.5 Oops Reversal

- **definition** — A session opens beneath the prior session's low
  (gap down), then reverses intraday and closes back inside (or above)
  the prior session's range.
- **trigger_level** — A reclaim of the prior session's low intraday,
  confirmed by closing strength.
- **failure_level** — A subsequent close that fails to hold the prior
  session's low.
- **stop_logic** — Stop beneath the reversal session's intraday low.
- **Korean_market_caveat** — Opening-auction prints can produce a
  pseudo-Oops; require the reversal to develop after `09:15`, not
  inside the auction window.

### 5.6 Opening Range Breakout (ORB)

- **definition** — Define an opening range over a fixed early window
  (e.g., the first 15 or 30 minutes after `09:15`); enter on a
  breakout of the range high on volume.
- **trigger_level** — The opening range high, on a sustained intraday
  print.
- **failure_level** — Re-entry into the opening range on the same
  session.
- **stop_logic** — Stop at the opening range low, or a defined
  fraction of the opening range below the trigger.
- **Korean_market_caveat** — Use the post-`09:15` window to define
  the opening range to exclude auction-induced distortions; do not
  evaluate ORB during sidecar conditions.

### 5.7 Intraday Base Entry

- **definition** — After a strong prior session or strong morning,
  price forms a tight intraday consolidation; entry on the
  consolidation breakout.
- **trigger_level** — The intraday consolidation high.
- **failure_level** — Re-entry below the intraday consolidation low.
- **stop_logic** — Stop beneath the intraday consolidation low.
- **Korean_market_caveat** — The 11:30–13:30 period is a known
  false-signal window; intraday-base entries during this block require
  an explicit "near-yes from morning" precondition (see
  `SNIPE_DAILY_PROCESS.md` §6).

### 5.8 High Volume Close Pivot

- **definition** — A session closes through a defined pivot with
  range expansion *and* volume materially above the trailing
  reference, in the upper portion of the session.
- **trigger_level** — The closing print above the pivot, on the
  closing basis.
- **failure_level** — A subsequent session that closes back below
  the pivot.
- **stop_logic** — Stop beneath the pivot minus volatility buffer.
- **Korean_market_caveat** — A high-volume close concentrated inside
  the closing-auction window (`15:20`–`15:30`) is index-flow, not
  structural; require pre-auction strength to qualify.

### 5.9 Add-on Entry

- **definition** — A subsequent doctrinal entry on a name in which
  the operator already holds a position, made when the name presents
  a fresh setup *and* the existing position's stop has migrated to
  at least breakeven.
- **trigger_level** — The trigger level of the new setup (any of
  the tactics above).
- **failure_level** — The failure level of the new setup; does not
  override the existing position's stop.
- **stop_logic** — Stop on the *added tranche* per the new setup's
  rule; stop on the original tranche is left intact or migrated
  upward only, never widened.
- **Korean_market_caveat** — Adds during sidecar / circuit-breaker
  conditions are non-doctrinal regardless of setup quality.

---

## 6. Pre-Pivot Engagement — Refined Rule

Indiscriminate pre-pivot averaging is forbidden. However, several of
the entry tactics above (Key Support Level Reclaim, Consolidation
Pivot Breakout's preparatory zone, Key MA Pullback, Key Support Level
Pullback, Oops Reversal) are **explicitly permitted** before a
traditional base-breakout pivot, *provided* that:

- The tactic's `trigger_level` is precisely defined before any
  transaction.
- The tactic's `failure_level` is precisely defined before any
  transaction.
- The stop is pre-defined per the tactic's `stop_logic`.

Without all three fields specified in advance, no pre-pivot entry is
doctrinal.

---

## 7. Confirmation Requirements

Across tactics, the four standing confirmation requirements remain:

1. **Range expansion** versus the trailing reference at the trigger.
2. **Volume confirmation** versus the trailing reference at the
   trigger.
3. **Closing strength** in the upper portion of the session range
   (or, for intraday tactics, sustained hold above the trigger
   through the relevant re-test window).
4. **No contradicting macro / KR-session-structure print** (see
   `PBKR_V4_KOREAN_MARKET_ADAPTATION.md`).

Two-of-four is a *watch*, not an entry.

---

## 8. Initial Position Construction

- Doctrinal initial entry is a single tranche at confirmation.
- Optional second tranche is an Add-on Entry (§5.9), governed by its
  own setup, trigger, failure, and stop.
- Tranching is not a substitute for waiting for confirmation.

---

## 9. Disqualifiers at the Trigger

Even with a clean tactic, an entry is disqualified if:

- The trigger print occurs in the first 5 minutes of session opening,
  inside an unsettled price-discovery window.
- The trigger print occurs in the closing auction window.
- The session is under a circuit-breaker / sidecar condition.
- Spread at the trigger is materially wider than the name's median.
- Range-expansion is driven by a single non-recurring exchange
  disclosure with unclear implication.

---

## 10. Logging Requirement

Every doctrinal entry produces a journal entry with: edge cited, setup
label, tactic label, `trigger_level`, `failure_level`, `stop_logic`
applied, range/volume confirmation evidence, market cycle stage,
trade class, Total Open Risk before/after, and the explicit thesis
sentence. Entries without a journal record are non-doctrinal.

---

## 11. What This Document Is Not

- Not a list of names.
- Not a real-time alerter.
- Not a signal feed; it does not emit `trade_signal` of any kind, and
  no field in any system should be set truthy on the basis of these
  patterns alone.
