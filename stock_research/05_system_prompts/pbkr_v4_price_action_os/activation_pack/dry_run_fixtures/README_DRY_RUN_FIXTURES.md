# Dry-Run Fixtures — README

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Purpose of PR #54

PR #50 (Core Doctrine), PR #52 (Operating Package), and PR #53
(Activation / Operator Runbook) are already merged on `main`.

PR #54 adds **anonymized dry-run fixtures**: synthetic JSON examples
that demonstrate how PR #52 schemas plug into the six scenarios
defined in
`../DRY_RUN_PROTOCOL_ANONYMIZED.md`.

These fixtures are **schema-flow examples**. They are not real
operational outputs. The repository commits this directory; the
operator's actual dry-run results are *never* committed (per
`../DRY_RUN_PROTOCOL_ANONYMIZED.md` §3).

---

## 2. What These Fixtures Are (and Are Not)

### Are
- Synthetic illustrations of payload shapes.
- Anonymized by construction: only `Candidate A`, `Candidate B`,
  `Candidate C` (with IDs `cand-A-anon`, `cand-B-anon`,
  `cand-C-anon`).
- Schema-aligned: each artifact in a fixture references the schema
  it represents (`schema_refs`).
- Useful for visually verifying handoff between Orchestrator,
  Auditor, Human Gate, and Journal Review roles.

### Are Not
- Real market output.
- Real ticker / company / order / price / quantity / news / DART
  number.
- A backtest, a forecast, or a recommendation.
- Authorization for any automated execution path.
- A substitute for the operator's own dry-run runs (those are
  private and stay outside the repo).

---

## 3. Files in This Directory

| File | Scenario | Purpose |
|---|---|---|
| `README_DRY_RUN_FIXTURES.md` | — | This file. |
| `scenario_s1_clean_pass.fixture.json` | S1 | Clean pass; entry advances to `human_gate.result = pass` with `operator_decision = pending`. |
| `scenario_s2_hard_veto.fixture.json` | S2 | Auditor `block` on missing `failure_level`; chain stops at audit. |
| `scenario_s3_tier5_demote.fixture.json` | S3 | Tier-5-only sourcing → demoted; never enters snipe queue. |
| `scenario_s4_tor_saturation.fixture.json` | S4 | TOR headroom breach; lower-priority entry → `revise_required`. |
| `scenario_s5_gate_deny.fixture.json` | S5 | Missing `time_stop_window_sessions`; gate `deny` with `unchecked_items`. |
| `scenario_s6_no_action_day.fixture.json` | S6 | Stage 4 / defensive regime; empty focus list; cash posture. |
| `FIXTURE_VALIDATION_NOTES.md` | — | Manual validation notes; mapping to schemas / templates / scenarios. |

Total: **2 markdown + 6 `.fixture.json` = 8 files**.

---

## 4. Anonymization Conventions (Strictly Enforced)

| Field | Allowed values |
|---|---|
| `name` | `Candidate A`, `Candidate B`, `Candidate C` only |
| Identifier (e.g., `watchlist_item_id`, `ticket_id`) | `cand-A-anon`, `cand-B-anon`, `cand-C-anon` derivatives only |
| `trigger_level` / `failure_level` / `stop_level` | text placeholders only (e.g., `anon-pivot-A`, `anon-failure-A`, `anon-stop-A`) |
| `asof` / `session_date` / `date` | synthetic future date (e.g., `2099-01-01`, `2099-01-02`) |
| `source_refs[].source` | synthetic prefix only (e.g., `synthetic-tier1-disclosure`, `synthetic-tier4-newspaper`) |
| `operator_decision` | `pending` or `abstain` only — `execute` is **forbidden** in fixtures |
| `direct_trade_signal` | `false` (const) |
| `trade_signal` | `null` or `false` |
| `automatic_execution_allowed` | `false` (const) |
| `human_gate_required` | `true` (const) |

If any fixture appears to use a real identifier, real price, real
date, or any operational truthy flag, treat that as a regression and
file a fix immediately.

---

## 5. How to Use

1. Read `../DRY_RUN_PROTOCOL_ANONYMIZED.md` first.
2. Open the fixture for the scenario you want to walk through.
3. Match its `schema_refs` against the corresponding files in
   `../../schemas/`.
4. Manually verify the fixture's structure aligns with the schema's
   required and forbidden fields.
5. Use the fixture as input to a hand-walk of the role handoff
   (`../HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md`).
6. **Do not** feed these fixtures into any automated execution path.
   They are illustrative.

---

## 6. Hard Bans (Apply Always)

- No real ticker / company / KR exchange code / DART filing number.
- No real price / quantity / order / fill.
- No real news headline.
- No screenshots, PDFs, real-data CSV / parquet / xlsx.
- No API key / token / password.
- No `direct_trade_signal` truthy. No `trade_signal` truthy. No
  `automatic_execution_allowed` truthy.
- No `operator_decision = "execute"` in any fixture.
- No commit of the operator's actual dry-run outputs.

---

## 7. Future PR Hook (Informational, Non-Binding)

A later PR (e.g., PR #55) **may** introduce a non-execution
validation script that walks the schemas and confirms each fixture
parses against the corresponding schema. Until that script lands,
validation is manual and follows
`FIXTURE_VALIDATION_NOTES.md`.
