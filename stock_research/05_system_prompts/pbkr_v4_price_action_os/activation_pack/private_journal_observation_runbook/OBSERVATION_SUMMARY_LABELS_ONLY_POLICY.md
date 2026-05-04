# Observation Summary — Labels Only Policy

This document defines the **labels-only policy** that governs every
summary produced during a future read-only real-data observation
cycle. PR #63 records the policy. PR #63 produces no actual summary.

## Core Statement

An observation summary is a **labels-only** artifact. It contains
classification labels and category labels — it does not contain raw
ticker codes, raw prices, raw news headlines, raw disclosure
numbers, raw flow figures, or any other raw value covered by the
redline policy.

## Allowed Label Domains

The following are the label domains that may appear in a summary.
Each label is a category — never a raw value.

- `source_tier`
  - `tier_1_official`
  - `tier_2_report`
  - `tier_3_press`
  - `tier_4_public_signal`
  - `tier_5_unverified`
- `risk_flag_category`
  - `none`
  - `official_attention`
  - `official_warning`
  - `trading_halt`
  - `management_issue`
- `estimate_revision_bucket`
  - `upward`
  - `neutral`
  - `downward`
  - `insufficient`
- `chart_state_label`
  - `constructive`
  - `neutral`
  - `weak`
  - `not_reviewed`
- `supply_state_label`
  - `supportive`
  - `neutral`
  - `adverse`
  - `not_reviewed`

The label values above are illustrative category names, not actual
observed cycle outputs. PR #63 does not bind any label to any real
instrument or any real cycle.

## Forbidden in Any Summary

The summary must **never** include:

- Actual ticker code, in any format.
- Actual price, volume, or order-book figure.
- Actual news headline, body text, byline, or attribution.
- Actual disclosure number.
- Actual flow / supply numeric figure.
- Actual order id, account number, or broker response payload.
- API token, API key, password, or session cookie.
- Real chart screenshots or paywalled-PDF text.

## Statements

- A labels-only summary is **not** a trade signal.
- A labels-only summary is **not** candidate scoring.
- A labels-only summary is **not** order preparation.
- A labels-only summary is **not** an alerting trigger.
- A labels-only summary is **not** an authorization to act.
- A labels-only summary lives in the private journal only.

## Out of Scope for This PR

- Implementing automated label-only enforcement.
- Wiring any schema or runtime check.
- Any sample summary content — none is reproduced here.
