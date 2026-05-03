# PR #56 Acceptance Criteria

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Scope of This PR

PR #56 adds a **markdown-only dry-run report layer** under
`activation_pack/dry_run_reports/`. The layer contains a template
shape, a Korean drafting prompt, and these acceptance criteria. The
PR does not modify the validator, the fixtures, the schemas, the
operating package, the doctrine, or any engine code.

---

## 2. File Set (Acceptance Set)

The PR adds **exactly** these files, all under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/dry_run_reports/`:

- [ ] `DRY_RUN_REPORT_TEMPLATE.md`
- [ ] `DRY_RUN_REPORT_PROMPT_KO.md`
- [ ] `DRY_RUN_REPORT_ACCEPTANCE_CRITERIA.md` (this file)

Total: **3 files, all `.md`**.

---

## 3. Path / Type Constraints

- [ ] All added files are `.md`. No JSON, no Python, no shell, no
      notebook, no archive, no image, no PDF.
- [ ] All added files live under
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/dry_run_reports/`.
- [ ] No file outside this subdirectory is added or modified.

---

## 4. No Modifications to Prior Layers

- [ ] PR #50 Core Doctrine files are not modified
      (`PBKR_V4_SUPREME_DOCTRINE.md`, `PBKR_V4_GROWTH_POLICY.md`,
      `PBKR_V4_KOREAN_MARKET_ADAPTATION.md`,
      `ENTRY_TACTICS_SPEC.md`,
      `SELL_RULES_POSITION_MANAGEMENT.md`,
      `POSITION_SIZING_TOTAL_OPEN_RISK.md`,
      `MARKET_CYCLE_SYSTEM_KR.md`,
      `SCREENING_WATCHLIST_SYSTEM.md`, `SNIPE_DAILY_PROCESS.md`).
- [ ] PR #52 Operating Package files are not modified (anything
      under `00_README_PBKR_V4_OPERATING_PACKAGE.md`,
      `MANIFEST_PR51.json`, or the six PR #52 subdirectories).
- [ ] PR #53 Activation files under `activation_pack/` (excluding
      this PR's `dry_run_reports/` subdirectory) are not modified.
- [ ] PR #54 fixture files under `activation_pack/dry_run_fixtures/`
      (other than this PR's directory) are not modified.
- [ ] PR #55 validator files (`validate_fixtures.py` and
      `VALIDATOR_README.md`) are not modified.
- [ ] No engine code modified (parser / bridge / merge / build /
      emit / ticker_map / Kiwoom / WiseReport / Drive script).

---

## 5. No Real-Data Commitment

- [ ] No real ticker symbol, real company name, real KR exchange
      code, or real DART filing number appears in any added file.
- [ ] No real price / quantity / order id / fill price.
- [ ] No real news headline.
- [ ] No actual `validate_fixtures.py` console output is committed
      (the template is a shape, not a captured run).
- [ ] No actual instantiated dry-run report is committed (those
      live in the operator's private journal).
- [ ] No `*.csv`, `*.parquet`, `*.xlsx`, `*.pdf`, `*.png`, `*.jpg`,
      `*.jpeg`, `*.webp`, `*.gif`, archive, or output dump is
      committed.
- [ ] No API key, token, password, bearer token, or secret string
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
- [ ] No Korean retail-trading buy / sell exhortations or urgency /
      certainty equivalents appear.
- [ ] No imperative buy / sell phrasing in English.
- [ ] No price targets or certainty / urgency qualifiers attached
      to a transaction directive.

---

## 7. Doctrinal Consistency

- [ ] Template explicitly states it is **not** a real report and
      that real instantiated reports are kept in the operator's
      private journal, never committed to the repository.
- [ ] Template's Final Dry-Run Status section does not authorize
      automated execution under any value.
- [ ] Korean prompt explicitly forbids execution authorization,
      truthy safety flags, `operator_decision = "execute"`,
      real-data leakage, and committing instantiated reports back to
      the repository.
- [ ] Acceptance criteria reaffirm the human-gate-before-execution
      invariant.

---

## 8. Review Gates (Required Before Merge)

- [ ] Self-audit on the three added files passes for sections 2–7.
- [ ] Codex PR review posted (👍 reaction or P1/P2/P3 findings
      addressed).
- [ ] Operator review confirms the template captures the dry-run
      record-keeping flow without leaking into execution semantics.
- [ ] No outstanding `revise_required` review threads.

---

## 9. Branch / Push Constraints

- [ ] Branch is `docs/pbkr-v4-dry-run-report-template-pr56`.
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
