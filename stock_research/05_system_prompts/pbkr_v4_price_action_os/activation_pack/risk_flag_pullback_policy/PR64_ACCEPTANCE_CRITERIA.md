# PR #64 Acceptance Criteria

This document lists the acceptance criteria that PR #64 must satisfy
before it is merged.

## Structural Criteria

- [ ] Exactly seven new markdown files are added under
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/risk_flag_pullback_policy/`.
- [ ] All seven new files have the `.md` extension.
- [ ] All seven new files reside under the
      `risk_flag_pullback_policy/` directory and nowhere else.
- [ ] No file outside `risk_flag_pullback_policy/` is created or
      modified.

## Non-Modification Criteria

- [ ] No file from PR #50 – PR #63 is modified.
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
- [ ] No actual Google Drive URL or file id appears.

## Output / Record Artifact Criteria

- [ ] No real generated candidate artifact is committed.
- [ ] No real dry-run output is committed.
- [ ] No real validator output is committed.
- [ ] No real observation output is committed.
- [ ] No real approval record is committed.
- [ ] No real private-journal note instance is committed.

## Flag / Field Criteria

- [ ] No occurrence of the `direct_trade_signal` flag set truthy in
      any added file.
- [ ] No occurrence of the `trade_signal` field set truthy or set
      to a numeric `1` literal in any added file.
- [ ] No occurrence of the `automatic_execution_allowed` flag set
      truthy in any added file.
- [ ] No occurrence of the `operator_decision` field set to the
      execute literal in any added file.

## Status Misuse Criteria

- [ ] `RISK_FLAG_PULLBACK_WATCH` and `EXTREME_RISK_FLAG_WATCH` are
      documented strictly as watch postures. Neither is described
      as a `PB_TRIGGER`, a 본진 entry, an automatic alert source,
      or an execution authorization anywhere in the added files.
- [ ] No added file describes a 분류 A name (`HARD_EXCLUDE`:
      관리종목 / 상장폐지 실질심사 / 거래정지 / 불성실공시 /
      감사의견 문제 / 횡령/배임 / 회생/파산) as eligible for
      `RISK_FLAG_PULLBACK_WATCH` or `EXTREME_RISK_FLAG_WATCH`.
- [ ] No added file describes a 분류 C name
      (`EXTREME_RISK_FLAG_WATCH`: 투자위험 지정예고 / 투자위험종목
      / 투자경고 후 정지 임박 단계) as directly eligible for
      `RISK_FLAG_PULLBACK_WATCH` while the flag is active.
      Re-classification to `RISK_FLAG_PULLBACK_WATCH` is allowed
      only after the flag is formally lifted to 분류 B.
- [ ] No added file describes a 분류 D name (`NO_ENTRY`:
      매매거래정지 / 상장폐지 실질심사 관련 정지 / 공시불이행
      거래정지) as eligible for any watch posture or candidate
      posture.
- [ ] The four status labels (`HARD_EXCLUDE`, `REGULAR_PB_EXCLUDE`,
      `EXTREME_RISK_FLAG_WATCH`, `NO_ENTRY`) are used consistently
      with the taxonomy in `OFFICIAL_RISK_FLAG_TAXONOMY_KR.md`.

## Forbidden Korean Wording Criteria

The seven forbidden Korean trade-instruction phrase categories
established in PR #50 – PR #63 must not appear in any added file
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
documents established in PR #50 – PR #63.

## Process Criteria

- [ ] PR is opened as a **draft**.
- [ ] PR title matches the prescribed title.
- [ ] Commit message matches the prescribed commit message.
- [ ] **Codex review is required before merge.**
- [ ] Merge is **not** performed by the agent that opens the PR.
- [ ] The merge of PR #64 alone does **not** start automated
      execution, order placement, candidate scoring, or candidate
      recommendation.

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
- Real Google Drive URL or file id: 0 occurrences
- Real output artifact: 0
- Real approval record artifact: 0
- Real observation output artifact: 0
- `direct_trade_signal` flag set truthy: 0 occurrences
- `trade_signal` field set truthy: 0 occurrences
- `automatic_execution_allowed` flag set truthy: 0 occurrences
- `operator_decision` field set to the execute literal: 0
  occurrences
- Forbidden Korean phrase count: 0
- Merge performed by agent: no
