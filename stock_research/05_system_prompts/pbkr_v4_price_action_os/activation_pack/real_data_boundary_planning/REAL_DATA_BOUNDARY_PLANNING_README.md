# PBKR v4 Real-Data Boundary Planning (PR #59)

## Purpose

This PR introduces the **planning checklist** for the boundary between
anonymized dry-run material (PR #50 – PR #58) and any future stage that
might use real data sources. PR #59 itself does **not** add any real
ticker, real price, real news, real disclosure, real flow data, or real
order. It only documents the rules under which a future PR could even
begin to consider read-only real-data observation.

## Position Within the PBKR v4 Activation Pack

- PR #50 — Core Doctrine
- PR #51 — Reserved
- PR #52 — Operating Package
- PR #53 — Activation / Operator Runbook
- PR #54 — Anonymized Dry-Run Fixtures
- PR #55 — Non-Execution Fixture Validator
- PR #56 — Dry-Run Report Template
- PR #57 — First-Week Dry-Run Checklist
- PR #58 — Second-Week Anonymized Candidate Extension
- **PR #59 — Real-Data Boundary Planning Checklist (this PR)**

PR #50 through PR #58 collectively define a fully anonymized dry-run
operating loop. PR #59 is the **planning gate** that sits before any
hypothetical real-data PR. Merging PR #59 does **not** open the
real-data stage. The real-data stage requires:

1. A separate, future PR (referred to as PR #60 in planning terms only).
2. Explicit human approval recorded in writing.
3. Confirmation that no automated execution path exists in the repo.

## What This PR Is

- A markdown-only documentation PR.
- A set of seven planning documents under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/real_data_boundary_planning/`.
- A description of source tiers, allowed field names (names only),
  prohibited field categories, the human approval gate, the future
  shadow observation plan, and acceptance criteria for PR #59.

## What This PR Is NOT

- It is **not** a switch from dry-run to live.
- It is **not** a real-data import.
- It is **not** an execution authorization.
- It does **not** wire any broker, API, or live feed.
- It does **not** modify validators, fixtures, schemas, or engine code.
- It does **not** add Python or shell code.
- It does **not** authorize any automated execution under any condition.

## Hard Rules Carried From PR #50 – PR #58

- No automated execution is allowed in any form.
- A human approval gate is required before any real-data PR is opened.
- Anonymized dry-run material (PR #54 onward) remains the only source of
  fixtures used by the validator.
- The forbidden Korean trade-instruction wording defined in PR #50 –
  PR #58 (the seven categories: imperative buy, imperative sell,
  emphatic buy, certainty assertion, sharp-rise prediction, buy-signal
  label, sell-signal label) remains not permitted in any document.
- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.

## Reading Order

1. `REAL_DATA_BOUNDARY_PLANNING_README.md` (this file)
2. `REAL_DATA_SOURCE_TIERS.md`
3. `REAL_DATA_ALLOWED_FIELDS_DRAFT.md`
4. `REAL_DATA_PROHIBITED_FIELDS.md`
5. `HUMAN_APPROVAL_GATE_FOR_REAL_DATA.md`
6. `SHADOW_OBSERVATION_PLAN.md`
7. `PR59_ACCEPTANCE_CRITERIA.md`

## Merge Posture

- This PR is opened as a **draft**.
- Merge is performed only after Codex review.
- Merge of this PR alone does **not** start the real-data stage.
