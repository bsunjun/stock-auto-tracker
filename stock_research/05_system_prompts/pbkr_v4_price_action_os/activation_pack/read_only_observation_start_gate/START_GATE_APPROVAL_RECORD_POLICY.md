# Start-Gate Approval Record Policy

This document defines where an approval record may live, what wording
makes it valid, and what wording disqualifies it. PR #62 records the
policy. PR #62 does **not** record any actual approval, and does
**not** itself satisfy any approval requirement for any future PR.

## Storage Rule

- The actual filled-in approval record must live **only** in the
  operator's private journal. The private journal is not pushed to
  this repository.
- The actual approval record must **never** be committed to this
  repository, regardless of branch or PR scope.
- The approval record must contain **no** real ticker code, real
  listed-company name, real price, real news headline, real
  disclosure number, real flow figure, real order id, or real
  account number.

## Required Approval Phrase

The only wording that constitutes a valid start-gate approval is:

> read-only real-data observation only

The phrase must appear verbatim in the human operator's private
journal entry for the cycle being approved. Reordering, paraphrasing,
case-only edits intended as "equivalent", or translation are not
accepted.

## Forbidden Approval Phrases

If any of the following phrases (or any synonymous or paraphrased
variant) appears in the approval record, the start gate **fails** and
observation must not begin, regardless of any other text:

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

A valid start-gate approval is, and is only, an approval to begin a
single read-only observation cycle. In particular:

- It is **not** an execution approval.
- It is **not** a candidate-scoring approval.
- It is **not** an order-preparation approval.
- It is **not** an alerting approval.
- It is **not** a broker / API / Kiwoom / WiseReport / Drive
  connection approval.
- It does **not** roll forward to a later cycle. Each cycle must be
  approved on its own.

## Out of Scope for This PR

- The contents of any private-journal approval record.
- The actual repository state at the time of any future approval.
- Any record that ties an approval to a specific real ticker, real
  price, or real disclosure (such records are explicitly prohibited).
