# Observation Note Shape Template (Private Journal Only)

This file describes the **shape** that an observation note may take
in the operator's private journal. The actual note instance lives
**only** in the private journal and is **never** committed to this
repository. PR #63 records the shape. PR #63 records no instance.

## Storage Rule

- Actual filled-in observation notes must **never** be committed to
  this repository, on any branch, in any form.
- The shape below contains **no** real values, **no** real dates, and
  **no** real identifiers.

## Allowed Sections (Labels Only)

Each of the following sections is a label or category slot. None
carries a raw value in this PR.

- `observation_id`
  - A locally generated identifier used by the operator to refer to a
    cycle in the private journal. The form is the operator's choice.
    It is not a broker-side identifier and must never resemble one.
- `observation_date`
  - The date on which the cycle was conducted. Recorded only in the
    private journal.
- `source_tier_label`
  - The Tier 1 – Tier 5 classification slot defined in PR #59. Label
    only. No raw source URL, no raw filename.
- `source_type_label`
  - Kind of source within the tier (for example, official filing,
    press item, soft signal). Label only.
- `official_risk_flag_category_label`
  - Category of an official risk flag, where applicable (for
    example, attention, warning, suspension, administrative issue).
    Label only. No raw notice id.
- `estimate_revision_bucket_label`
  - Direction of an estimate revision (for example, upward, neutral,
    downward, insufficient). Label only. No raw EPS / target price
    figures.
- `sector_group_label`
  - Sector grouping descriptor. Label only. No raw sector index
    value.
- `chart_state_label`
  - Chart-state classification slot (for example, constructive,
    neutral, weak, not_reviewed). Label only. No price values, no
    chart screenshots.
- `volume_state_label`
  - Volume-state classification slot. Label only. No raw volume
    figures, no average-volume comparison numbers.
- `supply_state_label`
  - Supply-state classification slot. Label only. No raw flow
    figures, no aggregated trade prints.
- `human_review_required`
  - Boolean indicator that a human reviewer must inspect the row.
    Boolean only.
- `observation_only`
  - Boolean indicator that the row is for observation only and may
    not be used as input to any execution path. Boolean only.
- `no_execution_statement`
  - A short reaffirmation that nothing in this note is intended to
    authorize, recommend, or prepare any order. The statement does
    not name an instrument and does not refer to a price.

## Forbidden Values (Hard List)

The following must **not** appear in any observation note, in this
repository **or** in the private journal:

- Actual ticker (Korean six-digit form or any other form).
- Actual price value (price, last, bid, ask, open, high, low,
  close, fill).
- Actual news headline, byline, body, or attribution.
- Actual disclosure number (DART acceptance number, KIND notice id,
  exchange notice id, or any equivalent).
- Actual volume / supply number.
- Actual order id, order side, order size, order state, fill price.
- Actual account number, sub-account, balance, position.
- Actual broker response payload, raw or summarized.
- API token, API key, password, session cookie.
- Real chart screenshot tied to an identifiable instrument and
  timestamp.
- Private Telegram screenshot, group-chat screenshot, or DM
  screenshot.

## Statements

- All values in any observation note are **labels** or **categories**.
- A label is not a candidate. A label is not a recommendation. A
  label is not a trade signal. A label is not an order ticket.
- The presence of a `no_execution_statement` line does **not** create
  any authorization. It restates an existing prohibition.

## Out of Scope for This PR

- Any actual filled-in observation note.
- Any operator-specific journal layout.
- Any automation that produces or consumes notes.
