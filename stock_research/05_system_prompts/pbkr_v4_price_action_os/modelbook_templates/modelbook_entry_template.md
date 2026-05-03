# Modelbook Entry Template (Closed or Missed Trade)

> Educational. Not advice. Not a signal source.
> One entry per **closed trade** or **missed trade**. Pattern memory
> for the operator. Lessons over P&L.

---

## Header

- **schema_version:** `v4.1`
- **modelbook_id:** `mb-YYYYMMDD-<short>`
- **kind:** `closed_trade` | `missed_trade`
- **entry_session_date:** `YYYY-MM-DD` (closed_trade) or `<date the
  setup was tactic-ready>` (missed_trade).
- **exit_session_date:** `YYYY-MM-DD` (closed_trade only).
- **name:** `<anonymized identifier>`

---

## Classification

- **trade_class:** `short_term` | `swing` | `position` |
  `leader_grade_position`.
- **edge[]:** the edges that were cited at entry / would have been
  cited.
- **setup:** the setup at entry / the setup that resolved.
- **entry_tactic:** the canonical tactic (if applied) or the tactic
  that would have applied.

---

## Outcome

- For `closed_trade`:
  - **exit_category:** `risk_stop` | `structural` |
    `trim_into_strength` | `trim_into_weakness` | `time_stop`.
  - **outcome_class:** `winner_leader` | `winner_enhancer` |
    `winner_short_term` | `loser_stop` | `loser_structural` |
    `loser_time`.
  - **r_multiple_realized:** `<numeric>`
  - **holding_sessions:** `<integer>`
- For `missed_trade`:
  - **outcome_class:** `missed_trade`
  - **why_missed:** one of: `not_on_watchlist`, `proximity_far`,
    `audit_blocked`, `gate_denied`, `tor_saturated`, `event_risk`,
    `operator_choice`.
  - **what_would_have_happened:** `<observed tape outcome over the
    relevant horizon>`

---

## Lesson (one line; ≤ 280 chars)

`<the durable insight, written for the future operator-self>`

Examples:

- "Multi-quarter accelerating EPS plus group leadership produced a
  position trade that ran cleanly — leader_grade was correctly
  assigned, +5% partial was premature."
- "Single-edge candidate (RS only) became a loser_structural at
  failed_higher_low; multi-edge requirement protects."
- "Missed trade: gate_denied for sector_overrun was correct;
  expectancy was negative because of correlation throttle."

---

## Pattern Memory Note (≤ 600 chars)

Did the pattern behave as the doctrine predicted? Be specific:

- Did `trigger_level`, `failure_level`, `stop_logic` capture the
  structure?
- Did the four confirmation requirements align with what the tape
  showed?
- Did the `trade_class` assignment match the holding period actually
  realized?
- Did the size cap match the realized volatility?

If the pattern did not behave as predicted, this note is input to a
**future doctrine-review PR**, never an inline doctrine edit.

---

## Linked Reviews

- **linked_failure_case_review_id:** `fcr-YYYYMMDD-<short>` (when
  `outcome_class` ∈ `loser_*`).
- **linked_best_case_review_id:** `bcr-YYYYMMDD-<short>` (when
  `outcome_class` ∈ `winner_leader` or `winner_enhancer` and the
  trade was process-clean).

---

## Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
