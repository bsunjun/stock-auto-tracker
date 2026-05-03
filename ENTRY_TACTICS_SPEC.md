# PBKR v4 — Entry Tactics Specification

> Educational doctrine. Not advice. Not a signal source. Descriptions of
> human decision rules; nothing in this document is intended to be
> consumed as an automated order or as a `direct_trade_signal`-style flag.

---

## 1. Preconditions

Before any entry tactic is evaluated, all of the following must hold:

1. The market cycle stage is one in which entries are doctrinally
   permitted (see `MARKET_CYCLE_SYSTEM_KR.md`).
2. The name is on the active watchlist (see
   `SCREENING_WATCHLIST_SYSTEM.md`).
3. The growth gate is cleared (see `PBKR_V4_GROWTH_POLICY.md`).
4. Liquidity floor is satisfied at the candidate entry size.
5. Total Open Risk has headroom for the new position (see
   `POSITION_SIZING_TOTAL_OPEN_RISK.md`).

If any precondition fails, the candidate is parked. No "creative"
entry can override a failed precondition.

---

## 2. The Four Canonical Patterns

v4 recognizes four canonical entry patterns. Patterns outside this set
are doctrinally not entries; they may be observations, but not
positions.

### 2.1 Base Breakout (BB)

- Prior consolidation of meaningful duration (multi-week base).
- Tight closes near base highs in the days preceding the breakout.
- Range expansion through the pivot on volume meaningfully above the
  base-period average.
- Group context not contradicting (group not breaking down).

### 2.2 Pullback to Trend (PT)

- Established uptrend with a defined rising structure.
- Orderly retracement to a primary moving-average reference, or to a
  prior breakout level acting as support.
- Tape character on the pullback is contraction, not expansion
  (decreasing range, decreasing volume into the test).
- Reversal print on the test session shows range expansion and
  volume re-engagement.

### 2.3 Continuation Flag (CF)

- Sharp prior advance.
- Sideways-to-down low-volume drift forming a tight flag.
- Resolution through the flag boundary on volume above the flag-period
  average.
- Used only when underlying base structure is constructive.

### 2.4 Reversal-of-Trend (RT) — Restricted

- Prior downtrend showing exhaustion (failed lower lows, capitulation
  volume, then quiet stabilization).
- A distinct higher-low structure forms.
- A confirmation print breaks the most recent lower high on volume.
- RT entries are restricted to MCS-KR Stage 2 transitions or earlier
  Stage 3 confirmations and require explicit doctrinal logging.

---

## 3. Pivot Definition

Each pattern defines a **pivot**:

- BB: the prior base high, with a small acceptance buffer.
- PT: the reversal session high after the trend test.
- CF: the upper flag boundary.
- RT: the most recent lower-high level whose break confirms the structure.

The pivot is the *only* doctrinal entry reference. Anticipation of a
pivot, or chasing a print materially extended above a pivot, is
non-doctrinal.

---

## 4. Confirmation Requirements

An entry is only doctrinal if all of the following are present at the
pivot:

1. **Range expansion** versus the trailing reference.
2. **Volume confirmation** versus the trailing reference.
3. **Closing strength** in the upper portion of the session range
   (or, intraday, a sustained hold above the pivot through a defined
   re-test window).
4. **No contradicting macro print** (see Korean-market doc on session
   structure and circuit conditions).

Two-of-four is a *watch*, not an entry.

---

## 5. Stop Placement

Stops are pre-defined at the pivot calculation, not after the entry.

- BB: below the breakout base structure, beyond a defined volatility
  buffer.
- PT: below the swing low of the pullback test.
- CF: below the flag's lower boundary, beyond a volatility buffer.
- RT: below the higher-low that defined the structure.

The stop is the **risk anchor**; it feeds directly into sizing. A
position whose stop has not been pre-defined is non-doctrinal.

---

## 6. Initial Position Construction

- Doctrinal initial entry is a single tranche at confirmation. No
  pre-pivot accumulation. No "starter" positions before pattern
  confirmation.
- Optional second tranche, doctrinally permitted only on a structural
  add condition (see `SELL_RULES_POSITION_MANAGEMENT.md` §4 — symmetric
  treatment of adds).
- Tranching is not a substitute for waiting for confirmation.

---

## 7. Disqualifiers at the Pivot

Even with a clean pattern, an entry is disqualified if:

- The pivot print occurs in the first 5 minutes of session opening,
  inside an unsettled price-discovery window.
- The pivot print occurs in the closing auction window.
- The session is under a circuit-breaker / sidecar condition.
- Spread at the pivot is materially wider than the name's median.
- Range-expansion is driven by a single non-recurring exchange
  disclosure with unclear implication.

---

## 8. Logging Requirement

Every doctrinal entry produces a journal entry with: pattern label,
pivot value, stop value, range/volume confirmation evidence, market
cycle stage, growth-gate snapshot, Total Open Risk before/after, and
the explicit thesis sentence. Entries without a journal record are
non-doctrinal.

---

## 9. What This Document Is Not

- Not a list of names.
- Not a real-time alerter.
- Not a signal feed; it does not emit `trade_signal` of any kind, and
  no field in any system should be set truthy on the basis of these
  patterns alone.
