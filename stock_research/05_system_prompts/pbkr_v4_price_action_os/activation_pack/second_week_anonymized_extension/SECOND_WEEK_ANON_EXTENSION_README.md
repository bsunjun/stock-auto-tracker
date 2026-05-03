# PBKR v4 Second-Week Anonymized Candidate Extension — README

## Purpose of PR #58

PR #58 adds documentation that defines what the operator does in the
**second week** of the PBKR v4 Price Action OS dry-run program, **after**
the first-week fixed-fixture run (S1–S6) defined in PR #54–#57.

This PR is **markdown-only**. It does not modify the validator, the
fixtures, or any engine code.

## Where this fits in the dry-run program

- Week 1 (PR #54–#57): operator validates against **fixed anonymized
  fixtures** S1–S6 using `validate_fixtures.py`. The candidates in those
  fixtures are *Candidate A / Candidate B / Candidate C* — they are
  pre-committed and immutable.
- Week 2 (this PR, PR #58): operator practices **creating brand-new
  anonymized candidates** *Candidate X / Candidate Y / Candidate Z* on
  their own, runs the validator, and reviews the result in a private
  journal.
- Real-data stage: **out of scope for this PR**. Real data is only
  permitted after a separate, explicitly-approved PR.

## Hard rules for the second week

1. **No real data of any kind.**
   - No real ticker name.
   - No real ticker code.
   - No real price, volume, flow, or order book number.
   - No real news headline, source, or URL.
   - No real disclosure (공시) ID or filing number.
   - No real account, broker, or order ID.
2. **Anonymous identifiers only.**
   - Allowed candidate display names: `Candidate X`, `Candidate Y`,
     `Candidate Z`.
   - Allowed candidate IDs: `cand-X-anon`, `cand-Y-anon`, `cand-Z-anon`.
   - Allowed pivot/stop tags: `anon-pivot-X`, `anon-stop-X`,
     `anon-failure-X` (and the Y/Z equivalents).
   - Allowed synthetic disclosure tags:
     `synthetic-tier1-disclosure`, `synthetic-tier3-report`,
     `synthetic-tier5-unattributable-channel`.
   - Allowed dates: `2099-` prefix only (synthetic future dates).
3. **Operator artifacts are private.**
   - Generated candidate JSON, validator output, and review notes
     **must not** be committed to this repo. They live only in the
     operator's private journal.
4. **Human gate is mandatory.**
   - Every generated candidate must include an explicit `human_gate`
     section. No automatic execution path is acceptable.
5. **PASS is not execution permission.**
   - A `PASS` from `validate_fixtures.py` only means the fixture is
     well-formed under the schema. It is **not** a buy/sell signal,
     not a recommendation, and not an authorization to trade.

## What this PR does *not* do

- Does not change `validate_fixtures.py`.
- Does not change any of the S1–S6 fixtures.
- Does not change any engine code.
- Does not authorize automatic execution.
- Does not move the program to real-data stage.

## Files added by PR #58

All under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/second_week_anonymized_extension/`:

1. `SECOND_WEEK_ANON_EXTENSION_README.md` (this file)
2. `ANON_CANDIDATE_CREATION_GUIDE.md`
3. `DAY_BY_DAY_ANON_EXTENSION_PLAN_KR.md`
4. `ANON_CANDIDATE_BOUNDARY_RULES.md`
5. `SECOND_WEEK_REVIEW_TEMPLATE.md`
6. `PR58_ACCEPTANCE_CRITERIA.md`
