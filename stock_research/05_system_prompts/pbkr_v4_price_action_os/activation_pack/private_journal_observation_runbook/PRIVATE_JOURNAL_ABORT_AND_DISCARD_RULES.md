# Private Journal Abort and Discard Rules

This document defines the conditions under which a private-journal
observation session must be **aborted** and its in-progress note
**discarded**. Any single condition below is sufficient to require
abort. PR #63 records the rules. PR #63 invokes none of them.

## Abort Conditions

### Raw Value Capture

- A raw ticker code has been transcribed into the in-progress note.
- A raw price (last, bid, ask, fill, or any other) has been
  transcribed.
- A raw news headline or body fragment has been transcribed.
- A raw disclosure number has been transcribed.
- A raw flow / supply numeric figure has been transcribed.
- An account number, sub-account, order id, fill price, or position
  figure has been transcribed.
- A broker response payload (raw or summarized) has been
  transcribed.
- An API token, API key, password, or session cookie has been
  transcribed.
- A real chart screenshot tied to an identifiable instrument and
  timestamp has been pasted in.
- A private Telegram screenshot, group-chat screenshot, or DM
  screenshot has been pasted in.

### Invariant Truthy Patterns

- The `automatic_execution_allowed` flag is set truthy anywhere
  reachable by the session.
- The `trade_signal` field is set truthy or set to a numeric `1`
  literal anywhere reachable by the session.
- The `direct_trade_signal` flag is set truthy anywhere reachable by
  the session.
- The `operator_decision` field is set to the execute literal
  anywhere reachable by the session.

### Process Violations

- The human gate is bypassed (any attempt to start, continue, or
  finalize the session without explicit human action).
- Any attempt is made to commit the in-progress note, in part or in
  whole, to this repository.
- Any attempt is made to commit a real approval record, real
  candidate artifact, real dry-run output, real validator output, or
  real observation output to this repository.

## On Trigger

- The session is **immediately aborted**. No further notes are
  written.
- The in-progress note is **discarded**. It is not reused after a
  scrub: any incidental traces of the offending content are presumed
  to remain.
- A short **abort note** describing which condition fired and what
  corrective step is being proposed is recorded in the operator's
  private journal. The offending content itself is not transcribed
  into the abort note.
- The abort note is **not** committed to this repository.
- The operator considers whether a **corrective PR** is needed. A
  corrective PR is required if the trigger touched repository state
  (for example, a stage that would have committed the offending
  content was prevented by a hook). A corrective PR is itself
  subject to PR #50 – PR #63 invariants.
- Re-attempting observation requires re-running the start gate
  (PR #62) and the Day 0 precheck.

## Statements

- An abort is a normal outcome, not a failure mode to be hidden.
  Recording the abort and walking away is the correct behavior.
- An abort does not unlock execution. No abort outcome — and no
  recovery from an abort — creates execution permission.
- An abort does not unlock candidate scoring. The abort restores the
  status quo only as a session, not as a permission grant.

## Out of Scope for This PR

- Implementing automated abort detection.
- Wiring any pre-commit hook or runtime check.
- Sample abort notes — none are reproduced here.
