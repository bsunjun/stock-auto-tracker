# Observation Input Boundary Checklist

This document defines what may be considered as **input** during a
future read-only real-data observation cycle, and what must remain
**outside** the cycle. PR #62 records the boundary. PR #62 does
**not** ingest any input.

## Allowed (Labels Only)

The following are allowed as input descriptors. They are **labels
only**: classification slots, not raw real values. No raw values
appear in this PR.

- `source_tier` label — Tier 1 – Tier 5 classification per PR #59.
- `source_type` label — kind of source within a tier (for example,
  official filing vs. press item vs. soft signal).
- `disclosure_category` label — category of an official disclosure
  when applicable.
- `risk_flag_category` label — category of an official risk flag
  (for example, warning, designation, suspension, administrative
  issue).
- `estimate_revision_bucket` label — direction of consensus
  revision (for example, up, flat, down).
- `sector_group_label` — sector grouping descriptor.
- `chart_state_label` — chart-state classification descriptor.
- `volume_state_label` — volume-state classification descriptor.
- `supply_state_label` — supply-state classification descriptor.
- `human_review_required` — boolean indicator that the row demands
  human inspection.
- `observation_only` — boolean indicator that the row is for
  observation only and may not be used as input to any execution
  path.

## Prohibited (Raw Values)

The following are **never** valid input within a read-only
observation cycle, and must **never** appear in this repository:

- Raw real ticker code, in Korean six-digit form or any other form.
- Raw real price value (price, last, bid, ask, fill, etc.).
- Raw real order value (order id, order size, order side, order
  state).
- Raw real account value (account number, sub-account, balance,
  position).
- Raw news text — headline body, article body, attribution, byline.
- Raw disclosure number — DART acceptance number, KIND notice id,
  exchange notice id, or any equivalent.
- Raw paywalled-PDF text, in any volume, including snippets framed
  as quotes.
- Private Telegram screenshots, group-chat screenshots, or DM
  screenshots.
- Live broker response payload, raw or summarized.
- API token, API key, password, or session cookie of any kind.

## Statements

- Within a future read-only observation cycle, only **labels** may
  appear in any artifact reachable by the cycle. Raw values
  corresponding to those labels live, if anywhere, only inside the
  source the label is referencing. They are not extracted into a
  cycle artifact.
- The repository is the wrong place for any raw value. The private
  journal is the only place where any cycle output can live, and
  even there raw values from the prohibited list are not
  transcribed.
- A label by itself is not a candidate, not a recommendation, not a
  trade signal, and not an order ticket.

## Out of Scope for This PR

- Sample value data, even if labelled "synthetic". This PR contains
  none.
- Engine code that consumes any of the listed labels.
- Schema enforcement for any of the listed labels.
