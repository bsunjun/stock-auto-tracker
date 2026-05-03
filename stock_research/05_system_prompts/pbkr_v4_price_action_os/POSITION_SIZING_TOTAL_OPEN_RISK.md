# PBKR v4 — Position Sizing and Total Open Risk

> Educational doctrine. Not advice. Not a signal source.

---

## 1. The Risk-First Inversion

In v3, conviction sized positions; the stop was set after sizing. v4
inverts this: **the stop sets the position, and the portfolio risk
budget caps the book**. Growth, conviction, and setup quality enter
sizing only as caps, never as multipliers (see
`PBKR_V4_GROWTH_POLICY.md` §5).

---

## 2. The Sizing Pipeline

Position size is the **minimum** across all applicable caps. No cap
can ever increase size; each only restricts it.

```
position_size = min(
    risk_budget_shares      ,   # from R / stop_distance
    notional_cap_shares     ,   # from notional_cap * equity / entry_trigger
    liquidity_cap_shares    ,   # from liquidity floor
    sector_cap_shares       ,   # from per-sector exposure ceiling
    stage_cap_shares        ,   # from MCS-KR stage * base position cap
    conviction_cap_shares   ,   # from trade-class assignment (PBKR_V4_GROWTH_POLICY §4)
    setup_quality_cap_shares    # from setup cleanliness and growth context
)
```

Equivalently, expressed as percentages of equity:

```
position_size_pct = min(
    R / stop_distance_pct ,
    notional_cap_pct      ,
    liquidity_cap_pct     ,
    sector_cap_pct        ,
    stage_cap_pct         ,
    conviction_cap_pct    ,
    setup_quality_cap_pct
)
```

---

## 3. Per-Position Risk Budget (R)

`R = equity * r_per_position`

Where `r_per_position` is a doctrinal fraction (calibrated in the
operating notebook).

Risk-budget shares:

`risk_budget_shares = floor( R / (entry_trigger - stop_level) )`

A wide stop produces a small position; a tight stop produces a
larger position; the loss-on-stop is the same in both cases.

---

## 4. Stage Cap and Base Position Size

The MCS-KR stage sets the base position cap.

| MCS-KR Stage | Base position cap (% of equity) |
|---|---|
| Stage 1 (basing) | **10%** |
| Stage 2 (advance) | **10%** initial; up to **20% maximum**, only after positive feedback |
| Stage 3 (topping) | 5% (no new adds) |
| Stage 4 (decline) | Minimal (cash is the prescribed posture) |

**"Up to 20% in Stage 2 unless proven otherwise"** is a ceiling, not
a target. Initial positions are sized at the 10% base; increases
toward 20% are permitted *only* after the position has produced
positive feedback (a doctrinal trim into strength, a higher-low
formation, a stop migration to breakeven). Sizing up too large too
soon is non-doctrinal.

---

## 5. Conviction Cap and Setup-Quality Cap

These caps reflect the trade class and setup quality, derived from
upstream documents:

- `conviction_cap` is set by the trade class
  (`PBKR_V4_GROWTH_POLICY.md` §4):
  - Short-term trade: lowest cap.
  - Swing trade: standard cap.
  - Position trade: full cap.
  - Leader-grade position trade: maximum cap (still bounded by the
    stage cap).
- `setup_quality_cap` is set by setup cleanliness:
  - Tight, prolonged base with clean pivot: highest cap.
  - Wide, choppy base or marginal pivot: reduced cap.
  - Group context contradicts: cap reduced further.

Neither cap sets size on its own. Both feed into the `min(...)`
above.

---

## 6. Total Open Risk (TOR)

TOR is the sum of `R_i` across all currently open positions:

`TOR = sum_i ( position_size_i * stop_distance_i )`

`TOR_pct` (as a fraction of equity) is the headroom-management
quantity:

`TOR_pct = TOR / equity`

As stops migrate (see `SELL_RULES_POSITION_MANAGEMENT.md` §6),
`R_i` shrinks and TOR shrinks; new entries are permitted into the
freed headroom.

A new entry is doctrinally permitted only if:

`TOR_pct + R_new_pct <= K * TOR_ceiling_pct`

Otherwise the candidate is parked.

---

## 7. Stage Multiplier (K) on TOR

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

## 8. Size-Up Rule — "Only After Positive Feedback"

A position may be sized up (via Add-on Entry,
`ENTRY_TACTICS_SPEC.md` §5.9) only when **all** of the following
hold:

1. The existing position's stop has migrated to at least breakeven.
2. The position has produced a doctrinal trim into strength, **or**
   a confirmed higher-low post-entry.
3. A fresh setup with its own `trigger_level`, `failure_level`, and
   `stop_logic` is documented.
4. Total Open Risk headroom permits the resulting size.
5. The combined position size after the add does not breach the
   stage cap (10% initial, 20% maximum in Stage 2).

"Too large too soon" is the explicit failure mode this rule
prevents.

---

## 9. Correlation Throttle

Two positions in highly correlated names (same sector, same theme,
same supplier-customer chain) consume **shared** risk headroom: each
name is sized by its own trigger/stop, but a correlation factor `c`
(a fraction between 0 and 1) is applied so that:

`R_i_effective = R_i + c * sum(R_j) for related j`

The portfolio cannot be circumvented by spreading the same bet
across five tickers.

---

## 10. Heat Map Discipline

Operator maintains a current heat map of:

- TOR vs. ceiling (TOR_pct vs. K * TOR_ceiling_pct).
- Per-stage K vs. effective K.
- Per-sector R concentration vs. sector cap.
- Per-name notional concentration vs. notional cap.
- Per-trade-class concentration (leader vs. enhancer vs.
  short-term).

If any cell breaches its doctrinal limit, no new entries are
permitted until the breach is resolved by exits, by stop migration
that reduces `R_i`, or by equity growth.

---

## 11. Cash as a Position

Cash is a doctrinal position. Increasing cash in Stage 3 and Stage 4
is not "doing nothing"; it is the *prescribed* posture. Pressure to
deploy cash for its own sake is non-doctrinal.

---

## 12. Drawdown Governor

A trailing drawdown governor reduces `R` and `K` together when
realized drawdown exceeds defined thresholds:

- Mild drawdown: scale `R` and `K` by 0.75.
- Moderate drawdown: scale by 0.50.
- Severe drawdown: scale by 0.25 and pause new entries until a
  structural reset (defined in the journal protocol).

Restoration to full sizing is *not* automatic on drawdown recovery;
it requires a defined number of process-clean sessions documented
in the journal.

---

## 13. What This Document Is Not

- Not a portfolio-management product.
- Not a recommendation regarding any specific security.
- Not a system that emits orders. No field in any external system
  should be set truthy on the basis of these formulas; they are
  educational specifications of human discipline.
