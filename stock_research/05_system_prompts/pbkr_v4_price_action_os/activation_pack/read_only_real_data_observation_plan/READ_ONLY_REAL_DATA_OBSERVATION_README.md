# PBKR v4 Read-Only Real-Data Observation Plan (PR #60)

## Purpose

This PR documents the **operational plan** for a future read-only
real-data observation stage. PR #59 documented the boundary itself
(source tiers, allowed field names, prohibited categories, the
approval gate, the shadow observation outline). PR #60 documents the
**operating procedure** to be followed once and only once a separate,
explicitly approved real-data PR begins.

PR #60 itself does **not** start observation. PR #60 does **not**
introduce real data. PR #60 does **not** wire any broker, API, or
live feed.

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
- **PR #60 — Read-Only Real-Data Observation Plan (this PR)**

## What This PR Is

- A markdown-only documentation PR.
- Eight planning documents under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/read_only_real_data_observation_plan/`.
- A description of: observation scope and non-goals, the field
  allowlist policy, the redaction and storage policy, a Korean safe
  observation runbook, the human approval gate for observation, the
  no-execution guardrails, and acceptance criteria for PR #60.

## What This PR Is NOT

- It is **not** an observation start.
- It is **not** a real-data import.
- It is **not** an authorization to consume a real data source.
- It does **not** add any broker, API, Kiwoom, WiseReport, or Drive
  connection.
- It does **not** modify validators, fixtures, schemas, or engine
  code.
- It does **not** add Python or shell code.
- It does **not** authorize any automated execution under any
  condition.
- Its merge alone does **not** begin real-data observation. A separate
  PR with explicit human approval is required.

## Hard Rules Carried Forward

- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.
- The seven Korean trade-instruction phrase categories established in
  PR #50 – PR #59 (imperative buy, imperative sell, emphatic buy,
  certainty assertion, sharp-rise prediction, buy-signal label,
  sell-signal label) remain not permitted in any document.
- Real ticker, real name, real price, real news, real disclosure id,
  real flow, real order, and real account data are not permitted in
  the repository.

## Reading Order

1. `READ_ONLY_REAL_DATA_OBSERVATION_README.md` (this file)
2. `OBSERVATION_SCOPE_AND_NON_GOALS.md`
3. `REAL_DATA_FIELD_ALLOWLIST_POLICY.md`
4. `REAL_DATA_REDACTION_AND_STORAGE_POLICY.md`
5. `SAFE_OBSERVATION_RUNBOOK_KR.md`
6. `HUMAN_APPROVAL_FOR_OBSERVATION.md`
7. `NO_EXECUTION_GUARDRAILS.md`
8. `PR60_ACCEPTANCE_CRITERIA.md`

## Merge Posture

- Opened as a **draft**.
- Codex review is required before merge.
- Merge of this PR alone does **not** start real-data observation.
- Merge is **not** performed by the agent that opens the PR.
