# Trade Ticket Template (Pre-Execution)

> Educational. Not advice. Not a signal source.
> Validates against `schemas/trade_ticket.schema.json`.

---

## Header

- **schema_version:** `v4.1`
- **asof:** `YYYY-MM-DDTHH:MM:SS+09:00`
- **ticket_id:** `tkt-YYYYMMDD-<short>`
- **session_date:** `YYYY-MM-DD`
- **name:** `<anonymized identifier>`

---

## Edge / Setup

- **edge[]:** one or more of `HVE`, `HVIPO`, `HV1`, `RelativeStrength`,
  `NFactor`, `GroupMove`, `GrowthAcceleration`. Cite the specific
  evidence per edge.
- **setup:** one of `LaunchPad`, `Gapper`, `BaseBreakout`,
  `BreakoutFirstPullback`, `ContinuationFlag`, `ReversalOfTrend`.
- **trade_class:** `short_term` | `swing` | `position` |
  `leader_grade_position`.

---

## Entry Tactic

- **entry_tactic:** one of the canonical nine.
- **trigger_level:** `<concrete>`
- **failure_level:** `<concrete>`
- **stop_logic:** `<concrete>`
- **kr_caveat:** `<KR session / designation / sidecar handling>`

---

## Stop

- **stop_level:** `<concrete>`
- **stop_distance_pct:** `<numeric>`
- **stop_evaluation_basis:** `closing` | `intraday_hard`

---

## TOR

- **total_open_risk_before:** `<numeric, % of equity>`
- **total_open_risk_after:** `<numeric, % of equity>`
- Verify: `total_open_risk_after ≤ K * tor_ceiling_pct`.

---

## Position Size Plan

- **risk_budget_pct:** `<numeric, % of equity>`
- **applied_caps[]:** at minimum include `risk_budget` and
  `stage_cap`; add `notional_cap` / `liquidity_cap` / `sector_cap` /
  `conviction_cap` / `setup_quality_cap` as binding.
- **initial_size_pct:** `<numeric, % of equity>` — Stage 1/2 base = 10%,
  Stage 2 max = 20% **only after positive feedback**.
- **max_size_pct:** `<numeric, % of equity>`
- **size_up_rule:** `<what positive feedback would unlock an Add-on>`

---

## Sell Rules

- **trim_into_strength_triggers[]:** any of `plus_5_partial`,
  `r_multiple_partial`, `base_extension_20_25`, `climax_session`.
- **trim_into_weakness_triggers[]:** any of `first_close_below_ma`,
  `failed_higher_low_test`, `adverse_group_signal`.
- **structural_exit_triggers[]:** at least one of `failed_higher_low`,
  `distribution_print`, `two_closes_below_ma`, `failure_level_break`,
  `group_breakdown`, `key_reversal_bar`.
- **time_stop_window_sessions:** `<integer>`

---

## Thesis (≤ 3 sentences, neutral wording)

`<plain-language description of what the operator is observing,
framed as observation, not as recommendation>`

---

## Counter-Thesis (from Auditor)

`<the strongest specific case against this entry>`

---

## Linked Audit

- **linked_audit_pack_id:** `aud-YYYYMMDD-<short>`

---

## Human Gate

- **required:** `true`
- **result:** `pending` (set to `pass` or `deny` by the gate role).
- **unchecked_items[]:** filled by the gate role only.
- **operator_decision:** `pending` (set to `execute` or `abstain`
  by the human operator only after `result = pass`).

---

## Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
