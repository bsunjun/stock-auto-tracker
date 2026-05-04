# PBKR v4 Private-Journal-Only Observation Runbook (PR #63)

## Purpose

This PR documents the **runbook posture** for any future read-only
real-data observation cycle that an operator may run **outside** this
repository, with all notes living in a private journal. PR #62
documented the start gate; PR #63 documents how, in spirit and in
shape, the observation note is allowed to look while it lives in that
private journal.

The approval phrase referenced is the one fixed in PR #60 / PR #61 /
PR #62:

> read-only real-data observation only

## Position Within the PBKR v4 Activation Pack

- PR #50 — Core Doctrine
- PR #52 — Operating Package
- PR #53 — Activation / Operator Runbook
- PR #54 — Anonymized Dry-Run Fixtures
- PR #55 — Non-Execution Fixture Validator
- PR #56 — Dry-Run Report Template
- PR #57 — First-Week Dry-Run Checklist
- PR #58 — Second-Week Anonymized Candidate Extension
- PR #59 — Real-Data Boundary Planning Checklist
- PR #60 — Read-Only Real-Data Observation Plan
- PR #61 — Read-Only Observation Approval Packet
- PR #62 — Read-Only Observation Start Gate
- **PR #63 — Private-Journal-Only Observation Runbook (this PR)**

## What This PR Is

- A markdown-only documentation PR.
- Seven runbook documents under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/private_journal_observation_runbook/`.
- A description of: the observation note shape template (no values),
  the raw-value redline policy, a Korean observation session
  checklist, the labels-only summary policy, the private-journal
  abort and discard rules, and acceptance criteria for PR #63.

## What This PR Is NOT

- It is **not** an observation start.
- It is **not** an automation: there is no scheduler, no cron, no
  webhook, no agent loop wired by this PR.
- It does **not** add any broker, API, Kiwoom, WiseReport, or Drive
  connection.
- It does **not** modify validators, fixtures, schemas, or engine
  code.
- It does **not** add Python or shell code.
- It does **not** authorize any automated execution under any
  condition.
- It does **not** commit any actual observation output, any actual
  approval record, or any actual private-journal note instance.
  Actual notes live only in the operator's private journal — never
  in this repository.
- Its merge alone does **not** start automated execution, order
  placement, candidate scoring, candidate recommendation, or broker
  connection.

## Hard Rules Carried Forward

- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.
- The seven Korean trade-instruction phrase categories established in
  PR #50 – PR #62 (imperative buy, imperative sell, emphatic buy,
  certainty assertion, sharp-rise prediction, buy-signal label,
  sell-signal label) remain not permitted in any document.
- Real ticker, real name, real price, real news, real disclosure id,
  real flow, real order, and real account data are not permitted in
  the repository.
- Actual observation output, actual approval record content, and
  actual private-journal note instance are not permitted in the
  repository.
- Read-only observation is **not** execution approval, **not**
  candidate-scoring approval, **not** order-preparation approval,
  **not** alerting authorization.

## Reading Order

1. `PRIVATE_JOURNAL_OBSERVATION_RUNBOOK_README.md` (this file)
2. `OBSERVATION_NOTE_SHAPE_TEMPLATE.md`
3. `RAW_VALUE_REDLINE_POLICY.md`
4. `OBSERVATION_SESSION_CHECKLIST_KR.md`
5. `OBSERVATION_SUMMARY_LABELS_ONLY_POLICY.md`
6. `PRIVATE_JOURNAL_ABORT_AND_DISCARD_RULES.md`
7. `PR63_ACCEPTANCE_CRITERIA.md`

## Merge Posture

- Opened as a **draft**.
- Codex review is required before merge.
- Merge of this PR alone does **not** start automated execution,
  order placement, candidate scoring, candidate recommendation, or
  broker connection.
- Merge is **not** performed by the agent that opens the PR.
