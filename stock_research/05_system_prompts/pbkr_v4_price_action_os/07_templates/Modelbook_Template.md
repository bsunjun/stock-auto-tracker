# Modelbook Entry Template

> Educational. Not advice. Not a signal source.
> One entry per closed trade. Validates against
> `05_schemas/PBKR_V4_modelbook_schema.json`. The modelbook is the
> operator's pattern memory: what worked, what didn't, and whether the
> pattern behaved as the doctrine predicted.

---

## Header

- **schema_version:** `v4.1`
- **modelbook_id:** `mb-YYYYMMDD-<short>`
- **entry_session_date:** `YYYY-MM-DD`
- **exit_session_date:** `YYYY-MM-DD`
- **name:** `<anonymized identifier>`

---

## Classification

- **trade_class:** `short_term` | `swing` | `position` |
  `leader_grade_position`
- **edge:** the cited edges at entry (one or more of `HVE`, `HVIPO`,
  `HV1`, `RelativeStrength`, `NFactor`, `GroupMove`,
  `GrowthAcceleration`).
- **setup:** the cited setup at entry (one of `LaunchPad`, `Gapper`,
  `BaseBreakout`, `BreakoutFirstPullback`, `ContinuationFlag`,
  `ReversalOfTrend`).
- **entry_tactic_id:** the tactic invoked (one of the nine in
  `ENTRY_TACTICS_SPEC.md` §5).

---

## Outcome

- **exit_category:** `risk_stop` | `structural` | `trim_into_strength`
  | `trim_into_weakness` | `time_stop`
- **outcome_class:** `winner_leader` | `winner_enhancer` |
  `winner_short_term` | `loser_stop` | `loser_structural` | `loser_time`
- **r_multiple_realized:** `<numeric, multiple of initial R>`
- **holding_sessions:** `<integer>`

---

## Lesson (one line; ≤ 280 chars)

`<the durable insight, written so a future self reading this in six
months still recognizes the situation>`

Examples of good lessons:

- "Failed reclaims twice on same name → pattern reliability degraded;
  do not re-enter on same pivot."
- "+5% partial in Stage 2 strong was premature for a leader-grade
  position trade; let trend extend longer next time."
- "Group breakdown preceded name breakdown by one session; structural
  exit on group signal would have saved the time-stop loss."

Bad lessons (do not write):

- "Should have bought sooner." (Hindsight, not pattern.)
- "Bad luck." (Not a lesson.)
- "Will do better next time." (Not specific.)

---

## Pattern Memory Note (specific; ≤ 600 chars)

Did the pattern behave as the doctrine predicted? Be concrete:

- Did the trigger / failure / stop levels actually capture the
  structure?
- Did the confirmation requirements
  (`ENTRY_TACTICS_SPEC.md` §7) align with what the tape showed?
- Did the trade-class assignment match the holding period actually
  realized?
- Was the size cap appropriate to the actual volatility?

If the pattern did not behave as predicted, the pattern memory note
becomes input to a future doctrine-review PR — never an inline
edit to the doctrine.

---

## Linked Postmortem (if applicable)

- **linked_postmortem_id:** `pm-YYYYMMDD-<short>` (only when
  `outcome_class` ∈ `loser_*` or when a process deviation occurred).

---

## Disclaimers (mandatory)

```yaml
direct_trade_signal: false
trade_signal: null
human_gate_required: true
```
