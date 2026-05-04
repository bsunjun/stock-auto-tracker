# Observation Start Blockers

This document defines the **hard blockers** that prevent any
read-only real-data observation from starting. Any single blocker
below is sufficient to forbid observation start. PR #61 records the
blockers. PR #61 does **not** clear any of them for any future PR.

## Blocker Categories

### Approval Wording Blockers

- The required approval wording defined in
  `APPROVAL_WORDING_REQUIREMENTS.md` is missing from the approving
  comment.
- The required approval wording is altered: paraphrased, reordered,
  translated, or otherwise not verbatim.
- One or more forbidden approval phrases listed in
  `APPROVAL_WORDING_REQUIREMENTS.md` appear in the approving
  comment.

### Connection Blockers

- A broker connection (live or sandbox) exists in the repository.
- An external trading API connection exists in the repository.
- A Kiwoom (or equivalent retail-broker) order path exists in the
  repository.
- A WiseReport auto-feed exists in the repository.
- A Drive auto-sync exists in the repository.
- A webhook that emits an alert outside the operator's private
  journal exists.
- An automated notification path (email, SMS, push, mobile,
  messaging) exists.

### Output Posture Blockers

- The destination for observation output is undefined. (The only
  permitted destination is the operator's private journal, off this
  repository.)
- A pipeline that would commit observation output to this repository
  is configured or proposed.
- A pipeline that would persist real generated candidate artifacts,
  real dry-run outputs, real validator outputs, or real approval
  records to this repository is configured or proposed.

### Policy Blockers

- The prohibited-field policy from PR #59 / PR #60 has not been
  acknowledged by the human operator for the cycle in question.
- Real order information, real execution information, or real
  account information is mixed into any working artifact.
- Any attempt is in progress to commit real ticker, price, news, or
  disclosure content to this repository.

### Invariant Blockers (Truthy Pattern)

- The `automatic_execution_allowed` flag is set truthy anywhere
  reachable by the cycle.
- The `trade_signal` field is set truthy or set to a numeric `1`
  literal anywhere reachable by the cycle.
- The `direct_trade_signal` flag is set truthy anywhere reachable by
  the cycle.
- The `operator_decision` field is set to the execute literal
  anywhere reachable by the cycle.

### Process Blockers

- Any attempt to bypass the human gate is detected.
- Any attempt to start observation without a private-journal note
  recording the checklist run is detected.
- Any role acting outside its responsibilities as defined in
  `APPROVAL_ROLES_AND_RESPONSIBILITIES.md`.

## When a Blocker Fires

- Observation must **not** start.
- A **corrective PR** is required to address the underlying
  condition before observation can be reconsidered. The corrective
  PR is itself subject to PR #50 – PR #61 invariants and to PR #61
  acceptance criteria for the relevant scope.
- Only a brief **blocker note** is recorded in the private journal,
  describing which blocker fired and what corrective step is being
  proposed.
- The blocker note is **not** committed to this repository.
- Re-attempting observation start requires re-running the
  pre-observation operator checklist in full and re-confirming that
  every blocker has been cleared.

## Out of Scope for This PR

- Implementing automated detection for any of the above blockers.
- Wiring any runtime check or pre-commit hook for these blockers.
- Sample blocker notes (none are reproduced here).
