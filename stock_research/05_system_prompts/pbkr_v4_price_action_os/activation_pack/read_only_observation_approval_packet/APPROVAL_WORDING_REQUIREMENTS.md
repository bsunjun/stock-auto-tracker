# Approval Wording Requirements

This document defines the **exact wording requirements** for any
human approval that may be applied to a future read-only real-data
observation PR. PR #61 records the wording rules. PR #61 does **not**
record any actual approval.

## Required Approval Wording

The human reviewer must record the approval using this exact phrase,
and only this phrase, in the approving comment of the future
real-data observation PR:

> read-only real-data observation only

If the approving comment does not contain this exact phrase, the
future PR is treated as **not approved**, regardless of any other
text in the comment.

## Wording Discipline

- The phrase must appear verbatim. Reordering, paraphrasing,
  capitalization-only edits intended to be "equivalent", or
  translation are not accepted as the required wording.
- The phrase is the **only** wording that constitutes a valid
  approval for read-only observation.
- A future PR opening, a successful CI status, a passing review of
  unrelated content, or a casual comment containing "approve" or
  "looks good" do not constitute approval. Only the exact phrase,
  written by the human reviewer in the approving comment of the
  future real-data observation PR, constitutes approval.

## Forbidden Approval Wording

The following phrases (and any synonymous or paraphrased variant)
must **not** appear in any approval comment for any read-only
observation PR. If any of these phrases appears, the future PR is
treated as not approved, regardless of any other text:

- "trade allowed"
- "auto execution allowed"
- "order enabled"
- "signal enabled"
- "live trading enabled"
- "candidate scoring enabled"
- "broker connection enabled"
- "Kiwoom enabled"
- "real trading enabled"

## Scope Statements

Approval recorded with the required wording is, and is only, an
approval for read-only observation. In particular:

- A read-only observation approval is **not** an execution approval.
- A read-only observation approval is **not** a candidate-scoring
  approval.
- A read-only observation approval is **not** an order-preparation
  approval.
- A read-only observation approval is **not** an alerting approval.
- A read-only observation approval is **not** a broker / API /
  Kiwoom / WiseReport / Drive connection approval.
- A read-only observation approval is **not** transitive: it does
  not extend to a sibling repository, a different branch, or a
  different PR.

## Out of Scope for This PR

- PR #61 does not invoke this gate.
- PR #61 does not record any approval for any future PR.
- PR #61 does not begin observation.
- The actual approval, if it is ever given, is recorded in a private
  journal, not in this repository.
