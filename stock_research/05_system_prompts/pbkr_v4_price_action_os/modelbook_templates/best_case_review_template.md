# Best Case Review Template

> Educational. Not advice. Not a signal source.
> Reviewing **good setups, good entries, good management** is as
> important as reviewing failures. Pattern memory is asymmetric:
> failures teach faster, but successes calibrate the doctrine.

---

## Header

- **best_case_review_id:** `bcr-YYYYMMDD-<short>`
- **linked_modelbook_id:** `mb-YYYYMMDD-<short>`
- **linked_ticket_id:** `tkt-YYYYMMDD-<short>`
- **session_date:** `YYYY-MM-DD`

---

## 1. What Was Good

Pick the dimensions where this case was process-clean (multiple may
apply):

- **Setup quality** — clean structure, multiple constructive
  features.
- **Edge quality** — multiple edges aligned (HVE + RS + Group, etc.).
- **Entry quality** — confirmation requirements met cleanly; no
  chasing.
- **Stop placement** — stop placed where invalidation was crisp.
- **Sizing** — caps applied correctly; size right-sized for
  volatility.
- **Trim execution** — partial trims at extension, not at panic.
- **Stop migration** — to-cost migration completed; trailing
  discipline maintained.
- **Exit quality** — structural / trim / time-stop applied
  appropriately.
- **Process adherence** — every checklist box passed.

---

## 2. Pattern Validation

Did the doctrine's prediction match the realized outcome on this
case? For each of the following, write `aligned`, `partial`, or
`misaligned`, with a one-line note:

- **MCS-KR stage prescription** for entries: `<aligned|partial|misaligned>` — note.
- **Trade class assignment**: `<…>` — note.
- **Trigger / failure / stop levels**: `<…>` — note.
- **Sell rules**: `<…>` — note.
- **Sizing pipeline**: `<…>` — note.

---

## 3. What to Repeat

State, specifically, the elements that are now reinforced for future
cases:

`<one or two paragraphs>`

---

## 4. What Could Still Improve

Even a clean trade has marginal improvements. Note one or two:

- `<improvement_1>`
- `<improvement_2>`

---

## 5. Doctrine Calibration Candidates

If the case suggests a doctrinal calibration (e.g., raising a default
threshold, expanding an enum), capture it here as input to a
**future doctrine-review PR**. Never edit doctrine inline based on a
single case.

`<one line>`

---

## 6. Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
