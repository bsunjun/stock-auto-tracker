# Shadow Observation Plan (Forward-Looking, Not Activated by PR #59)

This document describes the **forward-looking design** of a possible
shadow observation stage that may follow the anonymized dry-run stage.
PR #59 does **not** start shadow observation. PR #59 does **not**
introduce real data. The shadow observation stage, if it ever begins,
must be opened in a separate PR (referenced for planning purposes only
as PR #60), and must satisfy the human approval gate defined in
`HUMAN_APPROVAL_GATE_FOR_REAL_DATA.md`.

## Stage Definition

Shadow observation is a stage in which:

- Real data, if any, is consumed in **read-only** mode.
- No order is placed, on any account, on any venue, by any process.
- No automated execution path is wired in any form.
- No automated alert is dispatched. Any notification produced is
  treated as an internal artifact and is reviewed by a human before any
  external communication.
- Output is written only to a private journal location or a dedicated
  safe artifact location governed by an explicit safe-artifact policy
  to be defined in the same future PR.

## Hard Constraints

- The shadow observation stage **must** start in a separate PR. It
  must not be inferred from the merge of PR #59.
- The shadow observation stage **must not** be enabled by environment
  variable, configuration toggle, or any side-channel switch in
  PR #59.
- The shadow observation stage **must not** add a broker client, an
  order-router, a webhook poster, or any auto-trigger.
- The first real-data PR (referred to here as PR #60 only for planning
  reference) **must** be read-only and **must not** execute.

## Output Handling (Future)

When the future PR introduces shadow observation, output handling
must, at minimum:

- Be written to a private journal or a dedicated safe artifact
  location with explicit access scope.
- Exclude every category listed in `REAL_DATA_PROHIBITED_FIELDS.md`.
- Honor the source tier rules in `REAL_DATA_SOURCE_TIERS.md`,
  including the Tier 1 hard veto and the Tier 5 single-source
  insufficiency rule.
- Be reviewed by a human before any downstream use beyond the journal.

## Boundary Statement

- PR #59 itself **does not start shadow observation**.
- PR #59 **does not** acquire, fetch, or store real data.
- PR #59 **does not** authorize an alert pipeline.
- PR #59 **does not** authorize execution of any kind, manual or
  automated.

## Out of Scope for This PR

- The actual safe-artifact policy.
- The actual private journal location.
- The actual integration with any data source.
- The actual content of any future real-data observation.
