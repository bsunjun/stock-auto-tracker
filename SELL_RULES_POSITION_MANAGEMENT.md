# PBKR v4 — Exit Rules and Position Management

> Educational doctrine. Not advice. Not a signal source. Descriptions of
> human decision rules; nothing in this document constitutes a
> recommendation regarding any specific security.

---

## 1. Philosophy

Exits are not the inverse of entries; they are a separate discipline.
Entries decide *whether* to take risk. Exits decide *how long* to keep
that risk on the book. Most realized P&L variance comes from exits.

v4 separates exits into four distinct categories. Each category has its
own trigger logic and its own logging requirement.

---

## 2. Categories of Exit

| Category | Trigger | Action shape |
|---|---|---|
| Risk stop | Pre-defined stop level breached | Full reduction of the affected tranche |
| Structural exit | Tape structure breaks (failed higher low, distribution print) | Full or partial reduction depending on stage |
| Trim | Extension condition met while structure intact | Partial reduction only |
| Time stop | Position has not progressed within a defined window | Partial or full, per stage |

There is no "thesis-based hold" exception that overrides the risk stop.
The risk stop is always honored.

---

## 3. Risk Stop

- Defined at entry per `ENTRY_TACTICS_SPEC.md` §5.
- Evaluated on a closing basis unless the breach is by an explicitly
  defined intraday margin (a "hard" stop), to avoid being stopped out
  by transient prints during opening or closing auctions.
- Once breached, the affected tranche is reduced in full. There is no
  averaging, no "give it one more session," no thesis-based override.
- A re-entry after a stop-out requires a new doctrinal pattern
  (`ENTRY_TACTICS_SPEC.md`), not a return to the prior pivot.

---

## 4. Structural Exit

A structural exit is invoked when the tape evidence that justified the
entry is invalidated even though the risk stop has not yet been hit.
Conditions include:

- A failed higher-low: the most recent swing low is undercut on volume.
- A distribution print: range expansion to the downside on volume well
  above the trailing reference, particularly from extended levels.
- A breakdown of the primary moving-average reference used in the entry
  pattern, with confirmation.
- A sector/group breakdown that contradicts the name's structural
  premise.

Structural exits may be partial (reducing exposure while keeping a
remainder above the risk stop) or full (when multiple structural
conditions co-occur).

### 4.1 Symmetric Treatment of Adds

Adds are treated as new entries: they require their own pattern, pivot,
and stop, and they are constrained by Total Open Risk headroom. An add
*never* lowers the average price of an existing position as a goal in
itself. v4 does not condone "averaging down" as a reflex.

---

## 5. Trim Conditions

Trims are partial reductions taken while the structure remains intact.
They are tools for compounding through volatility, not exits.

Doctrinal trim conditions include:

- A stretch print materially above a defined extension reference
  (e.g., a multiple of average true range above the entry pivot).
- A climax-style session showing range expansion *and* volume
  expansion *and* a close below the session midpoint.
- A defined gain milestone whose realization mechanically rebalances
  position weight back toward the model weight.

Trims are partial; a trim that reduces the position to zero is
re-classified as a structural exit and logged accordingly.

---

## 6. Time Stop

A time stop addresses positions that fail to progress.

- Default window: a stage-dependent number of sessions during which the
  position must establish a higher high or a higher low above its
  entry pivot.
- If the window elapses without progress, the position is reduced —
  partially in higher-conviction stages, fully in defensive stages.
- The intent is to free risk-budget headroom, not to predict direction.

---

## 7. Stop Migration

Stops migrate **only** in one direction: toward reduced risk.

- After a confirmed higher-low post-entry, the stop may be raised to
  beneath that higher-low minus the volatility buffer.
- After a doctrinal trim, the stop on the remainder may be raised to
  the entry pivot (a "to-cost" migration), and subsequently above it.
- Stops are never lowered. Widening a stop to "give the position room"
  is non-doctrinal.

---

## 8. Position Management by Market Stage

| MCS-KR Stage | Default exit posture |
|---|---|
| Stage 1 (basing) | Tighter trims, faster structural exits |
| Stage 2 (advance) | Wider trims, allow trends to extend |
| Stage 3 (topping) | Aggressive trims into strength, no new adds |
| Stage 4 (decline) | Risk stops only; structural exits dominate |

Defaults can be tightened by the operator; they cannot be loosened
beyond the doctrinal envelope.

---

## 9. Logging Requirement

Every exit produces a journal entry with: category, trigger evidence,
stage at exit, residual position, residual stop, P&L attribution, and
a one-line lesson. Exits without a journal record are non-doctrinal.

---

## 10. What This Document Is Not

- Not a real-time exit alerter.
- Not a list of names.
- Not a recommendation regarding any specific security or asset class.
- Not a signal source; nothing here should set any `trade_signal`
  field truthy in any system.
