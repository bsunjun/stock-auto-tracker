# Audit Ticket Template

> Educational. Not advice. Not a signal source.
> Per-entry section of an `audit_pack` validating against
> `schemas/audit_pack.schema.json`.

---

## Header

- **entry_ref:** `<focus list entry id>`
- **audit_decision:** `pass` | `block` | `revise_required`

---

## Findings (per finding, repeat block)

```yaml
- severity: hard_veto | soft_veto | missing_evidence | forbidden_signal
  code: A###
  description: <one to three specific sentences>
  suggested_fix: <one to two sentences, optional>
```

### 1. Hard Veto Examples

- `A001` — entry_tactic missing trigger_level / failure_level /
  stop_logic.
- `A002` — stop_plan missing.
- `A003` — initial_size_pct exceeds stage cap.
- `A004` — sell_rules missing or under-specified.
- `A005` — KR exchange designation present.
- `A006` — automatic_execution_allowed set truthy upstream.
- `A007` — direct_trade_signal or trade_signal set truthy upstream.

### 2. Soft Veto Examples

- `A101` — trade_class unsupported by documented growth evidence.
- `A102` — TOR headroom would be exceeded.
- `A103` — sector or correlation cap would be exceeded.
- `A104` — Add-on without prior stop migration to breakeven.
- `A105` — entry tactic dependent on opening / closing auction
  print.

### 3. Missing Evidence Examples

- `A201` — no edge cited.
- `A202` — no setup proximity tag.
- `A203` — no kr_caveat in entry tactic.
- `A204` — Tier-5-only sourcing for a leader / position class.

### 4. Forbidden Signal Examples

- `A301` — imperative buy / sell phrasing detected.
- `A302` — urgency / certainty qualifier attached to a transaction
  directive.
- `A303` — Korean retail-trading buy / sell exhortation detected.
- `A304` — price-target language detected.

---

## Counter-Thesis (mandatory if audit_decision != block)

`<one to three specific sentences citing tape, group, event window, or
operational fragility>`

---

## Risk Notes

- **concentration:** `<sector or single-name concentration note>`
- **correlation:** `<correlation factor note>`
- **event_window:** `<known event window in next 1–2 weeks>`

---

## Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
