# Fixture Validator — README

> Educational. Not advice. Not a signal source.
> Read-only. Standard library only. No network. No subprocess. No
> file write. Does not authorize any execution.

---

## 1. Purpose of PR #55

PR #50 (Core Doctrine), PR #52 (Operating Package), PR #53
(Activation / Operator Runbook), and PR #54 (Anonymized Dry-Run
Fixtures) are already merged on `main`.

PR #55 adds a **read-only validator** for the anonymized fixtures
introduced in PR #54. The validator confirms each `*.fixture.json`
file in this directory:

- Parses cleanly as JSON.
- Carries a non-empty `schema_refs` list of repo-relative paths.
- Has artifacts whose shape matches the corresponding PR #52 schema
  in `../../schemas/` (minimal Draft-07 subset).
- Honors signal-safety invariants: the `direct_trade_signal` flag is
  not truthy, the `trade_signal` field is null or false, the
  `automatic_execution_allowed` flag is not truthy,
  `human_gate_required` is true, and `operator_decision` is never
  `"execute"`.
- Honors anonymization invariants: `name` ∈ {Candidate A / B / C},
  dates begin with the synthetic prefix `2099-`, no real ticker /
  long-numeric / URL / brokerage / credential leakage.

The validator is for **fixture / schema consistency checking only**.
It is not an execution authorization, not a market analyzer, and not
a signal feed.

---

## 2. What the Validator Is Not

- Not a network client (no requests, no HTTP, no socket).
- Not a brokerage adapter.
- Not a market-data feed.
- Not a file writer (output is `print()` only).
- Not a subprocess launcher.
- Not a code mutator (does not modify any fixture or schema).
- Not a signal source (does not emit `trade_signal` or
  `direct_trade_signal` truthy under any condition).

The validator imports only `json`, `re`, `sys`, and `pathlib` from
the Python standard library. No third-party packages are required
or accepted.

---

## 3. How to Run

```
cd stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/dry_run_fixtures
python3 validate_fixtures.py
```

No arguments. Output is print-only.

---

## 4. Expected Output

For each fixture, the validator prints either:

```
PASS scenario_<id>_<name>.fixture.json
```

or:

```
FAIL scenario_<id>_<name>.fixture.json:
  - <issue 1>
  - <issue 2>
```

After all fixtures, a summary is printed:

```
---
checked: 6 fixtures
OVERALL: PASS
```

(or `OVERALL: FAIL`).

Exit code:

- `0` on `OVERALL: PASS`
- `1` on `OVERALL: FAIL`

---

## 5. Interpreting Failures

A `FAIL` indicates one of:

- **Schema drift** — a fixture's artifact uses fields not in the
  corresponding PR #52 schema (or omits required fields).
- **Fixture drift** — a fixture stops following the anonymization
  conventions documented in `README_DRY_RUN_FIXTURES.md` §4 and
  enforced by the safety audits in this validator.
- **Safety leak** — a forbidden value appears (e.g., a safety flag
  set truthy, a real ticker pattern, a URL, a credential string).

A `FAIL` is **not**:

- An execution permission.
- A trade signal.
- A recommendation regarding any specific security.
- A reason to override the human gate.

The corrective action for any `FAIL` is to file a follow-up commit
on the appropriate branch that fixes the fixture or aligns the
schema, then re-run the validator. No commit ever sets a safety
flag truthy as a way to "make the validator pass."

### 5.1 First-run discovery (PR #55)

On its first run against the fixtures merged in PR #54, the
validator correctly identified one schema drift: the S5 fixture's
`artifacts.trade_ticket_with_missing_time_stop` contained a
`fixture_note` field at the artifact level, but
`trade_ticket.schema.json` declares `additionalProperties: false`.
This was the same drift pattern that PR #54's earlier in-flight
fix had already lifted out of the `daily_focus_list*` artifacts
(S2/S4/S6) but had missed inside the trade_ticket artifact in S5.

The fix lifted the `fixture_note` value into a top-level
`fixture_notes` object on the fixture wrapper, mirroring the
S2/S4/S6 pattern. The fix is a separate commit on this branch;
the validator itself was **not** altered, was **not** weakened,
and did **not** special-case `fixture_note`. The
`additionalProperties: false` enforcement remains intact.

After the fix, the validator reports `OVERALL: PASS` (6/6).

---

## 6. Hard Bans (Apply Always)

- Validator must remain read-only. It must never write to disk or
  to a remote endpoint.
- Validator must remain standard-library-only.
- Validator must not import any module suggestive of network,
  brokerage, market-data, or credential handling.
- Validator output is print-only. No log file, no JSON dump, no
  CSV, no PDF, no screenshot.
- The validator's failure to PASS does not authorize any operator
  action other than fixing the underlying fixture or schema drift
  in a follow-up commit.

---

## 7. Future PR Hook (Informational, Non-Binding)

A later PR (e.g., PR #56) **may** introduce a markdown dry-run
report template that summarizes the validator's output for the
operator's journal. Such a template would be markdown only, would
not capture real outputs, and would not authorize execution.
