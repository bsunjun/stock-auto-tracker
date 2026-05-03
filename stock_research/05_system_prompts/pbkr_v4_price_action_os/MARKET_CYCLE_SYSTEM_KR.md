# PBKR v4 — Market Cycle System (KR)

> Educational doctrine. Not advice. Not a signal source.

---

## 1. Purpose

The Market Cycle System for Korea (MCS-KR) classifies the prevailing
regime of the Korean equity market and modulates **every** downstream
tactic (entries, exits, sizing, screening priority).

The classification is intentionally coarse. v4 prefers a robust
four-state model over a fragile fine-grained one.

---

## 2. Cycle ON/OFF — An Exposure Dial, Not a Confirmed Signal

The MCS-KR cycle ON/OFF reading is **not** a confirmed buy/sell
signal. It is an **exposure dial** — a continuous adjustment to how
much risk the operator is willing to keep on the book, not a binary
authorization to transact.

- *Cycle ON* dials risk envelope upward (toward `K = 1.0`).
- *Cycle OFF* dials risk envelope downward (toward `K = 0.10`).
- Neither setting authorizes any specific entry; entries still
  require a setup, a tactic, and the confirmation requirements in
  `ENTRY_TACTICS_SPEC.md`.

---

## 3. The Four Stages

| Stage | Tape character | Default posture |
|---|---|---|
| Stage 1 — Basing | Index in extended sideways range after a decline | Selective, small initial sizes, swing bias |
| Stage 2 — Advance | Index in a defined uptrend, broadening participation | Standard sizing, full TOR envelope |
| Stage 3 — Topping | Index losing breadth, leadership rotates defensively | Trim posture, no new adds, reduced K |
| Stage 4 — Decline | Index in a defined downtrend, breadth deteriorating | Risk-stop primacy, minimal TOR |

Stage transitions are not symmetric. A Stage 2 → Stage 3 transition
requires breadth deterioration *and* structural break of the index
trend reference. A Stage 3 → Stage 2 reversion requires the inverse,
plus a confirmation interval (no immediate flip-flopping).

---

## 4. Inputs

MCS-KR is a *conjunction* across the following inputs. No single
input determines the stage.

1. **KOSPI trend.** Regime against the **21EMA / 50SMA / 200SMA**
   moving-average reference set, daily-close basis. Slope direction
   matters as much as the level.
2. **KOSDAQ trend.** Same MA reference set, evaluated independently
   from KOSPI.
3. **Breadth.** Percentage of constituents above their primary
   moving-average reference; advance/decline net; new highs / new
   lows.
4. **Leading group action.** Whether new highs come from cyclical /
   growth groups or from defensive groups; whether the leading
   groups themselves are extending or contracting.
5. **Foreign-investor net flow.** A multi-session smoothed proxy.
6. **FX context.** KRW/USD trend direction relative to its own
   primary moving-average reference.
7. **Volatility regime.** A KOSPI200-derived implied-volatility
   regime label (low / normal / elevated / stress).
8. **Stress test.** A scripted check applied at regime-transition
   candidates: would the proposed posture still be acceptable if
   the most adverse plausible move occurred this week?
9. **Leader action.** Behavior of the operator's *named* leader
   universe — when leaders break, the regime is degrading even if
   the index has not yet confirmed.
10. **Recent 10 trades feedback.** The operator's own most recent
    closed trades — hit rate, average gain, average loss, and
    whether trims-into-strength have been profitable. Persistent
    underperformance in recent trades dials the posture down even
    when the index confirms otherwise.

---

## 5. Stage Definitions in Detail

### 5.1 Stage 1 — Basing

- Index has held above a defined trough zone for a meaningful
  duration after a Stage 4 decline.
- Breadth has stabilized; new lows have receded.
- 21EMA flattening or beginning to turn up; 50SMA still flat or
  declining gently.
- Leadership has not yet broadened, but selected groups show
  early-stage structure.
- Volatility regime is normalizing from elevated toward normal.

### 5.2 Stage 2 — Advance

- Index above 21EMA / 50SMA, with both rising; 200SMA also rising
  or about to.
- Breadth above a defined floor and trending up.
- Leadership in cyclicals / growth, not in defensives.
- Foreign net flow non-negative on the smoothed reference.
- Volatility regime in normal or low band.
- Recent-10-trades feedback constructive.

### 5.3 Stage 3 — Topping

- Index still above 21EMA, but 21EMA slope flattening; 50SMA slope
  weakening.
- Breadth diverging negatively from price (price up, breadth flat
  or down).
- Leadership rotating to defensives; named leaders breaking
  individually.
- Foreign net flow turning negative.
- Volatility regime drifting toward elevated.
- Recent-10-trades feedback deteriorating.

### 5.4 Stage 4 — Decline

- Index below 21EMA / 50SMA; 50SMA itself falling; 200SMA at risk
  of rolling over.
- Breadth below a defined floor.
- Leadership entirely defensive or absent.
- Foreign net flow persistently negative.
- Volatility regime elevated or stress.
- Recent-10-trades feedback adverse.

---

## 6. Weak / Normal / Strong Market — Risk Dial

Within Stage 2, the market itself is graded weak / normal / strong,
which adjusts the risk envelope:

| Sub-grade | Effective dial | Sizing posture |
|---|---|---|
| Strong (Stage 2, broad leadership, healthy breadth) | Full `K`, Stage 2 caps available | Up to 20% per name allowed after positive feedback |
| Normal (Stage 2, mixed leadership) | Full `K`, base 10% caps | Standard |
| Weak (Stage 2 with deteriorating breadth) | Reduced `K`, base 10% caps held tight | Trim into strength earlier |

In Stage 1, sub-grades default to "weak" until breadth and leader
action confirm broadening. In Stage 3 / Stage 4, the sub-grade is
moot — the dial is set by the stage.

---

## 7. Transitions and Hysteresis

- **Worsening transitions** (Stage 2 → 3, 3 → 4): require fewer
  confirmation sessions. Doctrine errs on the side of de-risking.
- **Improving transitions** (4 → 1, 1 → 2, 3 → 2 reversion): require
  more confirmation sessions. Doctrine errs on the side of
  patience.

Asymmetry is intentional: false positives on improvement are far
more expensive than false positives on worsening.

---

## 8. Stage-Conditional Tactics

The MCS-KR stage and sub-grade are read at the start of each
session and explicitly referenced in:

- `ENTRY_TACTICS_SPEC.md` — tactic eligibility (RT restricted to
  early stages; ORB de-prioritized in Stage 4; etc.).
- `SELL_RULES_POSITION_MANAGEMENT.md` — exit posture by stage.
- `POSITION_SIZING_TOTAL_OPEN_RISK.md` — stage cap and stage
  multiplier `K`.
- `SCREENING_WATCHLIST_SYSTEM.md` — screening priorities by stage.

There is **no** doctrinal context in which the stage is ignored.

---

## 9. Disagreement Between KOSPI and KOSDAQ

When KOSPI and KOSDAQ stages disagree:

- The watchlist is partitioned by listing venue, and each partition
  uses its own stage.
- Total Open Risk is a *single* portfolio quantity and uses the
  more conservative of the two stages for the K multiplier.

---

## 10. Logging Requirement

Each session opens with a journal entry recording: KOSPI stage,
KOSDAQ stage, sub-grade (weak/normal/strong), the inputs that drove
any transition, the recent-10-trades feedback summary, and the
implications for K and screening priority.

---

## 11. What This Document Is Not

- Not a market forecast.
- Not a recommendation regarding any specific security or asset
  class.
- Not a confirmed signal; the stage label is an exposure dial for
  human decisioning, not an automated execution flag.
