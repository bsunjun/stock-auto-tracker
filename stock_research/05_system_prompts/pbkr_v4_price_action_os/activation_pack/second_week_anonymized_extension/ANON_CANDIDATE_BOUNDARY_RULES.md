# Anonymized Candidate Boundary Rules

This document defines the **boundary** between three layers of the
PBKR v4 dry-run program:

1. The fixed first-week fixtures (PR #54).
2. The second-week generated anonymized candidates (this PR, #58).
3. The not-yet-authorized real-data stage.

## 1. Fixed first-week fixtures

- Location: `activation_pack/dry_run_fixtures/scenario_s1_*.fixture.json`
  through `scenario_s6_*.fixture.json`.
- Candidates inside these fixtures use the names
  **Candidate A / Candidate B / Candidate C**.
- These fixtures are **immutable** in the context of PR #58.
  PR #58 does not modify them, does not rename them, does not add new
  scenario files alongside them, and does not change
  `validate_fixtures.py`.

## 2. Second-week generated anonymized candidates

- Names: **Candidate X / Candidate Y / Candidate Z** only.
- IDs: `cand-X-anon`, `cand-Y-anon`, `cand-Z-anon` only.
- All values are anonymized tags (`anon-pivot-*`, `anon-stop-*`,
  `anon-failure-*`, `synthetic-tierN-*`) or `2099-` synthetic dates.
- These candidates are **operator training artifacts**. They are
  built locally and **must not be committed** to this repo:
  - No `*.fixture.json` for Candidate X/Y/Z is added to the repo.
  - No validator output capturing Candidate X/Y/Z is committed.
  - No review note containing real data is committed.
- The boundary with first-week fixtures is strict:
  - Do not edit `Candidate A/B/C` to "become" `Candidate X/Y/Z`.
  - Do not place Candidate X/Y/Z files inside
    `activation_pack/dry_run_fixtures/`.

## 3. Real-data stage (not in scope)

- The real-data stage would involve real tickers, real prices, real
  disclosures, real flow, real accounts, or real orders.
- This stage is **explicitly out of scope** for PR #58.
- Entering the real-data stage requires **all** of the following:
  - A separate, dedicated PR.
  - Explicit written approval from the human operator and reviewer.
  - A documented gate that names which real-data sources are
    permitted and under what constraints.
- Until that PR is opened, reviewed, and approved, the program
  remains in anonymized-only mode.

## 4. Automation boundary

- No automatic execution path is created or implied by this PR.
- The validator does not place orders.
- A `PASS` from `validate_fixtures.py` against the committed S1–S6
  fixtures does not authorize alerts, webhooks, broker calls, or
  any downstream side effect. The same applies to a passing manual
  schema-conformance check on a Candidate X/Y/Z draft.
- The `human_gate` block in every generated candidate must be a
  human-in-the-loop checkpoint, not an auto-satisfied flag.

### Validator scope

| Target                                  | `validate_fixtures.py` | Manual schema-conformance |
| --------------------------------------- | ---------------------- | ------------------------- |
| Committed S1–S6 fixtures (A/B/C)        | Yes (week-1 workflow)  | Optional                  |
| Locally-drafted X/Y/Z candidates        | **No** (would FAIL on `name` check) | Yes |

The validator's `ALLOWED_NAMES = {"Candidate A", "Candidate B",
"Candidate C"}` constraint is intentional and unchanged in PR #58.
Bringing X/Y/Z into the validator's allowed name set would require
a separate, explicitly-approved PR.

## 5. Anonymization boundary

The following content is on the **wrong side** of the anonymization
boundary and must never be used, even "for testing":

- Real Korean ticker names and codes (KRX/KOSPI/KOSDAQ).
- Real foreign tickers, ISINs, or CUSIPs.
- Real prices, real OHLCV bars, real volume, real flow numbers.
- Real news headlines, real article URLs, real source attributions.
- Real disclosure (공시) IDs, DART filing numbers, regulatory IDs.
- Real account IDs, broker IDs, order IDs, API keys, tokens, or
  passwords.

If any of the above appears in a draft candidate, the draft is
discarded. It is not redacted and reused.

## 6. Summary

| Layer                    | Names              | Committed? | Real data? | Auto exec? |
| ------------------------ | ------------------ | ---------- | ---------- | ---------- |
| Fixed first-week fixture | Candidate A/B/C    | Yes        | No         | No         |
| Second-week generated    | Candidate X/Y/Z    | **No**     | No         | No         |
| Real-data stage          | (not in scope)     | TBD by separate PR | TBD by separate PR | No |
