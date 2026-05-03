# Daily Focus Ticket Template

> Educational. Not advice. Not a signal source.
> A name without a fully filled ticket — including setup, entry tactic
> with all five fields, stop plan, size plan, and sell plan — cannot
> enter the daily focus list, regardless of how compelling its thesis
> sounds.

> Validation: this template, when filled, must validate against
> `05_schemas/PBKR_V4_ticket_schema.json`.

---

## Header

- **schema_version:** `v4.1`
- **ticket_id:** `tkt-YYYYMMDD-<short>`
- **session_date:** `YYYY-MM-DD`
- **name:** `<anonymized identifier>`
- **trade_class:** `short_term` | `swing` | `position` | `leader_grade_position`

---

## Edge

- **edge:** one or more of `HVE`, `HVIPO`, `HV1`, `RelativeStrength`,
  `NFactor`, `GroupMove`, `GrowthAcceleration`.

Citation (one sentence per edge):

- `<edge>` — `<the specific evidence supporting this edge>`

---

## Setup

- **setup:** one of `LaunchPad`, `Gapper`, `BaseBreakout`,
  `BreakoutFirstPullback`, `ContinuationFlag`, `ReversalOfTrend`.

Setup notes (1–3 sentences): describe the structural condition the
tape currently presents.

---

## Entry Tactic (all five fields are mandatory)

- **tactic_id:** one of the nine in `ENTRY_TACTICS_SPEC.md` §5.
- **definition:** the structural condition that defines the tactic.
- **trigger_level:** the precise price reference whose interaction with
  the tape opens the entry consideration.
- **failure_level:** the price reference whose breach invalidates the
  tactic before stop-out, requiring exit even at small loss.
- **stop_logic:** the rule that places the protective stop relative
  to the tactic's structure.
- **kr_caveat:** KR-specific handling (auctions, daily limit,
  designations, sidecar, lunch sag, etc.).

---

## Stop Plan

- **initial_stop_rule:** the concrete level + rule (e.g., "below the
  reclaim swing low minus 0.6 × ATR(14), evaluated on close").
- **stop_evaluation_basis:** `closing` | `intraday_hard`.
- **migration_plan:** how the stop will migrate (to breakeven after
  doctrinal trim into strength; never widened).

---

## Size Plan

- **risk_budget_pct:** R as a fraction of equity for this tranche.
- **stop_distance_pct:** distance from trigger to stop, as a fraction.
- **applied_caps:** the caps from
  `POSITION_SIZING_TOTAL_OPEN_RISK.md` §2 that bind the size — e.g.,
  `[risk_budget, stage_cap, conviction_cap, setup_quality_cap]`.
- **initial_size_pct:** the resulting initial position size as a
  percent of equity (Stage 1/2 base = 10%; Stage 2 max = 20% only
  after positive feedback).
- **max_size_pct:** the ceiling allowed for this name today.
- **size_up_rule:** what positive feedback would unlock an Add-on
  Entry (`ENTRY_TACTICS_SPEC.md` §5.9).

---

## Sell Plan

- **trim_into_strength_triggers:** any of `plus_5_partial`,
  `r_multiple_partial`, `base_extension_20_25`, `climax_session`.
- **trim_into_weakness_triggers:** any of `first_close_below_ma`,
  `failed_higher_low_test`, `adverse_group_signal`.
- **structural_exit_triggers:** at least one of `failed_higher_low`,
  `distribution_print`, `two_closes_below_ma`, `failure_level_break`,
  `group_breakdown`, `key_reversal_bar`.
- **time_stop_window_sessions:** integer (stage-dependent).

---

## Thesis (≤ 3 sentences)

`<plain-language description of what the operator is looking for, framed
as observation rather than recommendation>`

---

## Counter-Thesis (≤ 3 sentences, from the Auditor)

`<the strongest case against this entry, specific to this name's tape /
group / event window>`

---

## Linked Audit

- **linked_audit_id:** `aud-YYYYMMDD-<short>` from the morning audit
  brief.

---

## Disclaimers (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
human_gate_required: true
```

---

## Operator Notes (post-fill, optional)

- `<intraday observations during the primary window>`
- `<reasons for any deviation from this ticket>`
