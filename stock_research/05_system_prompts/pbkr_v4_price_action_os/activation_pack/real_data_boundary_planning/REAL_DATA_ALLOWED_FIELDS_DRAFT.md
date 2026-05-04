# Real-Data Allowed Fields (Draft, Names Only)

This document is a **draft list of field names** that may be considered
acceptable for a future read-only real-data shadow observation stage.
This PR does **not** populate any of these fields. No values are
introduced. No sample ticker, no sample price, no sample disclosure
identifier is provided. Placeholders that resemble real codes (for
example, six-digit Korean ticker codes) are also prohibited in this PR.

## Field Names (Names Only)

The following identifiers are documented as candidate **field names**
only. Their actual values, value types beyond a brief notional
description, and value sources are out of scope for PR #59.

- `ticker`
- `name`
- `market`
- `source_tier`
- `source_type`
- `event_date`
- `disclosure_type`
- `risk_flag_type`
- `estimate_revision_bucket`
- `sector_group`
- `chart_state_label`
- `supply_state_label`
- `human_review_required`

## Notional Descriptions (No Values)

- `ticker`: identifier slot for a listed instrument. Not populated in
  this PR. No real or real-looking codes are provided.
- `name`: human-readable label slot. Not populated in this PR.
- `market`: classification slot for the listing venue. Not populated.
- `source_tier`: classification slot referencing
  `REAL_DATA_SOURCE_TIERS.md` (Tier 1 – Tier 5). Not populated.
- `source_type`: classification slot for the kind of source within the
  tier (for example, official filing vs. press vs. soft signal). Not
  populated.
- `event_date`: slot for the date associated with an observed event.
  Not populated.
- `disclosure_type`: classification slot for the kind of official
  disclosure (Tier 1) when applicable. Not populated.
- `risk_flag_type`: classification slot for risk flag categories such as
  warning, designation, suspension, administrative-issue status. Not
  populated.
- `estimate_revision_bucket`: classification slot for direction of
  consensus revision (for example, up, flat, down). Not populated.
- `sector_group`: classification slot for sector grouping. Not
  populated.
- `chart_state_label`: classification slot for chart-state category.
  Not populated. No price values, no chart screenshots.
- `supply_state_label`: classification slot for supply-state category.
  Not populated. No flow values, no aggregated trade prints.
- `human_review_required`: boolean slot indicating that a human reviewer
  must inspect the row before it can be used as supporting context.
  Not populated.

## Hard Constraints for This PR

- No real values are introduced for any field.
- No sample ticker codes, including dummy six-digit numeric strings, are
  introduced.
- No real names of listed companies are introduced.
- No price, no volume, no flow, no order, no fill, no account number is
  introduced.
- Placeholders that look like real codes are not allowed. If an example
  is needed in future documentation, it must be obviously synthetic and
  must not collide with any real Korean listing code format.

## Future Use

These field names are documentation-only seeds for the eventual
real-data shadow observation stage, which itself requires its own PR
and explicit human approval per
`HUMAN_APPROVAL_GATE_FOR_REAL_DATA.md`.
