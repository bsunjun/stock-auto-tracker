# Pre-Observation Operator Checklist

This checklist must be completed by the human operator **before** any
read-only real-data observation is started. PR #61 records the
checklist. PR #61 does **not** invoke it. The actual checklist run,
if it ever occurs, takes place outside this repository (in a private
journal) and is gated by a separate future PR.

## Hard Rule

- If **any** item below is unchecked, observation must **not** start.
- An item that the operator cannot personally verify is treated as
  unchecked.

## Repository State

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
- [ ] PR #60 (Read-Only Real-Data Observation Plan) is merged into
      `main`.
- [ ] PR #61 (this Approval Packet) is merged into `main`.

## Policy Acknowledgement

- [ ] PR #60 read-only observation plan has been read.
- [ ] The real-data field allowlist policy
      (`REAL_DATA_FIELD_ALLOWLIST_POLICY.md`) has been read.
- [ ] The prohibited field policy (the prohibited categories defined
      in PR #59 / PR #60) has been read.
- [ ] The redaction and storage policy
      (`REAL_DATA_REDACTION_AND_STORAGE_POLICY.md`) has been read.
- [ ] The no-execution guardrails (`NO_EXECUTION_GUARDRAILS.md`)
      have been read.
- [ ] The private journal storage policy has been read. Observation
      output is journal-only and is not committed to this
      repository.

## Connection State (Must All Be "None")

- [ ] No broker connection (live or sandbox) is wired.
- [ ] No external trading API connection is wired.
- [ ] No Kiwoom (or equivalent retail-broker) order path is wired.
- [ ] No webhook that emits an alert outside the operator's private
      journal is wired.
- [ ] No automated notification (email, SMS, push, mobile,
      messaging) is wired.
- [ ] No WiseReport feed is wired.
- [ ] No Drive auto-sync is wired.

## Output Posture

- [ ] No real observation output is to be committed to this
      repository.
- [ ] No real candidate artifact is to be committed.
- [ ] No real validator output is to be committed.
- [ ] No real approval record is to be committed (records stay in
      the private journal).

## Approval Wording

- [ ] The required approval wording in
      `APPROVAL_WORDING_REQUIREMENTS.md` is understood. The exact
      phrase is the only valid wording.
- [ ] The forbidden approval wording list in
      `APPROVAL_WORDING_REQUIREMENTS.md` is understood. None of
      those phrases will be used in any approval comment.

## If Any Item Is Unchecked

- Observation must not start.
- A note describing what was missing may be recorded in the private
  journal.
- Such a note is **not** committed to this repository.
- Re-attempting observation requires re-running the entire checklist.
