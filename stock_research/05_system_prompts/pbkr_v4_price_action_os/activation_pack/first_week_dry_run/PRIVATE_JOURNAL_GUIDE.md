# Private Journal Guide

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. What the Private Journal Is

The **private journal** is the operator's own record of dry-run
sessions, weekly reviews, postmortems, and any other PBKR v4
operating artifacts that contain anything beyond the template
shapes already committed to this repository.

The private journal lives **outside the repository**:

- A local notes app, an encrypted file, a personal pen-and-paper
  notebook, or any other storage the operator controls.
- It is not pushed to GitHub.
- It is not synced into a public service.
- It is not committed in any branch of this repository, including
  the operator's own forks.

The repository commits **only** the templates that shape how the
private journal entries are organized. The instantiated entries
themselves are private artifacts.

---

## 2. What May Appear in the Private Journal

The journal may contain:

- **Synthetic fixture identifiers** — `fx-S1-clean-pass-anon`,
  `cand-A-anon`, etc.
- **Validator PASS / FAIL summary** — the `OVERALL` line and the
  per-fixture line from `validate_fixtures.py`.
- **Walk-through notes** — yes / no answers and short comments
  per scenario, per the `DRY_RUN_REPORT_TEMPLATE.md` shape.
- **Human notes** — operator's reflections on process adherence,
  cognitive state, hesitation, fatigue, surprise.
- **Mistake taxonomy** — labeled deviations using the categories
  documented in
  `ai_project_instructions/PBKR_V4_JOURNAL_REVIEW_INSTRUCTIONS.md`
  §4 (`process_skip`, `tactic_drift`, `stop_drift`, `size_overrun`,
  etc.).
- **Corrective actions** — per-deviation action with cadence
  (`immediate`, `this_week`, `structural_pr`).
- **Pattern memory notes** — for future reference; what worked,
  what felt off.

---

## 3. What May Not Appear in the Private Journal

The journal must not contain any of:

- Real ticker symbols, real company names, real KR exchange codes.
- Real DART filing numbers, real news headlines verbatim.
- Real prices, quantities, order ids, fill prices.
- Account numbers, brokerage credentials, login tokens.
- API keys, OAuth tokens, bearer tokens, cookies, session ids.
- Passwords or pass-phrases.
- Screenshots of real charts, real trading platforms, real news
  articles (paywalled or not).
- Anything that, if disclosed, could identify a real position or
  a real intent to transact.

This rule is **stricter** than the repository's no-real-data rule.
The journal is private but not invulnerable; treat it as if a
future version of yourself or an unauthorized reader could see it,
and decide accordingly.

---

## 4. The Journal Is Not an Execution Artifact

Even when the journal records a daily `OVERALL: PASS`, the journal
does not authorize any automated execution. It is a **record of
process adherence**, not a permission slip.

- A `PASS` entry says: "the schema-flow was consistent today."
- A `PASS` entry does not say: "transact now."
- A `PASS` streak across multiple days does not auto-promote any
  candidate to live processing.
- The transition from dry-run to any non-dry-run mode is gated by
  a separate explicit decision documented in a future PR (no such
  PR exists at the time of writing).

---

## 5. Recommended Entry Shape

Adopt the shape of
`activation_pack/dry_run_reports/DRY_RUN_REPORT_TEMPLATE.md` for
each daily entry. Its sections cover:

- Report metadata (id, date, repo head SHA, validator head SHA).
- Validator result summary.
- Per-fixture result table.
- S1–S6 walk-through reviews.
- Signal-safety / anonymization / schema-drift / human-gate
  audits.
- Findings, corrective actions, and final dry-run status.

Filling all sections is the discipline. Empty sections are
intentional only when the day's scope explicitly excludes them
(e.g., a Day 1 setup entry with no fixture walk-through).

---

## 6. Storage Discipline

- **Single source of truth.** Choose one storage location for the
  journal and stay there. Multiple parallel notebooks fragment
  pattern memory.
- **Encryption at rest** is recommended when the storage is on a
  device that may leave a trusted location.
- **Backup with care.** Backups should respect the same no-real-data
  rule; if a backup mechanism would publish journal contents to a
  cloud surface readable by a third party, the journal contents
  must be free of any sensitive operational detail by construction.
- **Retention.** Older entries inform pattern memory. Do not delete
  reflexively; stale entries can be marked `archive` rather than
  removed.

---

## 7. Drafting With AI (Optional)

The Korean drafting prompt in
`activation_pack/dry_run_reports/DRY_RUN_REPORT_PROMPT_KO.md` may
be used to ask Claude Code or GPT to assemble an initial draft from:

- Validator console output.
- Manually reviewed scenario notes.
- Fixture validation notes.
- Human gate notes.

The AI-generated draft is reviewed line-by-line by the operator
before it is treated as the day's journal entry. The operator's
review confirms:

- No real ticker / order / price / news / disclosure number was
  introduced.
- No safety flag was flipped truthy.
- No `operator_decision = "execute"` was recorded.
- No imperative buy / sell phrasing was introduced.
- No PASS interpretation as execution permission was introduced.

If any check fails, the draft is discarded and the AI is asked to
regenerate from a corrected input.

---

## 8. Repository Boundary

The repository contains:

- The doctrine, operating package, activation runbook, anonymized
  fixtures, validator, report template, and this guide.

The repository does **not** contain:

- Real validator console output.
- Real instantiated dry-run reports.
- Real operator journal entries.
- Real market data, real chart screenshots, real PDF research
  reports.
- Anything generated by an actual operating session that contains
  data beyond the template shape.

Do not commit such artifacts to any branch of this repository,
including hotfix branches, even with `[skip ci]` or similar
shortcuts.

---

## 9. If You Suspect a Leak

If the operator suspects that any of the following has happened:

- Real data was committed to a branch.
- A safety flag was flipped truthy in a committed file.
- An automated execution path was wired up.

Then:

1. Immediately stop dry-run operations.
2. Document the suspected leak in a private postmortem entry.
3. Open a corrective-action PR that removes the leaked artifact
   (without rewriting history; use a follow-up commit on a branch).
4. Do not attempt to "fix" the leak by force-pushing or rebasing
   merged commits. Leaks in merged history require a public,
   reviewed corrective action.

---

## 10. Disclaimers

- This guide is part of the educational PBKR v4 operating package.
- Nothing in it constitutes investment advice or a recommendation
  regarding any specific security.
- The operator is solely responsible for any decisions taken
  outside this repository.
