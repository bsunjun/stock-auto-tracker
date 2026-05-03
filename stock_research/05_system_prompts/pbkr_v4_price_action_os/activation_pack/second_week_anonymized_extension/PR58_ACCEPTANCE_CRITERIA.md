# PR #58 Acceptance Criteria

The following criteria must all be satisfied before PR #58 is
eligible for merge. Each item is a hard gate.

## File-level criteria

1. PR #58 adds **exactly six** new markdown files. No more, no less.
2. All six files have the `.md` extension.
3. All six files live under
   `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/second_week_anonymized_extension/`.
   No file is added outside this directory.
4. The six files are:
   - `SECOND_WEEK_ANON_EXTENSION_README.md`
   - `ANON_CANDIDATE_CREATION_GUIDE.md`
   - `DAY_BY_DAY_ANON_EXTENSION_PLAN_KR.md`
   - `ANON_CANDIDATE_BOUNDARY_RULES.md`
   - `SECOND_WEEK_REVIEW_TEMPLATE.md`
   - `PR58_ACCEPTANCE_CRITERIA.md`

## Non-modification criteria

5. No file from PR #50–#57 is modified by this PR.
6. `validate_fixtures.py` is not modified.
7. No fixture file (`scenario_s*.fixture.json`) is modified.
8. No engine code is modified.
9. No Python or shell code is added by this PR.

## Anti-leak criteria

10. No real generated candidate artifact is committed.
11. No real validator output is committed.
12. No real dry-run report instance is committed.
13. No real ticker name, ticker code, price, volume, flow, news,
    headline, disclosure number, account, broker, order, API key,
    token, or password is added in any file.

## Signal-safety criteria

14. No occurrence of the `direct_trade_signal` flag set truthy
    (any whitespace / separator variant) in any added file.
15. No occurrence of the `trade_signal` field set truthy or set
    to a numeric `1` literal (the `direct_trade_signal` substring
    is excluded from this audit).
16. No occurrence of the `automatic_execution_allowed` flag set
    truthy in any added file.
17. No occurrence of `operator_decision` set to the execute literal
    in any added file.
18. No Korean retail-trading buy / sell exhortations, no urgency
    or certainty equivalents, no imperative trading directives in
    Korean or English appear in any added file.

## Process criteria

19. The branch name is
    `docs/pbkr-v4-second-week-anonymized-extension-pr58`.
20. The PR is opened as **draft**.
21. Codex review is required prior to merge.
22. The PR is **not** merged by the assistant. Merge is performed
    only after explicit human approval.
23. No direct write to `main` is performed.

## Boundary criteria

24. The PR does not authorize any automatic execution.
25. The PR does not move the program to the real-data stage.
    Moving to real data requires a separate PR with explicit
    approval.
26. The human gate remains a mandatory checkpoint in every
    documented workflow.

## Verification commands (informational)

The following commands may be run locally by reviewers to verify
non-modification and anti-leak criteria. They are informational and
are **not** added as automation in this PR:

- `git diff --name-only main...HEAD` — confirms only the six new
  files are touched.
- A grep for the `direct_trade_signal` flag set truthy in the
  added directory must return zero matches.
- A grep for the `automatic_execution_allowed` flag set truthy in
  the added directory must return zero matches.

If any criterion above is not met, the PR must be revised before
merge.
