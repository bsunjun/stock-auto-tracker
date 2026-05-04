# No-Execution Guardrails

This document records the **no-execution guardrails** that apply
before, during, and after any future read-only real-data observation
stage. PR #60 only documents the guardrails. PR #60 does not enable
any path described as forbidden below, and does not authorize any
party to enable any such path.

## Forbidden Paths

The following are **never** part of read-only observation, and are
**never** authorized by PR #60 or by any successful observation
cycle:

- Any broker connection (live or sandbox).
- Any external trading API connection.
- Any Kiwoom (or equivalent retail-broker) order path.
- Any webhook that emits an alert outside the operator's private
  journal.
- Any auto-notification (email, SMS, push, mobile, messaging) emitted
  without prior human review.
- Any order intent file, draft order ticket, or pre-staged order.
- Any execution artifact, including reconstructed fill prices or
  reconstructed orders.
- Any trade ticket generated from real data.
- Any automatic "screen-to-action" path in which observed data
  becomes a triggered action without a human in the loop.

## Statements

- A successful read-only observation cycle is **not** execution
  permission.
- A successful read-only observation cycle is **not** an instruction
  to a human operator to execute.
- Read-only observation is **not** candidate scoring.
- Read-only observation is **not** order preparation.
- Read-only observation is **not** alerting infrastructure.
- A human gate is required before any execution may even be
  discussed, and that gate is not satisfied by PR #60.
- The human gate is not satisfied by any number of successful
  observation cycles either; the gate is a separate, explicit,
  written approval, distinct from observation output.

## Carry-Forward From Earlier PRs

- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.
- The seven Korean trade-instruction phrase categories established in
  PR #50 – PR #59 (imperative buy, imperative sell, emphatic buy,
  certainty assertion, sharp-rise prediction, buy-signal label,
  sell-signal label) remain not permitted in any document.

## Out of Scope for This PR

- Implementing any guardrail in code.
- Wiring any blocking check at runtime.
- Any sample of an execution artifact.
- Any sample of an alert.
