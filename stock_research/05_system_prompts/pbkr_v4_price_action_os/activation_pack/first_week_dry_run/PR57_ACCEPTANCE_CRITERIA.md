# PR #57 Acceptance Criteria

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Scope of This PR

PR #57 adds a **markdown-only first-week dry-run layer** under
`activation_pack/first_week_dry_run/`. The layer documents how the
operator runs the dry-run-only first week using PR #53 protocol,
PR #54 fixtures, PR #55 validator, and PR #56 report template
together. The PR does not modify the validator, the fixtures, the
schemas, the operating package, the doctrine, the activation runbook,
the dry-run reports template, or any engine code.

---

## 2. File Set (Acceptance Set)

The PR adds **exactly** these files, all under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/first_week_dry_run/`:

- [ ] `FIRST_WEEK_DRY_RUN_CHECKLIST.md`
- [ ] `DAY_BY_DAY_DRY_RUN_PLAN_KR.md`
- [ ] `PRIVATE_JOURNAL_GUIDE.md`
- [ ] `NO_REAL_DATA_BOUNDARY.md`
- [ ] `PR57_ACCEPTANCE_CRITERIA.md` (this file)

Total: **5 files, all `.md`**.

---

## 3. Path / Type Constraints

- [ ] All added files are `.md`. No JSON, no Python, no shell, no
      notebook, no archive, no image, no PDF.
- [ ] All added files live under
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/first_week_dry_run/`.
- [ ] No file outside this subdirectory is added or modified.

---

## 4. No Modifications to Prior Layers

- [ ] PR #50 Core Doctrine files are not modified.
- [ ] PR #52 Operating Package files are not modified
      (`00_README_PBKR_V4_OPERATING_PACKAGE.md`, `MANIFEST_PR51.json`,
      and the six PR #52 subdirectories).
- [ ] PR #53 Activation files (top-level files in `activation_pack/`)
      are not modified.
- [ ] PR #54 fixture files under `activation_pack/dry_run_fixtures/`
      are not modified.
- [ ] PR #55 validator files
      (`activation_pack/dry_run_fixtures/validate_fixtures.py` and
      `activation_pack/dry_run_fixtures/VALIDATOR_README.md`) are
      not modified.
- [ ] PR #56 dry-run report template files under
      `activation_pack/dry_run_reports/` are not modified.
- [ ] No engine code modified (parser / bridge / merge / build /
      emit / ticker_map / Kiwoom / WiseReport / Drive script).

---

## 5. No Real-Data Commitment

- [ ] No real ticker symbol, real company name, real KR exchange
      code, or real DART filing number appears in any added file.
- [ ] No real price / quantity / order id / fill price / news
      headline.
- [ ] No actual `validate_fixtures.py` console output is committed.
- [ ] No actual instantiated dry-run report is committed.
- [ ] No actual private journal entry is committed.
- [ ] No `*.csv` / `*.parquet` / `*.xlsx` / `*.pdf` / `*.png` /
      `*.jpg` / `*.jpeg` / `*.webp` / `*.gif` / archive / output
      dump is committed.
- [ ] No API key / token / password / bearer token / secret string
      appears.

---

## 6. Forbidden-Phrase Audit

- [ ] No occurrence of the `direct_trade_signal` flag set truthy
      (any whitespace / separator variant).
- [ ] No occurrence of the `trade_signal` field set truthy or set
      to a numeric `1` literal (the `direct_trade_signal` substring
      is excluded from this audit).
- [ ] No occurrence of the `automatic_execution_allowed` flag set
      truthy.
- [ ] No occurrence of `operator_decision = "execute"` in any
      added file.
- [ ] No Korean retail-trading buy / sell exhortations or
      urgency / certainty equivalents appear.
- [ ] No imperative buy / sell phrasing in English.
- [ ] No price targets or certainty / urgency qualifiers attached
      to a transaction directive.

---

## 7. Doctrinal Consistency

- [ ] Checklist explicitly states the first week is **dry-run
      only**.
- [ ] Day-by-day plan reaffirms the seven daily prohibitions at the
      top.
- [ ] Private-journal guide forbids real-data entries even in the
      operator's private storage.
- [ ] No-real-data boundary document enumerates allowed dry-run
      shapes and forbidden real-data categories.
- [ ] All five files reaffirm the human-gate-before-execution
      invariant.
- [ ] No file interprets validator `PASS` or daily `PASS` as
      execution permission.
- [ ] No file interprets a successful first week as automatic
      authorization to introduce real data.

---

## 8. Review Gates (Required Before Merge)

- [ ] Self-audit on the five added files passes for sections 2–7.
- [ ] Codex PR review posted (👍 reaction or P1/P2/P3 findings
      addressed).
- [ ] Operator review confirms the first-week flow matches the
      operator's intent and does not leak into execution semantics.
- [ ] No outstanding `revise_required` review threads.

---

## 9. Branch / Push Constraints

- [ ] Branch is `docs/pbkr-v4-first-week-dry-run-checklist-pr57`.
- [ ] No direct push to `main`.
- [ ] No force-push.
- [ ] No rebase against `main`.
- [ ] PR opens as **draft** initially. Conversion to
      ready-for-review is a separate explicit step.
- [ ] Merge is performed only with explicit operator
      authorization, using the repository's default merge policy.
      Squash and merge-commit are both acceptable per prior PR
      conventions on this stack; rebase is not.

---

## 10. `merge_performed` Field

- [ ] The PR body declares `merge performed: false` until the
      operator explicitly authorizes and executes the merge.

---

## 11. Disclaimers

This document is part of the educational PBKR v4 operating system.
It is not investment advice, does not constitute a recommendation
regarding any specific security, and does not authorize any
automated execution path.
