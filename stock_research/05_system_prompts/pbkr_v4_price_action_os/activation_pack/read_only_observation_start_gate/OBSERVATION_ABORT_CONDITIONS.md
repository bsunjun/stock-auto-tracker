# Observation Abort Conditions

This document defines the conditions under which a read-only
real-data observation cycle must be **immediately aborted**. Any
single condition below is sufficient to require abort. PR #62
records the conditions. PR #62 does **not** invoke any abort, because
PR #62 does **not** start any cycle.

## Immediate Abort Conditions

### Repository Contamination

- A real ticker code is found in any repository artifact during the
  cycle.
- A real price, volume, order, or account value is found in any
  repository artifact.
- An API key, API token, password, or session cookie is found in any
  repository artifact.
- A raw paywalled-PDF text dump is found in any repository
  artifact.
- A private Telegram screenshot, group-chat screenshot, or DM
  screenshot is found in any repository artifact.
- A real chart screenshot tied to an identifiable instrument and
  timestamp is found in any repository artifact.

### Connection Attempts

- A broker connection (live or sandbox) is being established or has
  been established during the cycle.
- An external trading API connection is being established or has
  been established.
- A Kiwoom (or equivalent retail-broker) order path is being wired
  or has been wired.
- A WiseReport auto-feed is being wired.
- A Drive auto-sync is being wired.

### Invariant Truthy Patterns

- The `automatic_execution_allowed` flag is set truthy anywhere
  reachable by the cycle.
- The `trade_signal` field is set truthy or set to a numeric `1`
  literal anywhere reachable by the cycle.
- The `direct_trade_signal` flag is set truthy anywhere reachable by
  the cycle.
- The `operator_decision` field is set to the execute literal
  anywhere reachable by the cycle.

### Process Violations

- The human gate is bypassed (an attempt to start, continue, or
  finalize the cycle without explicit human action).
- A commit is being prepared that would persist observation output
  to this repository.
- A commit is being prepared that would persist a real approval
  record, real candidate artifact, real dry-run output, or real
  validator output to this repository.

## On Trigger

- The observation cycle is **immediately aborted**.
- The artifact in which the offending condition was discovered is
  **discarded**. Reuse of the artifact is forbidden, because
  incidental traces of the offending content may remain.
- A short **abort note** describing which condition fired and what
  corrective step is being proposed is recorded in the operator's
  private journal. The offending content itself is not transcribed
  into the note.
- The abort note is **not** committed to this repository.
- A **corrective PR** is required before observation may be
  reconsidered. The corrective PR is itself subject to PR #50 –
  PR #62 invariants.
- Re-attempting observation start requires re-running the entire
  Day 0 precheck and re-confirming that every abort condition
  remains untriggered.

## Out of Scope for This PR

- Implementing automated detection for any abort condition.
- Wiring any pre-commit hook or runtime check.
- Any actual abort note. None is reproduced here.
