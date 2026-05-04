# Human Approval Gate for Real-Data Stage

This document defines the **mandatory human approval checklist** that
must be completed before any PR is opened that introduces real data of
any kind into the PBKR v4 documentation repository. Merging PR #59
does **not** satisfy this gate. Merging PR #59 only documents the
gate.

## Pre-Conditions Checklist

All of the following must be true before any real-data PR may be
opened:

- [ ] PR #50 (Core Doctrine) is merged into `main`.
- [ ] PR #51 is merged into `main` (where applicable in this sequence).
- [ ] PR #52 (Operating Package) is merged into `main`.
- [ ] PR #53 (Activation / Operator Runbook) is merged into `main`.
- [ ] PR #54 (Anonymized Dry-Run Fixtures) is merged into `main`.
- [ ] PR #55 (Non-Execution Fixture Validator) is merged into `main`.
- [ ] PR #56 (Dry-Run Report Template) is merged into `main`.
- [ ] PR #57 (First-Week Dry-Run Checklist) is merged into `main`.
- [ ] PR #58 (Second-Week Anonymized Candidate Extension) is merged
      into `main`.
- [ ] PR #59 (Real-Data Boundary Planning Checklist, this PR) is
      merged into `main`.
- [ ] Dry-run record for the anonymized stage has been completed and
      filed under the dry-run report path established in PR #56.
- [ ] The non-execution fixture validator from PR #55 reports PASS on
      the anonymized fixtures committed up through PR #58.
- [ ] The real-data source tier definitions from
      `REAL_DATA_SOURCE_TIERS.md` have been read and acknowledged by
      the human reviewer.
- [ ] The real-data prohibited fields list from
      `REAL_DATA_PROHIBITED_FIELDS.md` has been read and acknowledged
      by the human reviewer.
- [ ] No automated execution path exists in the repository. Confirmed
      by inspection.
- [ ] No broker connection, no broker API client, no order-routing
      module, and no live trading credential exists in the repository.
      Confirmed by inspection.
- [ ] The first real-data PR will be **read-only** with **no
      execution**, scoped strictly to observation.

## Required Approval Wording

The human reviewer must record the approval using this exact phrase,
and only this phrase, in the approving comment of the future real-data
PR:

> read-only real-data observation only

## Forbidden Approval Wording

The following phrases (or any synonymous variant) must **not** appear
in any approval comment for any real-data PR:

- "trade allowed"
- "auto execution allowed"
- "order enabled"

If any forbidden phrase appears, the future real-data PR must be
treated as not approved, regardless of any other text in the comment.

## Scope of This Gate

- This gate governs the entry into any real-data stage.
- This gate does **not** authorize execution.
- This gate does **not** authorize automatic alerts dispatched without
  human review.
- This gate does **not** authorize storing prohibited categories from
  `REAL_DATA_PROHIBITED_FIELDS.md`.

## Out of Scope for This PR

- PR #59 does not invoke this gate. PR #59 only writes it down.
- PR #59 does not add any approval record for any future real-data PR.
