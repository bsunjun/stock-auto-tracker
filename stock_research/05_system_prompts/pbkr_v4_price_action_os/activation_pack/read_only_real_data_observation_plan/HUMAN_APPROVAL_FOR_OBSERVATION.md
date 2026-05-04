# Human Approval for Read-Only Real-Data Observation

This document defines the **mandatory human approval gate** for any
future read-only real-data observation stage. Merging PR #60 does
**not** satisfy this gate. Merging PR #60 only writes the gate down.

## Required Approval Wording

The human reviewer must record the approval using this exact phrase,
and only this phrase, in the approving comment of the future
real-data observation PR:

> read-only real-data observation only

If the approving comment does not contain this exact phrase, the
future PR is treated as not approved.

## Forbidden Approval Wording

The following phrases (and any synonymous variant) must **not**
appear in any approval comment for any real-data observation PR:

- "trade allowed"
- "auto execution allowed"
- "order enabled"
- "signal enabled"
- "live trading enabled"

If any forbidden phrase appears in the approving comment, the future
PR is treated as not approved, regardless of any other text.

## Pre-Conditions Checklist

All of the following must be true before the future PR may even
**propose** to begin real-data observation:

- [ ] PR #50 (Core Doctrine) is merged into `main`.
- [ ] PR #52 (Operating Package) is merged into `main`.
- [ ] PR #53 (Activation / Operator Runbook) is merged into `main`.
- [ ] PR #54 (Anonymized Dry-Run Fixtures) is merged into `main`.
- [ ] PR #55 (Non-Execution Fixture Validator) is merged into `main`.
- [ ] PR #56 (Dry-Run Report Template) is merged into `main`.
- [ ] PR #57 (First-Week Dry-Run Checklist) is merged into `main`.
- [ ] PR #58 (Second-Week Anonymized Candidate Extension) is merged
      into `main`.
- [ ] PR #59 (Real-Data Boundary Planning Checklist) is merged into
      `main`.
- [ ] PR #60 (this Read-Only Real-Data Observation Plan) is merged
      into `main`.
- [ ] No automated execution path exists in the repository. Confirmed
      by inspection.
- [ ] No broker / API / Kiwoom / WiseReport / Drive auto-connection
      exists in the repository. Confirmed by inspection.
- [ ] The prohibited-field policy in
      `REAL_DATA_REDACTION_AND_STORAGE_POLICY.md` has been read and
      acknowledged.
- [ ] The safe-storage rule (no real-data artifact committed to this
      repository) has been read and acknowledged.
- [ ] The no-execution guardrails in `NO_EXECUTION_GUARDRAILS.md`
      have been read and acknowledged.
- [ ] The observation output policy (private journal only, no repo
      commit) has been read and acknowledged.

## Without Approval

- Without the exact required wording, no real-data observation may
  begin.
- A successful PR #60 merge is **not** approval. PR #60 only writes
  the rules.
- A successful future-observation PR opening is **not** approval. The
  written approving comment with the exact required wording is what
  constitutes approval.

## Out of Scope for This PR

- PR #60 does not invoke this gate.
- PR #60 does not record any approval for any future PR.
- PR #60 does not begin observation.
