# Close Review Prompts (Post-Close, KST 15:30–17:00)

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null`.
> `human_gate_required = true`.

---

## 0. Purpose

The close review block produces the day's permanent record:

1. The session journal entry.
2. The modelbook updates (one entry per closed trade).
3. The postmortem entries (one per stop-out, structural exit, or
   policy deviation).
4. Tomorrow's preliminary focus pool.

A session is not complete until all four are written.

---

## 1. Step 1 — Session Journal Entry

Write a journal entry containing:

- End-of-session `MCS-KR` stage and sub-grade.
- End-of-session `TOR_pct`, `K`, per-stage allocation, per-sector
  allocation.
- Per-position state: name (anonymized), trade class, current stop,
  status (held / trimmed / stopped / structural-exited).
- Each entry today: ticket id, edge, setup, tactic, trigger, stop,
  initial size, fill summary.
- Each exit today: category (risk-stop / structural / trim-strength /
  trim-weakness / time-stop), trigger evidence, residual stop, P&L
  attribution.
- Adherence note: any deviation from the documented process and the
  reason.

The journal entry is a private artifact. It is not committed to the
repo.

---

## 2. Step 2 — Modelbook Updates (Operator → Solo)

For each **closed** trade today (full exit), append one entry to the
modelbook using `07_templates/Modelbook_Template.md` and validate
against `05_schemas/PBKR_V4_modelbook_schema.json`. Required:

- Edge cited at entry.
- Setup label.
- Entry tactic.
- Outcome class: { winner-leader, winner-enhancer, winner-short-term,
  loser-stop, loser-structural, loser-time }.
- One-line lesson.
- Pattern memory note: did this pattern behave as the doctrine
  predicted?

Modelbook entries accumulate over time and feed the weekly review
(`07_templates/Weekly_Review_Template.md`).

---

## 3. Step 3 — Postmortem Entries (Operator → Solo)

For each:

- stop-out today,
- structural exit today,
- or policy deviation today,

write one postmortem entry using
`07_templates/Postmortem_Template.md`. Required:

- What was the doctrine prescription?
- What was the action taken?
- If different, why?
- What is the corrective action for next time?

Postmortems are private artifacts. They feed the weekly review.

---

## 4. Step 4 — Tomorrow's Preliminary Focus Pool (Operator → GPT
Orchestrator, Optional)

Optional pre-pass for tomorrow's focus pool. If invoked:

```
Role: Orchestrator.
Task: produce a preliminary focus pool for tomorrow (cap 10).
This is NOT the final daily focus list; that is built fresh in the
morning block.
Inputs:
  - end-of-session MCS-KR stage and sub-grade
  - end-of-session TOR_pct and K
  - active watchlist with setup-proximity tags
  - today's modelbook updates
Output: a candidate_list matching PBKR_V4_candidate_schema.json,
ranked by setup proximity and trade-class consistency.
Required disclaimers per entry: direct_trade_signal=false,
trade_signal=null, human_gate_required=true.
```

The Orchestrator returns a ranked candidate list. This is **input** to
tomorrow's morning block, not a focus list itself.

---

## 5. Step 5 — Weekly Review Trigger Check

If today is the last trading session of the calendar week:

- Run `07_templates/Weekly_Review_Template.md`.
- Review the modelbook entries from the past five sessions for
  pattern reliability and outcome distribution.
- Re-score the active watchlist; demote names whose thesis has
  weakened to `cold` (per
  `SCREENING_WATCHLIST_SYSTEM.md` §11).
- Recompute correlation factors used by the sizing throttle.

If today is the last trading session of the calendar quarter:

- Run a full eligibility re-evaluation on every watchlist name on the
  publication of new financials
  (`PBKR_V4_GROWTH_POLICY.md` §8).

---

## 6. Hard Constraints

- The close review block does **not** transact. The session is closed
  for transactions in the closing window
  (`INTRADAY_PROMPTS.md` §5).
- The close review block does **not** publish to public surfaces (no
  social posts, no Drive uploads).
- The close review block does **not** set any flag truthy.
- No buy / sell recommendation language in any artifact produced
  here.

---

## 7. Failure Mode Recovery

- Modelbook entry fails schema validation: fix the entry; do not
  commit an invalid modelbook.
- Postmortem reveals a systemic deviation: schedule a doctrine review
  (a separate PR; never modify doctrine inline at close).
- Weekly review reveals leader-quality misclassification: downgrade
  the affected names' trade class on tomorrow's preliminary focus
  pool with the reason logged in the postmortem.
