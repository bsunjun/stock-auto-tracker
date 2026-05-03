# Dry-Run Report Template

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.
>
> **This file is a template, not a real report.** Real dry-run
> reports are written to the operator's private journal — they are
> never committed to this repository. The repository commits only
> the template shape.

---

## 1. How to Use

For each manual dry-run pass, the operator instantiates this
template *outside* the repository (e.g., in a personal journal or
local scratch directory). The instantiated report is read by the
operator only and is never pushed back to the repo.

The operator may use
`DRY_RUN_REPORT_PROMPT_KO.md` to ask an AI assistant to generate a
draft report from console output and manually reviewed scenario
notes; the draft must still be reviewed by the operator before it
is treated as final.

---

## 2. Template

```yaml
report_id:                 dryrun-YYYYMMDD-<short>
report_date:               YYYY-MM-DD
operator:                  <anonymized identifier>

repo_head_sha:             <main HEAD at time of dry run>
validator_head_sha:        <commit that introduced the validator
                            being run; PR #55 head or later>
fixture_set_version:       v4.1
operating_package_version: v4.1
core_doctrine_version:     v4.0
```

### 2.1 Validator Result Summary

```yaml
validator_invocation:      "python3 validate_fixtures.py"
validator_exit_code:       <0 | 1>
validator_overall:         <PASS | FAIL>
fixtures_checked:          <integer>
fixtures_pass:             <integer>
fixtures_fail:             <integer>
```

### 2.2 Fixture Result Table

For each fixture:

| fixture | scenario_id | result | issue_count | one-line note |
|---|---|---|---|---|
| `scenario_s1_clean_pass.fixture.json` | S1 | PASS / FAIL | 0..N | … |
| `scenario_s2_hard_veto.fixture.json` | S2 | PASS / FAIL | 0..N | … |
| `scenario_s3_tier5_demote.fixture.json` | S3 | PASS / FAIL | 0..N | … |
| `scenario_s4_tor_saturation.fixture.json` | S4 | PASS / FAIL | 0..N | … |
| `scenario_s5_gate_deny.fixture.json` | S5 | PASS / FAIL | 0..N | … |
| `scenario_s6_no_action_day.fixture.json` | S6 | PASS / FAIL | 0..N | … |

---

## 3. Scenario Walk-Through Reviews

Each section is filled by the operator after a manual hand-walk
through the scenario's expected role-handoff path
(`activation_pack/HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md`).

### 3.1 S1 — Clean Pass

- Did the focus-list draft validate against
  `daily_focus_list.schema.json`? `<yes / no>`
- Did the audit-pack mark the entry as `pass`? `<yes / no>`
- Did the human-gate result come out `pass` with empty
  `unchecked_items`? `<yes / no>`
- Did the fixture's `operator_decision` remain `pending` (never
  `execute`)? `<yes / no>`
- Notes: `<one or two lines>`

### 3.2 S2 — Hard Veto

- Did the auditor return `block` with finding `A001`? `<yes / no>`
- Did the chain stop at audit (no gate evaluation)? `<yes / no>`
- Did the journal record an `audit_block` for Candidate B?
  `<yes / no>`
- Notes: `<one or two lines>`

### 3.3 S3 — Tier-5 Demote

- Did the news-grounding pack tag every Candidate-C item as
  `tier: 5`? `<yes / no>`
- Did the auditor produce `missing_evidence` finding `A204`?
  `<yes / no>`
- Did the focus list exclude Candidate C? `<yes / no>`
- Notes: `<one or two lines>`

### 3.4 S4 — TOR Saturation

- Did the auditor compress the focus list from 2 to 1 entry?
  `<yes / no>`
- Did the auditor cite finding `A102` (TOR breach) on the dropped
  entry? `<yes / no>`
- Did the higher-priority entry pass cleanly? `<yes / no>`
- Notes: `<one or two lines>`

### 3.5 S5 — Gate Deny

- Did the human-gate result come out `deny`? `<yes / no>`
- Did `unchecked_items` include
  `sell_rules.time_stop_window_sessions`? `<yes / no>`
- Did `operator_decision` remain `abstain`? `<yes / no>`
- Notes: `<one or two lines>`

### 3.6 S6 — No-Action Day

- Did the market-cycle classification produce stage_4
  defensive posture? `<yes / no>`
- Did the focus list remain empty? `<yes / no>`
- Was the no-action journal filled with reason
  `regime_defensive`? `<yes / no>`
- Notes: `<one or two lines>`

---

## 4. Signal-Safety Audit

Repeat for each fixture and roll up:

| flag | observed values | violation count |
|---|---|---|
| `direct_trade_signal` | only `false` | 0 |
| `trade_signal` | only `null` or `false` | 0 |
| `automatic_execution_allowed` | only `false` | 0 |
| `human_gate_required` | only `true` | 0 |
| `operator_decision` | only `pending` or `abstain` | 0 |

Any non-zero violation count fails this dry run regardless of any
other section.

---

## 5. Anonymization Audit

| check | expected | observed |
|---|---|---|
| names ⊆ {Candidate A / B / C} | yes | <yes / no> |
| dates begin with `2099-` | yes | <yes / no> |
| no real ticker / exchange code / DART number | none | <none / count> |
| no real news headline | none | <none / count> |
| no URL leak | none | <none / count> |
| no API key / token / password / brokerage / market-data leak | none | <none / count> |

---

## 6. Schema-Drift Audit

| check | expected | observed |
|---|---|---|
| every artifact key matches a known schema prefix or is intentional | yes | <yes / no> |
| no `additionalProperties: false` violation | 0 | <count> |
| no `required` field missing | 0 | <count> |
| every `enum` value in range | yes | <yes / no> |
| every `const` value matched | yes | <yes / no> |
| `schema_refs` entries point to existing files | yes | <yes / no> |

---

## 7. Human-Gate Audit

| check | expected | observed |
|---|---|---|
| every fixture's `human_gate_required` is `true` | yes | <yes / no> |
| no fixture sets `operator_decision = "execute"` | yes | <yes / no> |
| no agent in the dry-run record claims execution authority | yes | <yes / no> |

---

## 8. Findings

For each issue (zero or more), record:

```yaml
- finding_id:        find-YYYYMMDD-<short>
  severity:          info | low | medium | high
  area:              schema_drift | safety_leak | anonymization |
                     gate_logic | tor_logic | news_tier | other
  description:       <one to three sentences>
  reproducer:        <minimal repro, no real data>
```

---

## 9. Corrective Actions

For each finding, record:

```yaml
- action_id:         act-YYYYMMDD-<short>
  related_finding:   find-YYYYMMDD-<short>
  cadence:           immediate | this_week | structural_pr
  description:       <what to change and where>
  responsible_role:  <operator | claude_code | gpt | gemini |
                     codex_reviewer>
```

A `structural_pr` corrective action is filed as a separate PR;
this template never authorizes inline edits to merged PR files.

---

## 10. Final Dry-Run Status

One of:

- `PASS` — all sections clean, validator OVERALL: PASS, no
  open finding above `info`.
- `RE-RUN_REQUIRED` — at least one finding requires a corrective
  action that, once applied, would change the outcome; rerun
  before proceeding.
- `FAIL` — at least one safety leak, schema drift, or gate-logic
  finding that cannot be resolved with a corrective action in this
  cycle.

A `PASS` status authorizes nothing automatically. The operator,
not the dry-run report, decides whether to proceed to live
processing of real candidates — and even then, with full safety
flags intact and the human gate as the final decider.

---

## 11. Hard Bans (Apply to Every Instantiated Report)

- The instantiated report is **not** committed to this repository.
- The instantiated report does **not** contain real ticker /
  exchange code / DART number / news headline / price / quantity /
  order id / fill data.
- The instantiated report does **not** authorize any automated
  execution path.
- The instantiated report does **not** flip any safety flag truthy.
- The instantiated report does **not** record `operator_decision =
  "execute"`.

---

## 12. Disclaimers

This template is an educational record-keeping shape. It is not
investment advice, not a recommendation regarding any specific
security, and not a system that emits machine-actionable signals.
The operator is solely responsible for any decisions taken outside
this repository.
