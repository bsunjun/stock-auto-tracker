# PR #63 Acceptance Criteria

This document lists the acceptance criteria that PR #63 must satisfy
before it is merged.

## Structural Criteria

- [ ] Exactly seven new markdown files are added under
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/private_journal_observation_runbook/`.
- [ ] All seven new files have the `.md` extension.
- [ ] All seven new files reside under the
      `private_journal_observation_runbook/` directory and nowhere
      else.
- [ ] No file outside `private_journal_observation_runbook/` is
      created or modified.

## Non-Modification Criteria

- [ ] No file from PR #50 – PR #62 is modified.
- [ ] `validate_fixtures.py` is not modified.
- [ ] No fixture file is modified.
- [ ] No schema file is modified.
- [ ] No engine code is modified.
- [ ] No Python source file is added.
- [ ] No shell script is added.
- [ ] No CI configuration is modified.
- [ ] No broker / API / Kiwoom / WiseReport / Drive connection code
      is added.

## Content Safety Criteria

- [ ] No real ticker code appears in any added file.
- [ ] No real listed-company name appears in any added file.
- [ ] No real price, volume, or order-book value appears.
- [ ] No real news headline, article body, or attribution appears.
- [ ] No real disclosure identifier appears.
- [ ] No real flow / supply data appears.
- [ ] No real account number, no order id, no fill price, and no
      broker response payload appears.
- [ ] No real chart screenshot, paywalled-PDF dump, or private
      Telegram screenshot appears.
- [ ] No API key, token, password, or session cookie appears.
- [ ] No example uses a real-looking Korean six-digit ticker code.
- [ ] No example uses a real corporate name, real article title, or
      real price.

## Output / Record Artifact Criteria

- [ ] No real generated candidate artifact is committed.
- [ ] No real dry-run output is committed.
- [ ] No real validator output is committed.
- [ ] No real observation output is committed.
- [ ] No real approval record is committed.
- [ ] No real private-journal note instance is committed. The repo
      holds policy and templates only.

## Flag / Field Criteria

- [ ] No occurrence of the `direct_trade_signal` flag set truthy in
      any added file.
- [ ] No occurrence of the `trade_signal` field set truthy or set
      to a numeric `1` literal in any added file.
- [ ] No occurrence of the `automatic_execution_allowed` flag set
      truthy in any added file.
- [ ] No occurrence of the `operator_decision` field set to the
      execute literal in any added file.

## Approval Wording Criteria

- [ ] The required approval wording is referenced verbatim only as
      the prescribed required wording (in the README and / or
      session checklist), never asserted as an actual approval.
- [ ] The forbidden approval phrases are presented only as
      forbidden, not as authorizing.

## Forbidden Korean Wording Criteria

The seven forbidden Korean trade-instruction phrase categories
established in PR #50 – PR #62 must not appear in any added file
(count = 0). The categories are referenced by description only and
are not reproduced literally in this document:

1. Imperative buy command.
2. Imperative sell command.
3. Emphatic / strong buy declaration.
4. Certainty assertion regarding price direction.
5. Sharp-rise prediction phrase.
6. Buy-signal label.
7. Sell-signal label.

For the literal phrase list, see the corresponding doctrine
documents established in PR #50 – PR #62.

## Process Criteria

- [ ] PR is opened as a **draft**.
- [ ] PR title matches the prescribed title.
- [ ] Commit message matches the prescribed commit message.
- [ ] **Codex review is required before merge.**
- [ ] Merge is **not** performed by the agent that opens the PR.
- [ ] The merge of PR #63 alone does **not** start automated
      execution, order placement, candidate scoring, candidate
      recommendation, or broker connection.

## Self-Verification Summary (To Be Confirmed at Merge Time)

- Added files count: 7
- Modified files count: 0 (excluding the 7 new files)
- `validate_fixtures.py` modified: false
- Fixture files modified: false
- Schema files modified: false
- Engine code modified: false
- Python / shell files added: 0
- Broker / API / Kiwoom / WiseReport / Drive connection code
  added: false
- Real ticker / price / news / disclosure / flow / order / account
  data: 0 occurrences
- Real output artifact: 0
- Real approval record artifact: 0
- Real observation output artifact: 0
- Real private-journal note instance: 0
- `direct_trade_signal` flag set truthy: 0 occurrences
- `trade_signal` field set truthy: 0 occurrences
- `automatic_execution_allowed` flag set truthy: 0 occurrences
- `operator_decision` field set to the execute literal: 0
  occurrences
- Forbidden Korean phrase count: 0
- Merge performed by agent: no
