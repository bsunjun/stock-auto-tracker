# Real-Data Redaction and Storage Policy

This document defines what is allowed to be **stored**, what must be
**redacted**, and what must be **discarded** if real data ever
appears during a future read-only observation stage. PR #60 records
the policy. PR #60 does **not** ingest real data.

## Repository Storage Rule

- Real data is **not** stored in this repository.
- Real ticker codes, real corporate names, real prices, real news
  bodies, real disclosure identifiers, real flow figures, real order
  identifiers, real account identifiers, and real broker responses
  are **never** committed to this repository.
- This applies to every branch, every PR, and every form of
  presentation, including snippets that are framed as examples.

## Private Journal Storage Rule

- Where a private journal is used, sensitive material is **minimized**
  even there.
- The journal is private to the operator and is not pushed to any
  remote tracked by this repository.
- Even in the private journal, the prohibited categories below should
  be avoided unless absolutely required for a corrective note.

## Prohibited Real-Data Categories

The following must not appear in this repository under any condition,
and must be minimized in any private journal:

- Real ticker code (Korean or otherwise).
- Real order id.
- Real fill price / executed price.
- Real account number, sub-account number, or account-identifying
  fragment.
- API token, API key, password.
- Session cookie or any authenticated session material.
- Live broker response payload, raw or summarized.
- Raw paywalled-PDF text dumps.
- Private Telegram screenshots, group-chat screenshots, or DM
  screenshots.
- Real chart screenshots tied to specific tickers and timestamps.

## Leak Handling

If real data nonetheless leaks into a working artifact during a
future observation cycle:

- The artifact is **scrubbed** and may not be reused. Reuse is
  prohibited because incidental traces may remain.
- The leaked artifact is **discarded**.
- Only a **corrective note** is recorded, in the private journal,
  describing what category of data was seen and what corrective step
  was taken. The leaked content itself is not transcribed into the
  note.
- The corrective note is **not** committed to this repository.
- If the leak has already entered git history at any point, the
  situation is treated as a security incident: the affected branch
  stops accepting commits until the history is cleaned, and the
  prohibited content is purged from all reachable refs.

## Out of Scope for This PR

- Concrete tooling for scrubbing.
- Concrete tooling for journal storage.
- Any sample of redacted output.
- Any sample of real material in any form.
