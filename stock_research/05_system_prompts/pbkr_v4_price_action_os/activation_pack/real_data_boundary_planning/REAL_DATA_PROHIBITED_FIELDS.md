# Real-Data Prohibited Fields

This document defines the categories of real-data content that **must
never be committed** to the PBKR v4 documentation repository. The
prohibition applies to PR #59 and to every subsequent PR, including any
future real-data shadow observation PR.

## Absolutely Prohibited Categories

The following must not be committed to this repository under any
circumstance:

- **Account number** — brokerage account number, sub-account number, or
  any partial form sufficient to identify a real account.
- **Order id** — broker-side order identifier in any form.
- **Fill price** — real executed price, including post-trade
  confirmations and any reconstructed fill price.
- **Live broker response** — raw or summarized response payload from a
  real broker API or trading terminal.
- **API token / API key / password** — credentials of any kind for any
  data provider, broker, exchange, mail server, messaging service, or
  storage backend.
- **Session cookie** — authenticated session material from any web
  service.
- **Real chart screenshot** — screenshots of real, identifiable chart
  windows tied to specific tickers and timestamps.
- **Paywalled PDF raw text** — raw text dumps from paywalled research
  PDFs (broker reports, paid databases, etc.).
- **Actual private Telegram screenshot** — screenshots of private
  Telegram channels, group chats, or DMs.
- **Unredacted account / position snapshot** — any holdings, balance,
  or P&L view that includes real values, real positions, or real
  account identifiers.
- **Actual execution intent** — any message or document that states or
  implies a real, immediate intent to place a real order on a real
  account.

## Hard Statement

Real order information, real execution information, and real account
information must **never** be committed to the PBKR v4 documentation
repository. This applies regardless of branch, regardless of PR scope,
and regardless of whether the content is presented as an example.

## Handling If Encountered

If any of the above categories appears in a draft, the draft must be
purged and rewritten with synthetic, anonymized, clearly non-real
material. If such content has already entered git history, treat it as
a security incident and stop further commits to the affected branch
until the history is cleaned.

## Out of Scope for This PR

- This document does **not** authorize collecting, processing, or
  storing any of the prohibited categories elsewhere.
- This document does **not** create any execution path.
- This document does **not** reduce the prohibitions established in
  PR #50 – PR #58.
