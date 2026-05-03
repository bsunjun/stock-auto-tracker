# Failure Case Review Template

> Educational. Not advice. Not a signal source.
> Required for: every loser, every rule violation, every chase, every
> failed stop. Process-first review; not a P&L autopsy.

---

## Header

- **failure_case_review_id:** `fcr-YYYYMMDD-<short>`
- **linked_modelbook_id:** `mb-YYYYMMDD-<short>` (if a closed trade)
- **linked_ticket_id:** `tkt-YYYYMMDD-<short>` (if applicable)
- **session_date:** `YYYY-MM-DD`

---

## 1. Failure Class

Pick one (or more):

- **A — loser_stop** — risk stop hit at the pre-defined level.
- **B — loser_structural** — structural exit triggered before stop.
- **C — loser_time** — time-stop window expired without progress.
- **D — chase** — entered above the trigger by a material margin.
- **E — failed_stop** — stop was widened or evaluated incorrectly.
- **F — process_skip** — required step bypassed.
- **G — signal_leak** — imperative buy/sell or forbidden flag truthy.

A loser of class A on a process-clean trade is **not** a failure of
process — it is correct execution of the doctrine. It is logged for
pattern memory only.

---

## 2. What the Doctrine Prescribed

State the section / rule and what the prescription was:

- Document(s): `<which doctrine file(s)>`
- Section / rule: `<which section>`
- Prescription: `<what should have happened>`

---

## 3. What Actually Happened

Plain narrative; cite tape evidence and timestamps:

`<paragraph>`

---

## 4. Why the Difference

Pick the dominant cause (multiple may apply):

- **Cognitive:** hesitation, overconfidence, fatigue, FOMO.
- **Procedural:** skipped audit, skipped schema validation, skipped
  gate.
- **Tape-driven:** real-time observation that the doctrine did not
  account for.
- **Tooling:** an agent failed to produce its artifact in time.

If tape-driven and a doctrinal blind spot is suspected, log this
case as input to a **future doctrine-review PR**. Do not modify
doctrine inline.

---

## 5. Corrective Action

Stated specifically and with cadence:

- **Immediate (next session):** `<…>`
- **Short-term (this week):** `<…>`
- **Structural (this month or longer; via PR):** `<…>`

---

## 6. Outcome Discounting

If the trade was profitable despite the failure, discount the
outcome in the modelbook pattern memory: a profitable rule violation
is still a rule violation.

`<one line>`

---

## 7. Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
