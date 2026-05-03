# AI Service Mapping

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Purpose

Bind specific AI services to specific PBKR v4 Operating Package
instruction files. The bindings below are the **only** authorized
role assignments in this operating system. Cross-binding (e.g.,
asking GPT to act as Auditor) is not doctrinal.

---

## 2. Service-to-Role Bindings

### 2.1 GPT Pro — Orchestrator

- **Instruction file:**
  `../ai_project_instructions/PBKR_V4_ORCHESTRATOR_INSTRUCTIONS.md`
- **Role:** consume upstream candidate inputs (watchlist + news
  grounding + market cycle + TOR state) and produce a single
  audited-ready `daily_focus_list` draft. Compose initial trade
  ticket drafts that downstream agents validate.
- **Outputs:** `daily_focus_list` (≤ 5 entries; ideal 1–3) and
  per-entry trade-ticket drafts.
- **Forbidden:** producing buy / sell recommendation wording, making
  execution decisions, setting any safety flag truthy, acting as
  Auditor or News Grounder.

### 2.2 Claude Code — Auditor + Human Gate Verifier + Journal Review

- **Instruction files:**
  - `../ai_project_instructions/PBKR_V4_AUDITOR_INSTRUCTIONS.md`
  - `../ai_project_instructions/PBKR_V4_HUMAN_GATE_INSTRUCTIONS.md`
  - `../ai_project_instructions/PBKR_V4_JOURNAL_REVIEW_INSTRUCTIONS.md`
- **Roles:**
  - **Auditor**: hard / soft / missing-evidence / forbidden-signal
    vetoes; counter-thesis per entry.
  - **Human Gate Verifier**: pre-execution checklist; emits a
    pass / deny result that the human operator reads before
    deciding.
  - **Journal Review**: post-session and weekly review; mistake
    taxonomy; expectancy review.
- **Outputs:** `audit_pack`, gate-result block, journal summary,
  weekly review payload.
- **Forbidden:** authoring trade tickets, selecting candidates,
  predicting outcomes, producing buy / sell recommendation wording,
  authorizing executions on behalf of the operator.

### 2.3 Gemini — News Grounder

- **Instruction file:**
  `../ai_project_instructions/PBKR_V4_NEWS_GROUNDER_INSTRUCTIONS.md`
- **Role:** translate macro / news / policy / corporate-disclosure /
  industry-report / newspaper flow into a `news_grounding_pack`
  with explicit Tier-1–5 source tiering.
- **Output:** `news_grounding_pack` (matches
  `../schemas/news_grounding_pack.schema.json`).
- **Forbidden:** authoring tickets, producing buy / sell
  recommendation wording, allowing Tier-5 (Telegram-only) items to
  be load-bearing for any downstream decision, setting any safety
  flag truthy.
- **Telegram-only restriction:** a candidate whose only evidence is
  Tier 5 cannot be promoted to the daily focus list. This is
  enforced upstream by Auditor finding code (`A204`) and re-checked
  here.

### 2.4 Human (You) — Final Gate Owner

- **Instruction file:** *(your own discretion, applied to the
  artifacts above)*
- **Role:** the only entity that decides whether to transact. Reads
  the gate result + audit pack + ticket and chooses execute or
  abstain. Maintains the journal, modelbook, postmortems, weekly
  review, and watchlist hygiene.
- **Forbidden:** delegating execution to an automated path;
  overriding safety flags; bypassing audit; transacting during
  opening / closing auctions or under sidecar / circuit-breaker
  conditions.

---

## 3. Cross-Service Invariants

Every agent above operates under the same four invariants:

```yaml
direct_trade_signal: false
trade_signal: null            # or false
automatic_execution_allowed: false
human_gate_required: true
```

If any agent's prompt or output appears to relax any of these,
treat it as a `forbidden_signal` finding (Auditor code A301–A304)
and refuse the artifact.

---

## 4. Cross-Binding Rules

| Allowed | Forbidden |
|---|---|
| GPT Pro requesting `news_grounding_pack` from Gemini | GPT Pro impersonating Gemini |
| GPT Pro asking Claude Code for an `audit_pack` | GPT Pro emitting an audit decision itself |
| Claude Code refusing to gate-pass when the audit shows `block` | Claude Code authoring a focus list |
| Gemini providing event-window context to GPT Pro | Gemini selecting candidates |
| Human asking any agent to act outside its bound role | Acting outside the bound role |

---

## 5. Audit Trail Requirement

Every artifact produced by any service above carries a self-evident
service tag in its top-level metadata (or in the operator's journal
if the artifact is private), so the audit trail is reconstructable.

The journal records, at minimum:

- Which service produced which artifact.
- Which prior-stage artifact it consumed.
- Which check the human ran before advancing it.
- Whether the human-gate result was `pass` or `deny`.
- Whether the human operator chose `execute` or `abstain`.

---

## 6. Disclaimers

- These bindings are operator-side conventions. The actual AI
  services have no automated transaction privileges.
- This document does not authorize anyone to integrate the bound
  services with a brokerage or any execution venue.
