# Second-Week Anonymized Extension Review Template

This template is filled out by the operator at the end of the
second-week extension. The filled-in instance is **private** — it is
saved to the operator's private journal and is **not committed** to
this repo.

The template itself (this file) is the only review artifact tracked
in the repo.

---

## report_id

`<operator-private-id>`  (e.g., `wk2-anon-ext-2099-01-21`)

## week_id

`<week tag>`  (must use a `2099-` synthetic-date based week tag)

## repo_head_sha

`<git rev-parse HEAD at the time of review>`

## manual_schema_conformance_result

For each day's draft, record the result of the **manual
schema-conformance check** (not a `validate_fixtures.py` run; that
binary is not used against X/Y/Z drafts):

- Day 1 — Candidate X clean conformance: `PASS / FAIL`
- Day 2 — Candidate Y hard veto: `PASS / FAIL`
- Day 3 — Candidate Z Tier-5-only demotion: `PASS / FAIL`
- Day 4 — Candidate X / Y TOR saturation: `PASS / FAIL`
- Day 5 — Candidate X gate-deny: `PASS / FAIL`
- Day 6 — no-action synthetic day: `PASS / FAIL`

`PASS` here means schema conformance and anonymization-tag usage
only. It does not authorize execution.

## generated_candidates_review

### Candidate X review

- Did all required fields exist? (`setup`, `edge`, `entry_tactic`,
  `trigger_level`, `failure_level`, `stop_logic`, `stop_level`,
  `sell_rules`, `human_gate`, `signal_safety`)
- Were `anon-pivot-X`, `anon-stop-X`, `anon-failure-X` used
  exclusively for Candidate X levels?
- Was the human gate explicit and not auto-satisfied?
- Were any real-data leaks observed? If yes, describe and confirm
  the draft was discarded.

### Candidate Y review

- Same checklist as Candidate X, scoped to Candidate Y and the
  `anon-*-Y` tags.
- Was the hard-veto invalidation expressed clearly?

### Candidate Z review

- Same checklist as Candidate X, scoped to Candidate Z and the
  `anon-*-Z` tags.
- Was Tier-5-only demotion produced solely from
  `synthetic-tier5-unattributable-channel` inputs?

## signal safety audit

- Confirm: no candidate carried a buy/sell directive.
- Confirm: no candidate implied automatic order routing.
- Confirm: every candidate stated that schema-conformance is not
  execution permission.
- Confirm: `validate_fixtures.py` was not run against any
  Candidate X/Y/Z draft.

## anonymization audit

- Confirm: only `Candidate X / Y / Z` names appeared.
- Confirm: only `cand-X-anon / cand-Y-anon / cand-Z-anon` IDs.
- Confirm: only `anon-*` tags and `synthetic-*` sources.
- Confirm: only `2099-` dated values.
- Confirm: zero occurrences of real ticker, real price, real
  volume, real flow, real news, real disclosure, real account.

## human gate audit

- Confirm: every candidate contained a `human_gate` section.
- Confirm: no candidate marked the human gate as auto-satisfied.
- Confirm: operator did not approve any execution path during the
  week.

## findings

Free-form notes on weak spots, unclear rules, or ambiguous
behaviors observed during the week. Anonymized only.

## corrective actions

Concrete follow-ups for the operator's private journal — for
example, "tighten failure_level definition for Candidate Y in
next iteration". No real data, no real names.

## final status

One of:

- `PASS` — week's anonymized exercise met all rules.
- `RE-RUN_REQUIRED` — issues found that require re-running parts
  of the week before moving on.
- `FAIL` — boundary violation detected (e.g., real data appeared,
  automatic execution attempted, repo commit of generated
  candidate). The week must be redone after the violation is
  documented in the private journal.

---

**Storage rule:** the filled instance of this template is saved
**only** to the operator's private journal. It must not be
committed to this repo.
