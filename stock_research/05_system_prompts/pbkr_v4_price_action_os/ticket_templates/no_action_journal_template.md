# No-Action Journal Template

> Educational. Not advice. Not a signal source.
> Even days with zero transactions are journaled. The absence of
> action is also a process artifact.

---

## Header

- **session_date:** `YYYY-MM-DD`
- **operator:** `<anonymized identifier>`

---

## 1. Regime

- **kospi_stage / kosdaq_stage / sub_grade:** `<…>`
- **k_multiplier:** `<…>`
- **stage_cap_pct:** `<…>`
- **regime_notes:** `<one line>`

---

## 2. Reason for No Action

Pick the dominant reason (multiple may apply, but identify the
primary one):

- `tor_saturated` — TOR headroom insufficient.
- `no_tactic_ready` — no watchlist name reached `tactic_ready`.
- `audit_blocked` — Auditor blocked all candidates today.
- `gate_denied` — Human Gate denied all candidates today.
- `event_risk_window` — known event window suppressed entries.
- `regime_defensive` — Stage 3 / 4 posture; cash is the prescribed
  position.
- `setup_invalidated` — overnight events invalidated all candidates.
- `operator_choice` — operator chose to abstain despite green checks.

Detail (one paragraph): `<…>`

---

## 3. What Was Observed

- **Daily focus list state:** `<count and per-entry classification:
  executed / passed_gate_no_act / watch_carry / demoted / retired>`
- **Holdings touched:** `<positions where stop migration / trim /
  exit was applied>`
- **Group / sector observations:** `<one or two lines>`

---

## 4. Lessons (one line each, optional)

- `<lesson_1>`
- `<lesson_2>`

---

## 5. Process Adherence

- **boxes_required:** `<integer>`
- **boxes_passed:** `<integer>`
- **adherence_pct:** `<numeric>`

---

## 6. Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
