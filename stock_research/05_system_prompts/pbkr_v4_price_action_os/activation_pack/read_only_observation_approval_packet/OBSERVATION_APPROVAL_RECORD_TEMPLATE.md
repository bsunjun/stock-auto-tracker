# Observation Approval Record Template

This file is a **template only**. It is not a record. It is not an
approval. It does not represent any decision. The actual approval
record, if it ever comes into existence, is written into the
operator's **private journal** — not into this repository — and is
gated by a separate future PR.

## Storage Rule

- The actual filled-in approval record must **never** be committed
  to this repository.
- The template below contains no real values, no real dates, no real
  identifiers, and no real approval text.

## Template Fields

The following fields describe the structure of an approval record.
The descriptions explain what each field is for. No example values
are provided.

- `approval_id`
  - A locally generated identifier used by the operator to refer to
    this approval cycle in the private journal. The form of the
    identifier is the operator's choice. It is not a broker-side
    identifier and never resembles one.
- `approval_date`
  - The date on which the human operator records the approval
    statement. Recorded in the private journal only.
- `repo_main_head`
  - The full commit SHA of `main` at the time the approval is
    recorded. Used for traceability of which repository state was in
    effect.
- `approval_phrase`
  - Must contain exactly the required wording defined in
    `APPROVAL_WORDING_REQUIREMENTS.md`. If it does not, the record
    is set to `NOT_APPROVED` regardless of any other field.
- `approval_scope`
  - A short statement that the approval applies only to read-only
    observation, and only to the cycle being recorded. The scope
    statement does not extend to execution, candidate scoring, order
    preparation, or alerting.
- `non_goals`
  - A short statement reaffirming what the approval is not for. At a
    minimum: not for execution, not for candidate scoring, not for
    order preparation, not for alerting, and not for connecting any
    broker / API / Kiwoom / WiseReport / Drive surface.
- `blockers_checked`
  - A confirmation that every blocker category in
    `OBSERVATION_START_BLOCKERS.md` has been individually inspected
    and cleared.
- `prohibited_fields_checked`
  - A confirmation that the prohibited-field categories from PR #59 /
    PR #60 have been read and that no prohibited content is being
    captured.
- `no_execution_guardrails_checked`
  - A confirmation that the no-execution guardrails from PR #60 are
    in force, and that no role has produced or is producing any
    execution artifact.
- `final_status`
  - One of:
    - `APPROVED_FOR_READ_ONLY_OBSERVATION`
    - `NOT_APPROVED`

## Status Semantics

- `APPROVED_FOR_READ_ONLY_OBSERVATION` is approval **only** for the
  read-only observation cycle being recorded. It is **not**
  execution permission. It is **not** candidate-scoring permission.
  It is **not** order-preparation permission.
- `NOT_APPROVED` is the default and applies whenever the approval
  phrase is missing, paraphrased, or accompanied by any forbidden
  approval wording.
- A status of `APPROVED_FOR_READ_ONLY_OBSERVATION` from a prior
  cycle does **not** roll forward to a later cycle. Each cycle must
  be approved on its own.

## Out of Scope for This PR

- Any actual filled-in template.
- Any real `approval_id` value.
- Any real `repo_main_head` value (the SHA of `main` at the moment a
  real cycle starts is recorded only in the private journal).
- Any real `approval_phrase` quotation tied to a real cycle.
- Any real cycle. PR #61 does not invoke any cycle.
