# First-Week Dry-Run Checklist

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.
>
> **The first week after PR #56 merge is a dry-run-only period.**
> No real candidate, no real ticker, no real order, no real news,
> no real disclosure number. Validator output and instantiated
> reports are written to the operator's private journal — they are
> never committed to this repository.

---

## 1. Daily Routine (Run Each of the First Five Trading Sessions)

For each session in the first week, the operator runs the routine
below in order. Estimated duration: 60–90 minutes total.

### 1.1 Environment + Validator

- [ ] Repository is at the latest `main` (no in-flight branches
      consumed by this routine).
- [ ] Working tree clean before the run.
- [ ] `python3 validate_fixtures.py` from
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/dry_run_fixtures/`
      executed.
- [ ] Validator output observed: `OVERALL: PASS`, exit code 0.

### 1.2 Fixture Hand-Walk (S1 → S6)

For each scenario, the operator follows the path documented in
`activation_pack/HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md` and the
expectations documented in `activation_pack/DRY_RUN_PROTOCOL_ANONYMIZED.md` §2:

- [ ] **S1 — Clean Pass** — confirm focus-list draft validates,
      audit returns `pass`, gate returns `pass`,
      `operator_decision` stays `pending`.
- [ ] **S2 — Hard Veto** — confirm auditor `block` with finding
      `A001`; chain stops at audit; no gate evaluation.
- [ ] **S3 — Tier-5 Demote** — confirm Tier-5-only sourcing
      yields `A204`; Candidate C never enters snipe queue.
- [ ] **S4 — TOR Saturation** — confirm focus list compresses
      from 2 to 1; Candidate A returns `revise_required` with
      `A102`; Candidate B passes.
- [ ] **S5 — Gate Deny** — confirm gate `deny`;
      `unchecked_items` includes
      `sell_rules.time_stop_window_sessions`; operator stays
      `abstain`.
- [ ] **S6 — No-Action Day** — confirm Stage 4 / defensive
      regime; focus list empty; no-action journal filled with
      reason `regime_defensive`.

### 1.3 Private Report Drafting

- [ ] Use `activation_pack/dry_run_reports/DRY_RUN_REPORT_TEMPLATE.md`
      as the **shape** for the private report.
- [ ] Optionally invoke
      `activation_pack/dry_run_reports/DRY_RUN_REPORT_PROMPT_KO.md`
      to ask Claude Code or GPT for a draft from the validator
      output and walk-through notes.
- [ ] **The draft is reviewed by the operator and then written to
      the operator's private journal**, never to this repository.

### 1.4 Signal-Safety Verification

For every artifact reviewed during the day:

- [ ] `direct_trade_signal == false` everywhere observed.
- [ ] `trade_signal ∈ {null, false}` everywhere observed.
- [ ] `automatic_execution_allowed == false` everywhere observed.
- [ ] `human_gate_required == true` everywhere observed.
- [ ] No `operator_decision == "execute"` anywhere observed.

A single violation fails the day's dry run.

### 1.5 Anonymization Verification

- [ ] All names in any reviewed artifact are `Candidate A` /
      `Candidate B` / `Candidate C`.
- [ ] All identifiers contain `cand-A-anon` / `cand-B-anon` /
      `cand-C-anon` substrings.
- [ ] All dates begin with the synthetic prefix `2099-`.
- [ ] All sources begin with `synthetic-tier...-`.
- [ ] No real ticker / KR exchange code / DART filing number
      observed.
- [ ] No URL leakage observed.

### 1.6 Human-Gate Verification

- [ ] Every fixture's `human_gate_required` is `true`.
- [ ] No artifact in the dry-run record claims execution
      authority on the operator's behalf.
- [ ] No agent in the dry-run record interprets a gate `pass` as
      authorization to transact.

---

## 2. Weekly Wrap-Up (End of the First Week)

After the fifth dry-run session:

- [ ] Run a meta-review across the week's five private reports.
- [ ] Summarize: validator runs (5 expected, 5 observed),
      fixture pass count (30 expected — 6 fixtures × 5 days),
      any safety / anonymization / gate violations (must be 0).
- [ ] If all clean: the operator may consider transitioning to
      processing a single anonymized candidate per day for the
      second week. **A real candidate is never introduced this
      week.**
- [ ] If any violation: the violation is documented in the
      operator's private postmortem, a corrective-action PR is
      drafted (if doctrinal), and the dry-run-only week is
      extended.

---

## 3. Hard Bans (Apply to the Entire Week)

- No real ticker / company name / KR exchange code / DART
  filing number / news headline / order / fill / quantity / price
  introduced.
- No actual `validate_fixtures.py` console output committed to
  the repository.
- No actual instantiated dry-run report committed to the
  repository.
- No screenshot / PDF / output JSON / CSV produced from real
  market data.
- No API key / token / password stored anywhere in the repository.
- No flip of any safety flag truthy under any pretext.
- No `operator_decision = "execute"` recorded in any artifact.
- No automated execution path connected to any agent or pipeline.
- No buy / sell recommendation wording in any language.

---

## 4. What Counts as a "Successful" First Week

A successful first week ends with all of:

- 5 validator runs, all `OVERALL: PASS`.
- 30 fixture walk-throughs, all matching expected outcomes.
- 0 safety violations, 0 anonymization leaks, 0 gate-logic
  failures.
- 5 private reports written and stored outside the repository.
- 0 commits of real data, real outputs, or real artifacts to the
  repository.
- 0 Codex / human / operator findings that imply execution
  semantics leaked into the dry-run flow.

A "successful" first week authorizes nothing automatically. It
only signals that the operator and the operating package are
mutually consistent enough to consider a more cautious next step.

---

## 5. Disclaimers

- This checklist is an educational record-keeping discipline.
- Nothing in it constitutes investment advice or a recommendation
  regarding any specific security.
- The human operator remains the sole decider for any real
  decision taken outside this repository.
