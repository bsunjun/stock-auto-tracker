# Postmortem Template

> Educational. Not advice. Not a signal source.
> Required for: every stop-out, every structural exit, every process
> deviation. Optional for routine wins. The postmortem is private — it
> belongs to the operator's journal, not to a public artifact.

---

## Header

- **postmortem_id:** `pm-YYYYMMDD-<short>`
- **session_date:** `YYYY-MM-DD`
- **operator:** `<anonymized identifier>`
- **trigger_type:** `stop_out` | `structural_exit` |
  `process_deviation`
- **linked_modelbook_id:** `mb-YYYYMMDD-<short>` (if the postmortem
  follows a closed trade)
- **linked_ticket_id:** `tkt-YYYYMMDD-<short>` (if applicable)

---

## 1. What was the doctrine prescription?

State what the operating-system documents prescribed for this
situation:

- Which document(s)?
  (`SUPREME_DOCTRINE` / `ENTRY_TACTICS_SPEC` /
  `SELL_RULES_POSITION_MANAGEMENT` / `POSITION_SIZING_TOTAL_OPEN_RISK`
  / `MARKET_CYCLE_SYSTEM_KR` / `SCREENING_WATCHLIST_SYSTEM` /
  `SNIPE_DAILY_PROCESS`)
- Which section / rule was relevant?
- What action did the doctrine prescribe?

---

## 2. What was the action actually taken?

State, plainly, what happened:

- Which action was taken?
- At what time / under what tape conditions?
- Was a flag deviated from? (`direct_trade_signal`, `trade_signal`,
  `human_gate_required` — these must remain at their canonical values;
  any deviation is a serious incident.)

---

## 3. If different, why?

If the action diverged from the prescription, write a single-paragraph
honest explanation:

- Was it cognitive (hesitation, overconfidence, fatigue)?
- Was it procedural (skipped audit, skipped schema validation)?
- Was it tape-driven (a real-time observation that the doctrine did
  not account for)?
- Was it tooling (an agent failed to produce its artifact in time)?

If the action was tape-driven and revealed a doctrinal blind spot, log
it as a candidate for a future doctrine-review PR — never modify the
doctrine inline.

---

## 4. Corrective Action

State the **specific** corrective action and the cadence over which it
will be enforced:

- Immediate (next session): `<action>`
- Short-term (this week): `<action>`
- Structural (this month or longer; via PR): `<action>`

---

## 5. Outcome Discounting (optional)

- Was the trade profitable despite the deviation? `<yes / no>`
- If yes, **discount the outcome** in the modelbook pattern memory
  note: a profitable deviation is still a deviation. Reinforce process,
  not P&L.

---

## 6. Linked Adjustments

- Did this postmortem feed an adjustment to next session's `K`?
  `<yes / no, with link to journal entry>`
- Did this postmortem trigger a watchlist demotion?
  `<yes / no>`
- Did this postmortem trigger a doctrine-review PR draft?
  `<yes / no, with PR id when filed>`

---

## Disclaimers (mandatory)

```yaml
direct_trade_signal: false
trade_signal: null
human_gate_required: true
```
