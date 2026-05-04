# Real-Data Field Allowlist Policy (Names Only)

This document declares the **field allowlist** that may apply to a
future read-only real-data observation stage. PR #60 lists field
**names** only. No values are introduced. No real ticker code, no
real listed-company name, no real price, no real news headline, no
real disclosure number, no real flow figure, no real order id, no
real account number is provided.

## Policy

- Only field names appear in this document.
- Real values are not introduced anywhere in this PR.
- Sample values that resemble real material are also prohibited.
- Examples that look like real Korean six-digit ticker codes are
  prohibited.
- Real corporate names, real article titles, and real price examples
  are prohibited.
- Field value entry, if it ever happens, must occur in a separate
  future PR governed by its own approval gate.

## Allowlisted Field Names

The following identifiers are documented as candidate **field names**
for a future read-only observation stage. Their actual values, value
formats, and value sources are out of scope for PR #60.

- `source_tier`
- `source_type`
- `source_timestamp`
- `disclosure_category`
- `official_risk_flag_type`
- `estimate_revision_bucket`
- `sector_group_label`
- `chart_state_label`
- `volume_state_label`
- `supply_state_label`
- `human_review_required`
- `observation_only`

## Notional Descriptions (No Values)

- `source_tier`: classification slot referencing the Tier 1 – Tier 5
  taxonomy defined in PR #59. Not populated in this PR.
- `source_type`: classification slot for the kind of source within a
  tier (for example, official filing vs. press item vs. soft signal).
  Not populated.
- `source_timestamp`: slot for the timestamp at which the material
  was observed. Not populated. No real timestamp is recorded.
- `disclosure_category`: classification slot for the category of an
  official disclosure (Tier 1) when applicable. Not populated.
- `official_risk_flag_type`: classification slot for the category of
  an official risk flag, such as warning, designation, suspension, or
  administrative-issue status. Not populated.
- `estimate_revision_bucket`: classification slot for the direction
  of an estimate revision (for example, up, flat, down). Not
  populated.
- `sector_group_label`: classification slot for sector grouping. Not
  populated.
- `chart_state_label`: classification slot for chart-state category.
  Not populated. No price values, no chart screenshots.
- `volume_state_label`: classification slot for volume-state
  category. Not populated. No real volume figures.
- `supply_state_label`: classification slot for supply-state
  category. Not populated. No flow values, no aggregated trade
  prints.
- `human_review_required`: boolean slot indicating that a human
  reviewer must inspect the row before it can be considered. Not
  populated.
- `observation_only`: boolean slot indicating that the row is for
  observation only and may not be used as input to any execution
  path. Not populated.

## Hard Constraints for This PR

- No real value is introduced for any field listed above.
- No example value is introduced for any field listed above.
- No real ticker code, no dummy six-digit numeric string, and no
  real-looking placeholder is introduced.
- No real corporate name is introduced.
- No real article title, no real disclosure number, no real price,
  and no real flow figure is introduced.
- A future PR that introduces values for any of these fields must
  satisfy the approval gate in
  `HUMAN_APPROVAL_FOR_OBSERVATION.md` and the storage rules in
  `REAL_DATA_REDACTION_AND_STORAGE_POLICY.md`.

## Out of Scope for This PR

- Field schemas.
- Field value validation logic.
- Engine code that consumes any of the listed fields.
- Any actual observation output.
