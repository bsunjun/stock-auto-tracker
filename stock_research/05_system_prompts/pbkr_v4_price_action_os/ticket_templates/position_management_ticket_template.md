# Position Management Ticket Template

> Educational. Not advice. Not a signal source.
> Validates against `schemas/position_update.schema.json`.

---

## Header

- **schema_version:** `v4.1`
- **asof:** `YYYY-MM-DDTHH:MM:SS+09:00`
- **position_update_id:** `pu-<short>`
- **linked_ticket_id:** `tkt-YYYYMMDD-<short>`
- **name:** `<anonymized identifier>`

---

## Action Type

One of:

- `stop_migration` — move stop in the only allowed direction (toward
  reduced risk).
- `trim_into_strength` — partial reduction while structure intact and
  extension condition met.
- `trim_into_weakness` — partial reduction while structure deteriorating
  but stop not yet hit.
- `structural_exit` — exit triggered by structural breakdown.
- `time_stop` — exit triggered by time-stop window expiry.
- `risk_stop` — exit triggered by stop level breach.
- `add_on` — new tranche; requires a fresh setup, trigger, failure,
  and stop, plus stop on existing tranche already at breakeven.

---

## Action Detail

Fill the relevant subset:

- **from_stop_level / to_stop_level** — for `stop_migration` only.
- **trim_pct_of_position** — for `trim_*`.
- **trim_trigger** — one of the trim trigger labels.
- **exit_trigger** — for structural / time / risk exits.
- **add_on_setup / add_on_tactic** — for `add_on`.

---

## Rationale

`<plain-language explanation of why the action is being taken now;
cite tape evidence and link to the relevant doctrine section>`

---

## Human Gate

- **required:** `true`
- **result:** `pending` (set to `pass` or `deny`).
- **unchecked_items[]:** filled by the gate role only.

---

## Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
