# PBKR v4 Read-Only Observation Start Gate (PR #62)

## Purpose

This PR documents the **start gate** that sits between the read-only
observation approval packet (PR #61) and any actual read-only
real-data observation activity. The approval phrase referenced in
this PR is the one defined in PR #60 / PR #61:

> read-only real-data observation only

This wording is reproduced here only as the prescribed **required
approval phrase** for the future observation cycle. PR #62 itself is
not an authorization to execute, alert, score candidates, or place
orders. It is markdown documentation of the start-gate posture.

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
- **PR #62 — Read-Only Observation Start Gate (this PR)**

## What This PR Is

- A markdown-only documentation PR.
- Seven start-gate documents under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/read_only_observation_start_gate/`.
- A description of: the approval record storage policy, the Day 0
  Korean precheck, the input boundary checklist, the output private
  journal policy, the abort conditions, and acceptance criteria for
  PR #62.

## What This PR Is NOT

- It is **not** an observation start.
- It is **not** an authorization to execute, alert, or place orders.
- It is **not** a candidate scoring activation.
- It does **not** add any broker, API, Kiwoom, WiseReport, or Drive
  connection.
- It does **not** modify validators, fixtures, schemas, or engine
  code.
- It does **not** add Python or shell code.
- It does **not** commit any actual observation output. Actual
  read-only observation, if it ever happens, is recorded only in the
  operator's private journal — never in this repository.
- Its merge alone does **not** start automated execution, order
  placement, candidate scoring, or candidate recommendation.

## Hard Rules Carried Forward

- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.
- The seven Korean trade-instruction phrase categories established in
  PR #50 – PR #61 (imperative buy, imperative sell, emphatic buy,
  certainty assertion, sharp-rise prediction, buy-signal label,
  sell-signal label) remain not permitted in any document.
- Real ticker, real name, real price, real news, real disclosure id,
  real flow, real order, and real account data are not permitted in
  the repository.
- Actual observation output, actual approval record content, and
  actual candidate artifact content are not permitted in the
  repository. They live only in a private journal.

## Reading Order

1. `READ_ONLY_OBSERVATION_START_GATE_README.md` (this file)
2. `START_GATE_APPROVAL_RECORD_POLICY.md`
3. `OBSERVATION_DAY0_PRECHECK_KR.md`
4. `OBSERVATION_INPUT_BOUNDARY_CHECKLIST.md`
5. `OBSERVATION_OUTPUT_PRIVATE_JOURNAL_POLICY.md`
6. `OBSERVATION_ABORT_CONDITIONS.md`
7. `PR62_ACCEPTANCE_CRITERIA.md`

## Merge Posture

- Opened as a **draft**.
- Codex review is required before merge.
- Merge of this PR alone does **not** start automated execution,
  order placement, candidate scoring, or candidate recommendation.
- Merge is **not** performed by the agent that opens the PR.
