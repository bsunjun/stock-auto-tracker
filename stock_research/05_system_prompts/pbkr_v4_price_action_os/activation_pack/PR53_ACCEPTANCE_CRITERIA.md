# PR #53 Acceptance Criteria

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Scope of This PR

PR #53 adds an **Activation / Operator Runbook layer** on top of the
PR #50 Core Doctrine and the PR #52 Operating Package. It contains
markdown documents only.

---

## 2. File Set (Acceptance Set)

The PR adds **exactly** these files, all under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/`:

- [ ] `PBKR_V4_ACTIVATION_README.md`
- [ ] `AI_SERVICE_MAPPING.md`
- [ ] `DAILY_OPERATOR_RUNBOOK_KR.md`
- [ ] `HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md`
- [ ] `MANUAL_VALIDATION_CHECKLIST.md`
- [ ] `DRY_RUN_PROTOCOL_ANONYMIZED.md`
- [ ] `PR53_ACCEPTANCE_CRITERIA.md` (this file)
- [ ] `POST_MERGE_INSTALLATION_GUIDE.md`

Total: **8 files, all `.md`**.

---

## 3. Path / Type Constraints

- [ ] All added files are `.md` (no JSON, no Python, no shell, no
      notebook, no archive, no image, no PDF).
- [ ] All added files live under
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/`.
- [ ] No file outside this subdirectory is added or modified.

---

## 4. No Modifications to Prior Layers

- [ ] PR #50 Core Doctrine files are not modified
      (`PBKR_V4_SUPREME_DOCTRINE.md`, `PBKR_V4_GROWTH_POLICY.md`,
      `PBKR_V4_KOREAN_MARKET_ADAPTATION.md`, `ENTRY_TACTICS_SPEC.md`,
      `SELL_RULES_POSITION_MANAGEMENT.md`,
      `POSITION_SIZING_TOTAL_OPEN_RISK.md`,
      `MARKET_CYCLE_SYSTEM_KR.md`, `SCREENING_WATCHLIST_SYSTEM.md`,
      `SNIPE_DAILY_PROCESS.md`).
- [ ] PR #52 Operating Package files are not modified (any file
      under `00_README_PBKR_V4_OPERATING_PACKAGE.md`,
      `MANIFEST_PR51.json`, `ai_project_instructions/`,
      `daily_prompts/`, `schemas/`, `ticket_templates/`,
      `modelbook_templates/`, `weekly_review/`).
- [ ] No engine code modified (parser / bridge / merge / build /
      emit / ticker_map / Kiwoom / WiseReport / Drive script).

---

## 5. Forbidden-Phrase Audit

- [ ] No occurrence of the `direct_trade_signal` flag set truthy
      (any whitespace / separator variant).
- [ ] No occurrence of the `trade_signal` field set truthy or set
      to a numeric `1` literal (the `direct_trade_signal` substring
      is excluded from this audit).
- [ ] No occurrence of the `automatic_execution_allowed` flag set
      truthy.
- [ ] No Korean retail-trading buy / sell exhortations or urgency /
      certainty equivalents appear.
- [ ] No imperative buy / sell phrasing in English
      (e.g., "buy now," "sell now," "strong buy," "actionable
      buy/sell").
- [ ] No price targets or certainty / urgency qualifiers attached
      to a transaction directive.

---

## 6. Real-Artifact Audit

- [ ] No real ticker symbol, real company name, real KR exchange
      code, or real order placeholder appears in any added file.
- [ ] No `*.csv`, `*.parquet`, `*.xlsx`, `*.pdf`, `*.png`, `*.jpg`,
      `*.jpeg`, `*.webp`, `*.gif`, archive, or output dump is
      committed.
- [ ] No API key, token, password, bearer token, or secret string
      appears.

---

## 7. Doctrinal Consistency

- [ ] Activation README explicitly states that PR #50 + PR #52 are
      already merged and are not modified.
- [ ] AI Service Mapping binds GPT Pro / Claude Code / Gemini /
      Human roles consistent with the PR #52 instruction files.
- [ ] Daily Operator Runbook references PR #52 prompts, templates,
      and schemas by relative path; no executable code is
      introduced.
- [ ] Handoff Protocol enumerates the conflict-resolution priority
      with Tier-1 official sources at the top.
- [ ] Manual Validation Checklist enumerates explicit
      forbidden-phrase audits and engine-code-modification audits.
- [ ] Dry-Run Protocol uses anonymized identifiers
      (Candidate A / B / C) and prohibits real-data leakage.
- [ ] Post-Merge Installation Guide forbids API-key storage,
      auto-execution wiring, and recommends a first-week dry-run
      only.

---

## 8. Review Gates (Required Before Merge)

- [ ] Self-audit (Claude) on this PR returns PASS for all sections
      above.
- [ ] Codex PR review posted (👍 reaction or P1/P2/P3 findings
      addressed).
- [ ] Human review confirms the activation layer matches operator
      intent.
- [ ] No outstanding `revise_required` review threads.

---

## 9. Branch / Push Constraints

- [ ] Branch is `docs/pbkr-v4-activation-runbook-pr53`.
- [ ] No direct push to `main`.
- [ ] No force-push.
- [ ] No rebase against `main`.
- [ ] The PR is opened as **draft** initially. Conversion to
      ready-for-review is a separate explicit step.
- [ ] Merge is performed only with explicit operator authorization,
      using the repository's default merge policy. Squash and
      merge-commit are both acceptable; rebase is not.

---

## 10. `merge_performed` Field

- [ ] The PR body and all internal documents declare
      `merge performed: false` until the merge is explicitly
      authorized and executed by the operator.

If any acceptance item above fails, the PR is not ready to merge.
Address the failure with a follow-up commit on this branch (no
force-push) and re-audit.
