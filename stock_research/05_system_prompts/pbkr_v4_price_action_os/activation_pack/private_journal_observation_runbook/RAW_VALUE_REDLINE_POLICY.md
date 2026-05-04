# Raw Value Redline Policy

This document defines the **redline** between labels (always allowed
inside an observation note's shape) and raw values (never allowed).
The policy applies to this repository **and** to the operator's
private journal. PR #63 records the policy. PR #63 does **not**
ingest any raw value.

## Redline Statement

A **raw value** is any data item that, by itself, identifies a real
instrument, a real price, a real account, a real disclosure
identifier, a real news body, a real flow figure, a real order, or a
real authentication credential. Raw values must **never** be
captured, transcribed, summarized at numeric resolution, screenshot,
quoted, or alluded to with a degree of specificity that re-identifies
them.

## Categories Subject to the Redline

The following are subject to the redline. Each category must
**never** appear in this repository and must **never** be captured
into the private journal. If a category does enter a working
artifact, the redline behavior in the next section applies:

- Actual ticker code (Korean six-digit form or any other form).
- Actual price (last, bid, ask, open, high, low, close, fill).
- Actual news headline, body text, byline, or attribution.
- Actual disclosure number (DART acceptance, KIND notice, exchange
  notice, or equivalent).
- Actual flow / supply numeric figures.
- Actual account / order / fill / broker information of any kind.
- API key, API token, password, session cookie.
- Live broker response payload, raw or summarized.
- Raw paywalled-PDF text dumps.
- Real chart screenshots tied to identifiable instruments and
  timestamps.
- Telegram screenshots, group-chat screenshots, or other private-chat
  captures.

## Redline Behavior

If a raw value enters a working artifact during a future cycle, the
operator must:

1. **Stop transcribing immediately.** No further values are added.
2. **Discard the artifact.** The artifact may not be reused, even
   after a "scrub", because incidental traces may remain.
3. **Do not commit.** The artifact is not committed to this
   repository, on any branch, regardless of the apparent
   sensitivity of the trace.
4. **Record only a minimal note.** A short line such as "redline
   breached, discarded" is acceptable in the private journal. The
   offending content itself is not transcribed into the note.
5. **Block further observation.** No further observation is
   conducted in the same session. A new cycle, if proposed, must
   re-run the start gate (PR #62) and the Day 0 precheck.

## Statements

- The redline is **stricter than a "scrub"**. A scrubbed artifact
  is still treated as compromised and is discarded, not reused.
- The redline applies regardless of intent. Accidental ingestion is
  treated identically to deliberate ingestion for the purposes of
  artifact handling.
- The redline applies regardless of the apparent triviality of the
  value. A single ticker code, a single price, a single disclosure
  number is sufficient to require artifact discard.

## Out of Scope for This PR

- Implementing automated detection of redline values.
- Wiring any pre-commit hook or runtime check.
- Any sample of redlined content. None is reproduced in this
  document.
