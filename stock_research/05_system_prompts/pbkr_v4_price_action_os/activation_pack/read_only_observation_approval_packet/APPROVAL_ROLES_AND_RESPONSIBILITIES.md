# Approval Roles and Responsibilities

This document defines **who is responsible for what** in any future
read-only real-data observation approval. PR #61 records the role
assignment. PR #61 does **not** activate any role for an actual
approval cycle.

## Common Invariants (All Roles)

- The `automatic_execution_allowed` flag remains set falsy at all
  times. No role is permitted to flip it.
- The human gate remains required. No role may bypass it.
- No role may produce an order, draft order, order ticket,
  reconstructed fill, or execution intent from real data.
- No role may commit real data to this repository. The prohibited
  categories defined in PR #59 / PR #60 apply to every role.

## Human Operator

- Final responsibility for the approval wording. The exact phrase
  in `APPROVAL_WORDING_REQUIREMENTS.md` is recorded by, and only by,
  the human operator.
- Final responsibility for the no-execution boundary. If any role
  appears to drift toward execution, the human operator must stop
  the cycle.
- Responsibility for the private journal. The private journal is
  the only place where any actual observation result or approval
  record is stored. The journal is not pushed to this repository.

## GPT / Orchestrator

- May draft an observation summary based only on allowlisted fields.
- May draft a checklist run-through.
- Must **not** make execution judgements.
- Must **not** suggest order preparation.
- Must **not** rank named instruments as a recommendation.
- Must escalate any ambiguity to the human operator rather than
  resolving it as an execution intent.

## Claude / Auditor

- Audits PR diffs for hard veto conditions: real data leak, policy
  drift, missing approval wording, broken invariants.
- Verifies pre-merge that none of the prohibited content categories
  have entered the diff.
- Verifies pre-merge that none of the prohibited flag truthy
  patterns have entered the diff.
- Has authority to mark a future observation PR as not approvable
  until corrective changes are made.
- Must **not** authorize execution. Audit pass is not execution
  authorization.

## Gemini / News Grounder

- May assist with source-tier classification at the Tier 1 – Tier 5
  level defined in PR #59.
- Must enforce the Tier 5 single-source insufficiency rule: a row
  supported only by Tier 5 must not be promoted as a candidate.
- Must enforce the Tier 1 hard-veto rule: a Tier 1 official negative
  event acts as a hard veto regardless of any other tier.
- Must **not** perform execution judgement.

## Codex / PR Reviewer

- Audits PR diff scope (file count, file paths, file extensions).
- Audits forbidden Korean directive wording (count must remain 0).
- Audits the four prohibited flag-truthy patterns
  (`direct_trade_signal`, `trade_signal`,
  `automatic_execution_allowed`, `operator_decision`) — count must
  remain 0.
- Audits invariant carry-forward from PR #50 – PR #60.
- Has authority to block merge until invariants pass.

## Conflict Resolution

- The strictest reading wins. If two roles disagree, the side that
  blocks observation start prevails until the human operator
  resolves the disagreement in writing in the private journal.
- A blocking decision by Claude / Auditor or Codex / PR Reviewer is
  not overridden by GPT / Orchestrator or Gemini / News Grounder.
- The human operator may override only by recording an explicit
  reasoned note in the private journal, and even then may not
  override the no-execution invariant.
