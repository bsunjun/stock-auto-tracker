# PBKR v4 — Position Sizing and Total Open Risk

> Educational doctrine. Not advice. Not a signal source.

---

## 1. The Risk-First Inversion

In v3, conviction sized positions; the stop was set after sizing. v4
inverts this: **the stop sets the position, and the portfolio risk
budget caps the book**.

Three variables are defined first, in order:

1. **R** — per-position risk budget (a fraction of equity).
2. **TOR** — Total Open Risk ceiling (a fraction of equity, summing
   per-position R across all open positions).
3. **K** — stage multiplier on TOR (see §5).

Position size is then a derived quantity, not an input.

---

## 2. Per-Position Risk Budget

`R = equity * r_per_position`

Where `r_per_position` is a doctrinal fraction (calibrated in the
operating notebook; conventionally a small single-digit basis-point
range relative to equity).

Position size in shares is then:

`shares = floor( R / (entry_pivot - stop_level) )`

This formulation makes the risk per position invariant across names
of different volatility profiles. A wide stop produces a small
position; a tight stop produces a larger position; the loss-on-stop is
the same in both cases.

---

## 3. Notional Cap

A separate cap limits notional exposure to any single name to a
maximum fraction of equity, even when the volatility-derived sizing
would permit more. This protects against a single-name gap event.

`shares = min( shares_from_R , floor( notional_cap * equity / entry_pivot ) )`

---

## 4. Total Open Risk (TOR)

TOR is the sum of `R_i` across all currently open positions, where
`R_i` is the *current* distance from market to stop, multiplied by
position size. As stops migrate (see
`SELL_RULES_POSITION_MANAGEMENT.md` §7), `R_i` shrinks and TOR
shrinks; new entries are permitted into the freed headroom.

Doctrinal TOR ceiling: a fraction of equity, calibrated per stage.

A new entry is doctrinally permitted only if:

`TOR + R_new <= K * TOR_ceiling`

Otherwise the candidate is parked.

---

## 5. Stage Multiplier (K)

`K` modulates TOR by market cycle stage:

| MCS-KR Stage | Default K |
|---|---|
| Stage 1 (basing) | 0.50 |
| Stage 2 (advance) | 1.00 |
| Stage 3 (topping) | 0.50 |
| Stage 4 (decline) | 0.10 |

Defaults may be tightened by the operator; they cannot be loosened
without an explicit doctrinal exception logged in the journal.

The intent is structural: the portfolio's exposure to risk is itself
a function of regime, not of individual-name conviction.

---

## 6. Correlation Throttle

Two positions in highly correlated names (same sector, same theme,
same supplier-customer chain) consume **shared** risk headroom: each
name is sized by its own pivot/stop, but a correlation factor `c` (a
fraction between 0 and 1) is applied so that:

`R_i_effective = R_i + c * sum(R_j) for related j`

The portfolio cannot be circumvented by spreading the same bet across
five tickers.

---

## 7. Heat Map Discipline

Operator maintains a current heat map of:

- TOR vs. ceiling.
- Per-stage K vs. effective K.
- Per-sector R concentration.
- Single-name notional concentration.

If any cell breaches its doctrinal limit, no new entries are permitted
until the breach is resolved by exits, by stop migration that reduces
`R_i`, or by equity growth.

---

## 8. Cash as a Position

Cash is a doctrinal position. Increasing cash in Stage 3 and Stage 4
is not "doing nothing"; it is the *prescribed* posture. Pressure to
deploy cash for its own sake is non-doctrinal.

---

## 9. Drawdown Governor

A trailing drawdown governor reduces `R` and `K` together when
realized drawdown exceeds defined thresholds:

- Mild drawdown: scale `R` and `K` by 0.75.
- Moderate drawdown: scale by 0.50.
- Severe drawdown: scale by 0.25 and pause new entries until a
  structural reset (defined in the journal protocol).

Restoration to full sizing is *not* automatic on drawdown recovery;
it requires a defined number of process-clean sessions documented in
the journal.

---

## 10. What This Document Is Not

- Not a portfolio-management product.
- Not a recommendation regarding any specific security.
- Not a system that emits orders. No field in any external system
  should be set truthy on the basis of these formulas; they are
  educational specifications of human discipline.
