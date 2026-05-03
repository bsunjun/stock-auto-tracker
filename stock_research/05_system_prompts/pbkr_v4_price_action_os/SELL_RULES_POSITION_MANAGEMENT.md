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
| Structural exit | Tape structure breaks (failed higher low, distribution print, MA breakdown) | Full or partial reduction depending on stage |
| Trim — into strength | Extension condition met while structure intact | Partial reduction only |
| Trim — into weakness | Defensive partial when structure deteriorates but stop not yet hit | Partial reduction only |
| Time stop | Position has not progressed within a defined window | Partial or full, per stage |

There is no "thesis-based hold" exception that overrides the risk stop.
The risk stop is always honored.

---

## 3. Risk Stop

- Defined at entry per `ENTRY_TACTICS_SPEC.md` §5 (`stop_logic`).
- Evaluated on a closing basis unless the breach is by an explicitly
  defined intraday margin (a "hard" stop), to avoid being stopped out
  by transient prints during opening or closing auctions.
- Once breached, the affected tranche is reduced in full. There is no
  averaging, no "give it one more session," no thesis-based override.
- A re-entry after a stop-out requires a new doctrinal tactic
  (`ENTRY_TACTICS_SPEC.md`), not a return to the prior trigger.

---

## 4. Structural Exit

A structural exit is invoked when the tape evidence that justified the
entry is invalidated even though the risk stop has not yet been hit.

### 4.1 Trigger Conditions

- A failed higher-low: the most recent swing low is undercut on volume.
- A distribution print: range expansion to the downside on volume well
  above the trailing reference, particularly from extended levels.
- **Two closes below the moving-average reference** used for the trade
  class:
  - Swing trades: two closes below the **21EMA**.
  - Position trades: two closes below the **50SMA / 10주선**
    (10-week line).
- A breakdown of the entry tactic's `failure_level`.
- A sector/group breakdown that contradicts the name's structural
  premise.
- **Key reversal bar criteria**: a session that opens at or near a new
  high, reverses through the prior session's low, closes in the lower
  portion of its own range, on volume above the trailing reference.

### 4.2 Symmetric Treatment of Adds

Adds are treated as new entries: they require their own setup,
tactic, `trigger_level`, `failure_level`, and `stop_logic`, and they
are constrained by Total Open Risk headroom. An add never lowers the
average price of an existing position as a goal in itself. v4 does
not condone "averaging down" as a reflex.

### 4.3 Add-Back After Failure

A position that was structurally exited may be re-entered only when:

1. A new low-risk setup forms (per `ENTRY_TACTICS_SPEC.md` §4).
2. A new entry tactic with fresh `trigger_level`, `failure_level`,
   and `stop_logic` is documented.
3. Total Open Risk headroom permits the resulting size.

Add-back is not "averaging back into a loser"; it is a fresh trade
on the same name.

---

## 5. Trim Conditions

Trims are partial reductions taken while the stop has not been hit.
v4 distinguishes two trim modes.

### 5.1 Trim Into Strength

Used while the structure remains intact but extension or gain
milestones are met.

- **+5% partial in Stage 1 / Stage 2.** A defined partial reduction
  (commonly half or a smaller fraction) once the position is up
  approximately 5% from cost, applied especially to swing-class
  trades during MCS-KR Stage 1 or early Stage 2.
- **Average gain / R-multiple partial.** Once the position has
  achieved a defined R-multiple (e.g., 1R, 2R, 3R) above cost, a
  partial reduction is taken that mechanically rebalances position
  weight back toward the model weight.
- **Base extension partial.** When price is approximately 20–25%
  extended from the most recent base, a partial reduction is
  considered, particularly for swing-class trades.
- **Climax-style session trim.** A session showing range expansion,
  volume expansion, *and* a close below the session midpoint is a
  partial-reduction signal even when the stop is not threatened.

### 5.2 Trim Into Weakness

Used when structure is deteriorating but the stop has not been hit.

- A close that violates the trade-class moving-average reference
  (21EMA for swing, 50SMA/10주선 for position) once but not twice —
  a partial reduction can pre-empt a structural exit at the second
  close.
- A failed test of the most recent higher low without a clean
  reclaim by close.
- An adverse group/sector signal that has not yet resolved into a
  full structural exit at the name level.

Trims are partial; a trim that reduces the position to zero is
re-classified as a structural exit and logged accordingly.

---

## 6. Breakeven Stop and Stop Migration

- After a doctrinal trim into strength, the stop on the remainder is
  raised to **breakeven** ("to-cost" migration).
- After a confirmed higher-low post-entry, the stop may be raised to
  beneath that higher-low minus the volatility buffer.
- Stops are never lowered. Widening a stop to "give the position
  room" is non-doctrinal.
- A position whose stop has not migrated to at least breakeven is
  ineligible for an Add-on Entry (`ENTRY_TACTICS_SPEC.md` §5.9).

---

## 7. Time Stop

A time stop addresses positions that fail to progress.

- Default window: a stage-dependent number of sessions during which
  the position must establish a higher high or a higher low above
  its entry trigger.
- If the window elapses without progress, the position is reduced —
  partially in higher-conviction stages, fully in defensive stages.
- The intent is to free risk-budget headroom, not to predict
  direction.

---

## 8. True Market Leader vs. Performance Enhancer

Not every winning name is a leader. v4 distinguishes:

| Type | Definition | Management posture |
|---|---|---|
| True market leader | Top trade-class name with multi-quarter growth, leading group, persistent RS, and clean structural advances | Allow the trend to extend; trim sparingly; widest extension tolerance; full `conviction_cap` |
| Performance enhancer | Tradable mover that contributes to the book but lacks one or more leader requirements | Trim more aggressively into strength; tighter extension tolerance; reduced `conviction_cap` |
| Short-term trade | Tactical position without growth qualifications | Tightest exits; smallest `conviction_cap`; first to be reduced when TOR pressure rises |

Mis-classifying a performance enhancer as a leader is a primary
source of P&L variance. The journal records the classification at
entry and reviews it weekly.

---

## 9. Position Management by Market Stage

| MCS-KR Stage | Default exit posture |
|---|---|
| Stage 1 (basing) | Tighter trims into strength, faster structural exits, swing bias dominates |
| Stage 2 (advance) | Wider trims, allow trends to extend, leader names sized fullest |
| Stage 3 (topping) | Aggressive trims into strength; trims into weakness on first MA violation; no new adds |
| Stage 4 (decline) | Risk stops only; structural exits dominate; cash is the prescribed posture |

Defaults can be tightened by the operator; they cannot be loosened
beyond the doctrinal envelope.

---

## 10. Logging Requirement

Every exit produces a journal entry with: category (risk stop /
structural / trim-into-strength / trim-into-weakness / time stop),
trigger evidence, stage at exit, residual position, residual stop,
P&L attribution, classification (leader / enhancer / short-term),
and a one-line lesson. Exits without a journal record are
non-doctrinal.

---

## 11. What This Document Is Not

- Not a real-time exit alerter.
- Not a list of names.
- Not a recommendation regarding any specific security or asset class.
- Not a signal source; nothing here should set any `trade_signal`
  field truthy in any system.
