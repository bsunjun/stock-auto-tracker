# Weekly Review Template

> Educational. Not advice. Not a signal source.
> Run on the last trading session of the calendar week as part of the
> close review block (`04_daily_prompts/CLOSE_REVIEW_PROMPTS.md` §5).
> All disclaimer values must remain `direct_trade_signal = false`,
> `trade_signal = null`, `human_gate_required = true`.

---

## Header

- **week_id:** `wk-YYYY-WW` (ISO week)
- **review_date:** `YYYY-MM-DD`
- **operator:** `<anonymized identifier>`

---

## 1. Macro / Regime Recap

- KOSPI MCS-KR stage at week start: `<stage / sub-grade>`
- KOSPI MCS-KR stage at week end: `<stage / sub-grade>`
- KOSDAQ MCS-KR stage at week start: `<stage / sub-grade>`
- KOSDAQ MCS-KR stage at week end: `<stage / sub-grade>`
- Regime transitions during the week: `<list with input citations>`
- `K` (TOR multiplier) trajectory: `<from → to>`

---

## 2. Trade Outcomes

For each trade closed this week, summarize:

| ticket_id | name | trade_class | edge | setup | tactic | exit_category | outcome_class | R_realized | lesson |
|---|---|---|---|---|---|---|---|---|---|
| `<id>` | `<name>` | `<class>` | `<edge>` | `<setup>` | `<tactic>` | `<exit>` | `<outcome>` | `<R>` | `<one line>` |

(Source: modelbook entries from
`05_schemas/PBKR_V4_modelbook_schema.json`.)

---

## 3. Pattern Reliability Audit

For each pattern (setup × tactic) used during the week:

- Hit rate this week: `<n / m>`
- Average R realized: `<value>`
- Did the pattern behave as the doctrine predicted? `<yes / partially /
  no, with one-sentence explanation>`
- If `partially` or `no`, propose a doctrinal adjustment (separate PR)
  with the supporting evidence.

---

## 4. Trade-Class Distribution

- Short-term trades: `<count, avg holding sessions, avg R>`
- Swing trades: `<…>`
- Position trades: `<…>`
- Leader-grade position trades: `<…>`

Was the distribution consistent with the regime
(`MARKET_CYCLE_SYSTEM_KR.md` §6)? If not, why?

---

## 5. True Leader vs. Performance Enhancer Audit

List each currently held name and confirm or revise its classification
(`SELL_RULES_POSITION_MANAGEMENT.md` §8):

| name | classification at entry | classification at week end | reason for change (if any) |
|---|---|---|---|
| `<name>` | `<class>` | `<class>` | `<reason>` |

A demoted name must have its `conviction_cap` and management posture
adjusted on next session's tickets.

---

## 6. Watchlist Hygiene

- Names re-scored: `<count>`
- Names demoted to `cold`: `<count>`; rationale: `<one line each>`
- Names retired: `<count>`; rationale: `<one line each>`
- Correlation factors recomputed: `<yes / no>`

---

## 7. Process Adherence

- Sessions where the morning ticket was filled completely: `<n / 5>`
- Sessions with zero protocol deviations: `<n / 5>`
- Deviations logged: `<count>`; root causes from postmortems:
  `<short list>`

---

## 8. Drawdown Governor State

- Trailing drawdown at week end: `<pct>`
- `R` and `K` scaling currently applied:
  `<full / 0.75 / 0.50 / 0.25>`
- Restoration progress (if applicable): `<sessions of clean process /
  required>`

---

## 9. Recent-10-Trades Feedback

- Hit rate: `<value>`
- Average winner R: `<value>`
- Average loser R: `<value>`
- Trim-into-strength profitability: `<constructive / neutral /
  adverse>`
- Implication for next week's `K`: `<unchanged / dial down / dial up>`

---

## 10. Next Week Plan

- Carry-over watchlist (active): `<count>`
- Pending names approaching tactic-ready: `<count>`
- Known event-risk windows next week: `<list>`
- Adjusted defaults for next week (if any), with rationale:
  `<list>`

---

## Disclaimers (mandatory)

```yaml
direct_trade_signal: false
trade_signal: null
human_gate_required: true
```
