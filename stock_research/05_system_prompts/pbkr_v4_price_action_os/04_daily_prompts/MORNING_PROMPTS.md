# Morning Prompts (Pre-Open, KST 08:00–08:50)

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null`.
> `human_gate_required = true`.

---

## 0. Purpose

The morning block produces three artifacts in sequence:

1. The MCS-KR stage read for the session.
2. The audited daily focus list (max 5; ideally 1–3).
3. One filled `Daily_Focus_Ticket_Template.md` per focus name.

Anything beyond these three is **out of scope** for the morning block.

---

## 1. Step 1 — Stage Read (Operator → Solo)

Read `MARKET_CYCLE_SYSTEM_KR.md` §4 inputs and produce a one-line
classification:

```
Stage: <1|2|3|4>
Sub-grade: <weak|normal|strong>   (Stage 2 only; otherwise N/A)
K (TOR multiplier): <0.10|0.50|1.00>
Stage cap on new positions: <% of equity>
Recent-10-trades feedback: <constructive|deteriorating|adverse>
Notes: <one line, optional>
```

Log it to the journal before any other agent prompt is sent.

---

## 2. Step 2 — Macro / News Grounding (Operator → Gemini NewsGrounder)

Send the following to Gemini (see
`03_ai_project_instructions/Gemini_NewsGrounder_v4.md`):

```
Role: NewsGrounder.
Task: produce today's news_grounding_brief.
Inputs:
  - MCS-KR stage: <stage>
  - Sub-grade: <sub-grade or N/A>
  - Date: <YYYY-MM-DD>
Required sections: macro context, KR policy/regulation, technology/sector
flow, newspaper flow signal vs. noise, event-risk windows, disclaimers.
Required disclaimers: direct_trade_signal=false, trade_signal=null,
human_gate_required=true.
No buy/sell recommendation language.
```

Gemini returns a `news_grounding_brief` markdown block.

---

## 3. Step 3 — Candidate Compression (Operator → GPT Orchestrator)

Send the following to GPT (see
`03_ai_project_instructions/GPT_PBKR_Orchestrator_v4.md`):

```
Role: Orchestrator.
Task: produce today's daily_focus_list (cap 5; ideal 1–3).
Inputs:
  - candidate_list: <attach JSON matching PBKR_V4_candidate_schema.json>
  - MCS-KR stage: <stage>
  - Sub-grade: <sub-grade or N/A>
  - TOR_pct (current): <value>
  - K (current): <value>
  - news_grounding_brief: <attach Gemini brief>
Reject any candidate missing entry_tactic, trigger_level, failure_level,
stop_logic, size_plan, or sell_plan.
Reject any candidate with growth-as-entry-trigger framing.
Reject any candidate whose trade_class is unsupported by documented
growth evidence.
Required disclaimers per entry: direct_trade_signal=false,
trade_signal=null, human_gate_required=true.
Output must validate against PBKR_V4_focus_list_schema.json.
```

GPT returns a draft focus list.

---

## 4. Step 4 — Audit (Operator → Claude Auditor)

Send the following to Claude (see
`03_ai_project_instructions/Claude_PBKR_Auditor_v4.md`):

```
Role: Auditor.
Task: audit the draft focus list. Produce an audit_brief matching
PBKR_V4_audit_schema.json.
Inputs:
  - draft_focus_list: <attach Orchestrator output>
  - MCS-KR stage: <stage>
  - TOR_pct: <value>
  - K: <value>
  - sector_concentration: <attach>
  - last_10_trades_summary: <attach>
For each focus entry produce:
  - audit_decision ∈ { pass, block, revise_required }
  - rule_violations (R1–R12 ids)
  - counter_thesis (1–3 sentences, specific)
  - risk_notes
Required disclaimers per entry: direct_trade_signal=false,
trade_signal=null, human_gate_required=true.
```

If any entry comes back `block` or `revise_required`, return to Step 3
with the violations attached. Iterate until all entries are `pass` or
the focus list is empty (an empty focus list is a valid morning
outcome).

---

## 5. Step 5 — Ticket Fill (Operator → Solo)

For each focus entry that passed audit, fill one
`07_templates/Daily_Focus_Ticket_Template.md` and validate it against
`05_schemas/PBKR_V4_ticket_schema.json`. Required fields, no
exceptions:

- `name` (anonymized identifier)
- `trade_class`
- `edge`, `setup`, `entry_tactic` (with all five fields)
- `stop_plan`, `size_plan`, `sell_plan`
- `thesis`, `counter_thesis`
- `disclaimers` (the three flags)

A ticket missing any field is invalid. The ticket cannot be the basis
of a transaction unless it validates against the schema.

---

## 6. Step 6 — Snipe-Queue Build (Operator → Solo)

From the validated tickets, build the snipe queue per
`SNIPE_DAILY_PROCESS.md` §3. Cap by current TOR headroom.

---

## 7. Hard Constraints on the Morning Block

- No transactions in the morning block. Transactions belong to the
  primary window of `SNIPE_DAILY_PROCESS.md`.
- No new entries inside the opening auction (`09:00`–`09:15`).
- No "creative" focus entries that bypass the schema or skip the
  Auditor.
- No setting any flag truthy.

---

## 8. Failure Mode Recovery

- If the Orchestrator returns a focus list with any forbidden-phrase
  leak: discard, file an issue, restart.
- If the Auditor returns `block` for all entries: the focus list is
  empty for the day. This is acceptable. Cash is a position
  (`POSITION_SIZING_TOTAL_OPEN_RISK.md` §11).
- If schema validation fails on a ticket: fix the ticket or drop it;
  do not transact on an unvalidated ticket.
