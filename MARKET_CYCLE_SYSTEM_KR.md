# PBKR v4 — Market Cycle System (KR)

> Educational doctrine. Not advice. Not a signal source.

---

## 1. Purpose

The Market Cycle System for Korea (MCS-KR) classifies the prevailing
regime of the Korean equity market into one of four stages, and
modulates *every* downstream tactic (entries, exits, sizing, screening
priority) accordingly.

The classification is intentionally coarse. v4 prefers a robust
four-state model over a fragile fine-grained one.

---

## 2. The Four Stages

| Stage | Tape character | Default posture |
|---|---|---|
| Stage 1 — Basing | Index in extended sideways range after a decline | Selective, small initial sizes |
| Stage 2 — Advance | Index in a defined uptrend, broadening participation | Standard sizing, full TOR envelope |
| Stage 3 — Topping | Index losing breadth, leadership rotates defensively | Trim posture, no new adds, reduced K |
| Stage 4 — Decline | Index in a defined downtrend, breadth deteriorating | Risk-stop primacy, minimal TOR |

Stage transitions are not symmetric. A Stage 2 → Stage 3 transition
requires breadth deterioration *and* structural break of the index
trend reference. A Stage 3 → Stage 2 reversion requires the inverse,
plus a confirmation interval (no immediate flip-flopping).

---

## 3. Inputs

MCS-KR consumes the following inputs (descriptions only; values are
not embedded in this doctrine):

1. **Index trend reference.** A primary moving-average reference for
   KOSPI and a secondary reference for KOSDAQ, observed on a daily
   close basis.
2. **Breadth.** Percentage of constituents above their primary
   moving-average reference; advance/decline net.
3. **Leadership composition.** Whether new highs come from cyclical /
   growth groups or from defensive groups.
4. **Foreign-investor net flow.** A multi-session smoothed proxy.
5. **FX context.** KRW/USD trend direction relative to its own
   primary moving-average reference.
6. **Volatility regime.** A KOSPI200-derived implied-volatility
   regime label (low / normal / elevated / stress).

No single input determines the stage. The stage is a **conjunction**
across inputs, not a vote.

---

## 4. Stage Definitions in Detail

### 4.1 Stage 1 — Basing

- Index has held above a defined trough zone for a meaningful
  duration after a Stage 4 decline.
- Breadth has stabilized; new lows have receded.
- Leadership has not yet broadened, but selected groups show
  early-stage structure.
- Volatility regime is normalizing from elevated toward normal.

### 4.2 Stage 2 — Advance

- Index above its primary MA reference, MA reference itself rising.
- Breadth above a defined floor and trending up.
- Leadership in cyclicals/growth, not in defensives.
- Foreign net flow non-negative on the smoothed reference.
- Volatility regime in normal or low band.

### 4.3 Stage 3 — Topping

- Index still above its MA reference, but MA slope flattening.
- Breadth diverging negatively from price (price up, breadth flat or
  down).
- Leadership rotating to defensives.
- Foreign net flow turning negative.
- Volatility regime drifting toward elevated.

### 4.4 Stage 4 — Decline

- Index below its MA reference; MA reference itself falling.
- Breadth below a defined floor.
- Leadership entirely defensive or absent.
- Foreign net flow persistently negative.
- Volatility regime elevated or stress.

---

## 5. Transitions and Hysteresis

Transitions require persistence to prevent regime whiplash:

- **Worsening transitions** (1→2 reverse, 2→3, 3→4): require fewer
  confirmation sessions. Doctrine errs on the side of de-risking.
- **Improving transitions** (4→1, 1→2, 3→2 reversion): require more
  confirmation sessions. Doctrine errs on the side of patience.

Asymmetry is intentional: false positives on improvement are far
more expensive than false positives on worsening.

---

## 6. Stage-Conditional Tactics

The MCS-KR stage is read at the start of each session and explicitly
referenced in:

- `ENTRY_TACTICS_SPEC.md` — pattern eligibility (RT restricted to
  early stages; CF emphasized in Stage 2; etc.).
- `SELL_RULES_POSITION_MANAGEMENT.md` — exit posture by stage.
- `POSITION_SIZING_TOTAL_OPEN_RISK.md` — stage multiplier `K`.
- `SCREENING_WATCHLIST_SYSTEM.md` — screening priorities by stage.

There is **no** doctrinal context in which the stage is ignored.

---

## 7. Disagreement Between KOSPI and KOSDAQ

When KOSPI and KOSDAQ stages disagree:

- The watchlist is partitioned by listing venue, and each partition
  uses its own stage.
- Total Open Risk is a *single* portfolio quantity and uses the
  more conservative of the two stages for the K multiplier.

---

## 8. Logging Requirement

Each session opens with a journal entry recording: KOSPI stage,
KOSDAQ stage, the inputs that drove any transition, and the
implications for K and screening priority.

---

## 9. What This Document Is Not

- Not a market forecast.
- Not a recommendation regarding any specific security or asset
  class.
- Not a signal source; the stage label is an input to human
  decisioning, not an automated execution flag.
