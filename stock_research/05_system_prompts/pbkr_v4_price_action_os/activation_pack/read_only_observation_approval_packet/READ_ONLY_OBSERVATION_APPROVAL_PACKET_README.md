# PBKR v4 Read-Only Observation Approval Packet (PR #61)

## Purpose

This PR documents the **approval packet** that must be assembled and
reviewed before any future read-only real-data observation is started.
PR #60 documented the operating plan for read-only observation. PR #61
documents the **pre-flight approval material**: the wording
requirements, the operator checklist, the role responsibilities, the
start blockers, and the approval record template.

PR #61 itself does **not** start observation. PR #61 does **not**
introduce real data. PR #61 does **not** wire any broker, API,
Kiwoom, WiseReport, or Drive connection. PR #61 does **not** record
any actual approval. The actual approval, if it ever happens, is
recorded in a private journal — not in this repository — and is gated
by a separate future PR (referenced in planning terms only as
PR #62).

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
- **PR #61 — Read-Only Observation Approval Packet (this PR)**

## What This PR Is

- A markdown-only documentation PR.
- Seven planning documents under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/read_only_observation_approval_packet/`.
- A description of: approval wording requirements, the
  pre-observation operator checklist, the role responsibilities, the
  observation start blockers, an approval record template (with no
  values), and acceptance criteria for PR #61.

## What This PR Is NOT

- It is **not** an observation start.
- It is **not** a recorded approval.
- It is **not** an authorization to consume any real data source.
- It does **not** add any broker, API, Kiwoom, WiseReport, or Drive
  connection.
- It does **not** modify validators, fixtures, schemas, or engine
  code.
- It does **not** add Python or shell code.
- It does **not** authorize any automated execution under any
  condition.
- Its merge alone does **not** begin real-data observation. A
  separate PR (PR #62 in planning terms only) with explicit human
  approval is required.

## Hard Rules Carried Forward

- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.
- The seven Korean trade-instruction phrase categories established in
  PR #50 – PR #60 (imperative buy, imperative sell, emphatic buy,
  certainty assertion, sharp-rise prediction, buy-signal label,
  sell-signal label) remain not permitted in any document.
- Real ticker, real name, real price, real news, real disclosure id,
  real flow, real order, and real account data are not permitted in
  the repository.

## Reading Order

1. `READ_ONLY_OBSERVATION_APPROVAL_PACKET_README.md` (this file)
2. `APPROVAL_WORDING_REQUIREMENTS.md`
3. `PRE_OBSERVATION_OPERATOR_CHECKLIST.md`
4. `APPROVAL_ROLES_AND_RESPONSIBILITIES.md`
5. `OBSERVATION_START_BLOCKERS.md`
6. `OBSERVATION_APPROVAL_RECORD_TEMPLATE.md`
7. `PR61_ACCEPTANCE_CRITERIA.md`

## Merge Posture

- Opened as a **draft**.
- Codex review is required before merge.
- Merge of this PR alone does **not** start real-data observation.
- Merge is **not** performed by the agent that opens the PR.
