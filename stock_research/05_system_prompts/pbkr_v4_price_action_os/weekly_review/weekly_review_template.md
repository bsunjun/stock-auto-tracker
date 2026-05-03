# Weekly Review Template

> Educational. Not advice. Not a signal source.
> Validates against `schemas/weekly_review.schema.json`.
> Run on the last trading session of the calendar week.

---

## Header

- **schema_version:** `v4.1`
- **week_id:** `wk-YYYY-W##`
- **review_date:** `YYYY-MM-DD`
- **operator:** `<anonymized identifier>`

---

## 1. This Week's Market Regime (MCS-KR)

- KOSPI stage week-start → week-end: `<…>` → `<…>`
- KOSDAQ stage week-start → week-end: `<…>` → `<…>`
- Sub-grade transitions: `<list>`
- `K` trajectory: `<from → to>`
- Recent-10-trades feedback: `<constructive|neutral|deteriorating|adverse>`
- Inputs that drove transitions: `<one or two lines>`

---

## 2. Leading Groups

- Leaders this week: `<list of 3 or fewer KR sector groups>`
- Group rotation events: `<one or two lines>`
- Group consistency vs. last week: `<note>`

---

## 3. Candidate Quality

- Watchlist size at week start: `<count>`
- Watchlist promotions to active: `<count>`
- Watchlist demotions to cold: `<count>`
- Watchlist retirements: `<count>`
- Daily focus list count distribution: `<e.g., 2/3/1/0/3>`
- Setup-proximity advancement: `<count of approaching → tactic_ready>`

---

## 4. Execution Tickets

- Tickets opened: `<count>`
- Tickets passed audit: `<count>`
- Tickets passed human gate: `<count>`
- Tickets executed (operator decision): `<count>`
- Tickets passed gate but not executed (operator chose to abstain):
  `<count>`

---

## 5. TOR Management

- TOR_pct trajectory: `<from → to>`
- Stage cap pressure: `<met / under>`
- Sector cap incidents: `<count>`
- Correlation throttle incidents: `<count>`

---

## 6. Exit Quality

For each closed trade, log exit category and process-cleanliness:

| modelbook_id | exit_category | outcome_class | r_realized | clean? |
|---|---|---|---|---|
| `<id>` | `<cat>` | `<class>` | `<R>` | `yes/no` |

Trim-into-strength was profitable on average? `<yes/no/n_a>`

---

## 7. Process Adherence

- `boxes_required`: `<int>`
- `boxes_passed`: `<int>`
- `adherence_pct`: `<num>`
- Sessions with full ticket fill: `<n / 5>`
- Sessions with zero deviations: `<n / 5>`

Mistake taxonomy summary:

- `process_skip`: `<count>`
- `tactic_drift`: `<count>`
- `stop_drift`: `<count>`
- `size_overrun`: `<count>`
- `sector_overrun`: `<count>`
- `correlation_overrun`: `<count>`
- `audit_override`: `<count>`
- `gate_override`: `<count>`
- `signal_leak`: `<count>`
- `evidence_gap`: `<count>`
- `time_window_breach`: `<count>`

---

## 8. Modelbook Updates

- Closed-trade entries appended this week: `<count>`
- Missed-trade entries appended this week: `<count>`
- Pattern reliability notes: `<one to three sentences>`

---

## 9. Expectancy Review

- Closed-trade count: `<int>`
- Hit rate: `<float in [0,1]>`
- Avg winner R: `<float>`
- Avg loser R: `<float>`
- Expectancy R = `hit_rate * avg_winner_r - (1 - hit_rate) * abs(avg_loser_r)`: `<float>`
- Trim-into-strength contribution: `<one line>`

---

## 10. Drawdown Governor State

- Trailing drawdown at week end: `<pct>`
- R / K scaling currently applied: `<full / 0.75 / 0.50 / 0.25>`
- Restoration progress: `<sessions clean / required>`

---

## 11. Next Week Focus

- `K` adjustment plan: `<hold|dial_down|dial_up>`
- Carry-over watchlist (active): `<count>`
- Pending names approaching tactic-ready: `<count>`
- Known event-risk windows: `<list>`
- Any defaults adjusted (and rationale): `<list>`

---

## 12. Signal Safety (mandatory, exact values)

```yaml
direct_trade_signal: false
trade_signal: null
automatic_execution_allowed: false
human_gate_required: true
```
