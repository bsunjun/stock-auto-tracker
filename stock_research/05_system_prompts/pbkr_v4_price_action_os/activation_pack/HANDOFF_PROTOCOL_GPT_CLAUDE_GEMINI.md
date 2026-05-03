# Handoff Protocol — GPT / Claude / Gemini

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Stage Map

```
Gemini (News Grounder)
   ↓ news_grounding_pack
GPT Pro (Orchestrator)
   ↓ daily_focus_list draft + per-entry trade_ticket drafts
Claude Code (Auditor)
   ↓ audit_pack
Claude Code (Human Gate Verifier)
   ↓ gate_result block
Human (You)
   ↓ execute or abstain decision
Claude Code (Journal Review)
   ↓ session journal summary; weekly review on EOW
```

Every arrow is a **structured handoff**. No agent forwards an
unstructured artifact, and no agent forwards an artifact whose
schema validation has failed.

---

## 2. Per-Stage Inputs / Outputs

### 2.1 Gemini — News Grounding

- **Input:** structured request from operator with the contextual
  domain needed (macro / KR-policy / sector / corporate / event
  window).
- **Output:** `news_grounding_pack` matching
  `../schemas/news_grounding_pack.schema.json`. Tier-1–5 source
  tagging; signal vs. noise separation; event-risk windows.
- **Refuse:** "predict the price"; "what should I buy"; Tier-5-only
  load-bearing requests.

### 2.2 GPT Pro — Orchestration

- **Input:** watchlist entries + `news_grounding_pack` +
  `market_cycle` + current TOR state.
- **Output:** `daily_focus_list` matching
  `../schemas/daily_focus_list.schema.json`, with per-entry
  trade-ticket drafts.
- **Refuse:** any input where `news_grounding_pack` Tier-5
  evidence would be load-bearing for a leader-class candidate;
  any request setting safety flags truthy.

### 2.3 Claude Code — Audit

- **Input:** `daily_focus_list` draft + `market_cycle` + TOR state
  + recent-10-trades summary.
- **Output:** `audit_pack` matching
  `../schemas/audit_pack.schema.json`, with per-entry decision
  (`pass` / `block` / `revise_required`), findings, and
  counter-thesis.
- **Refuse:** soft-passing entries that fail hard vetoes; producing
  buy / sell wording.

### 2.4 Claude Code — Human Gate Verification

- **Input:** the trade ticket and its linked `audit_pack`.
- **Output:** gate-result block (`pass` / `deny`, plus
  `unchecked_items`).
- **Refuse:** authorizing on behalf of the operator; relaxing the
  pre-execution checklist.

### 2.5 Human — Decision

- **Input:** the audit pack, the gate-result block, the ticket.
- **Output:** `operator_decision` field on the ticket
  (`execute` or `abstain`).
- **Refuse:** transacting under denied gate; transacting in
  forbidden time windows; transacting without a journal entry.

### 2.6 Claude Code — Journal Review

- **Input:** the session's tickets, position updates, audit packs,
  and modelbook entries.
- **Output:** session journal summary (post-session) or
  `weekly_review` payload (end of week).
- **Refuse:** inferring P&L without process adherence; producing
  buy / sell wording.

---

## 3. Fallbacks (Failure Modes)

| Failure | Fallback |
|---|---|
| News pack: missing source for a candidate | Drop the candidate from focus pool; do not promote. |
| News pack: only Tier-5 sources | Allowed for `short_term` consideration only; never for `swing` / `position` / `leader_grade_position`. |
| Orchestrator: schema validation fails on focus-list draft | Discard the draft; re-request from Orchestrator with the validation error. |
| Auditor: hard veto issued | Drop the entry from focus list. Do not retry without doctrinal change. |
| Auditor: `revise_required` | Send back to Orchestrator with the violations attached; iterate until `pass` or empty list. |
| Gate verifier: `deny` with `unchecked_items` | Operator does not transact. Items are journaled. |
| Human: deny / abstain | No transaction; reason logged in `no_action_journal_template.md`. |
| TOR headroom check fails | Drop the lowest-priority entry; recompute headroom. |
| Official-source risk flag (DART / KIND / exchange) | Setup-invalidating; entry rejected even if otherwise clean. |

---

## 4. Conflict Resolution Priority

When agent outputs disagree, resolve top-down:

1. **Official source (Tier 1)** — DART / KIND / exchange filings,
   central-bank statements, statutory disclosures.
2. **Schema validity** — an artifact failing schema validation is
   never load-bearing.
3. **Auditor veto** — hard / soft / forbidden findings outrank
   downstream synthesis.
4. **Orchestrator synthesis** — the focus-list draft is a
   synthesis of upstream inputs; it does not override its inputs.
5. **News narrative** — Tier 3 / 4 commentary informs but does not
   override Tier 1.

Tier 5 (Telegram-only, chat groups, aggregators, un-attributable
rumors) is never load-bearing for any leader-class decision.

---

## 5. Human Override

The human operator may override the Auditor or the Gate Verifier.
Conditions:

- The override **must** be journaled with the rule that was
  overridden, the reason, and the corrective action.
- An override classified as `audit_override` or `gate_override`
  becomes input to the next weekly review's mistake taxonomy
  (`PBKR_V4_JOURNAL_REVIEW_INSTRUCTIONS.md` §4).
- Repeated overrides on the same rule are a doctrine-review
  trigger (a separate PR; never an inline doctrine edit).
- A profitable override is **still** an override and is discounted
  in the modelbook pattern memory.

---

## 6. Hard Bans on Automated Execution

- No agent may execute on behalf of the operator.
- No tooling integration may convert a `pass` gate into an order.
- No webhook / cron / pipeline may consume any artifact in this
  operating system as a signal feed.
- The schemas explicitly forbid the `direct_trade_signal` flag set
  truthy, the `trade_signal` field set truthy, and the
  `automatic_execution_allowed` flag set truthy.

---

## 7. Observability

Every handoff produces an artifact (file or log line) that the
operator can replay. The minimum trail is:

- `news_grounding_pack` (Gemini output).
- `daily_focus_list` draft (GPT output).
- `audit_pack` (Claude output).
- gate-result block (Claude output).
- final ticket with `operator_decision` set.
- session journal entry referencing all of the above.

If any link is missing, the chain is broken and downstream actions
are not doctrinal.
