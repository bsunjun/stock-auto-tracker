# Real-Data Source Tiers (Definition Only)

This document defines the **tier classification** for real-data sources
that may be considered in a future read-only observation stage. It does
**not** introduce any actual data, ticker, value, or candidate. It is
not a trading signal of any kind. Tier classification governs only the
question of "is this source usable as supporting context", never the
question of "should an order be placed".

## Tier 1 — Official / Regulatory

- DART (Korean corporate disclosure system) original filings.
- KIND / KRX official notices: investment warning (투자경고),
  designation (지정), trading suspension (거래정지), administrative
  issue / management stock (관리종목) status.
- The listed company's own official disclosures.
- The exchange's own official information channels.

Properties:

- Highest confidence with respect to fact-of-event.
- Required as a primary reference where available.
- Tier 1 official negative events (for example, formal warning,
  designation, suspension, or administrative-issue status) function as a
  **hard veto** on candidate consideration.

## Tier 2 — Sell-Side Research and Consensus

- Issuer (company) IR materials.
- Brokerage research reports.
- WiseReport-style aggregated research extracts.
- FnGuide consensus data.

Properties:

- Useful for estimate-revision direction and analyst stance context.
- Not a substitute for Tier 1 on factual events.
- May be referenced in shadow observation only as context, not as an
  instruction.

## Tier 3 — Major Press

- Major economic newspapers.
- Major industry-focused press outlets.

Properties:

- Useful for narrative and theme context.
- Subject to redaction rules and copyright handling.
- Cannot, on its own, override Tier 1 facts.

## Tier 4 — Public Soft Signal

- Public search trend information.
- Blog posts.
- Open community-style public information.

Properties:

- May indicate attention level only.
- Cannot independently support a candidate decision.
- Subject to noise and manipulation risk.

## Tier 5 — Unverified / Closed-Channel

- Telegram messages.
- Group chat (단톡방) content.
- Summaries from unidentified or undisclosed sources.

Properties:

- **Tier 5 alone is never sufficient to promote a candidate.** A
  candidate that has only Tier 5 support must not be promoted.
- May be logged for traceability of where a name first appeared, but
  not as evidence supporting action.

## Cross-Tier Rules

- A Tier 1 official negative event acts as a hard veto regardless of
  what Tier 2 – Tier 5 say.
- Tier 5 alone is not sufficient evidence for any candidate promotion.
- Source tier definitions in this document are **not** trade signals.
  They are classification rules used for evidence weighting in a future
  read-only observation stage.
- This file does not specify any actual ticker, price, news item, or
  disclosure.

## Out of Scope for This PR

- Actual data fetched from any of the above sources.
- Any ranking, scoring, or candidate output.
- Any execution, order placement, or alert dispatch logic.
