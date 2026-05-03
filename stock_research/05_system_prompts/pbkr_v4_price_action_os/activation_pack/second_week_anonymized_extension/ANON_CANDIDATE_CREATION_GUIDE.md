# Anonymized Candidate Creation Guide

This guide defines the rules for creating **new** anonymized candidates
during the second-week extension. It applies only to fixtures the
operator constructs locally for training; it does **not** modify any
fixture committed to this repo.

## 1. Allowed identifiers

### Display names
- `Candidate X`
- `Candidate Y`
- `Candidate Z`

No other display names are allowed. Do not invent names that look like
real tickers, real companies, or real sectors.

### Candidate IDs
- `cand-X-anon`
- `cand-Y-anon`
- `cand-Z-anon`

### Allowed value tags
- `anon-pivot-X`, `anon-pivot-Y`, `anon-pivot-Z`
- `anon-stop-X`, `anon-stop-Y`, `anon-stop-Z`
- `anon-failure-X`, `anon-failure-Y`, `anon-failure-Z`
- `synthetic-tier1-disclosure`
- `synthetic-tier3-report`
- `synthetic-tier5-unattributable-channel`
- Any date string must use the `2099-` prefix
  (e.g., `2099-01-15`, `2099-03-04`).

These tags are **opaque labels**. They must not be replaced with real
numeric prices, real disclosure numbers, or real timestamps.

## 2. Forbidden content

The following must **never** appear in a generated candidate:

- Real ticker names (Korean or otherwise).
- Real ticker / ISIN / KRX codes.
- Real prices, real bid/ask, real volume, real turnover.
- Real OHLCV bars from any data vendor.
- Real news headlines, real article URLs, real source names.
- Real disclosure (공시) numbers, real DART filing IDs, real filing
  timestamps.
- Real net-buy / net-sell flow numbers (수급).
- Real account IDs, real broker IDs, real order IDs.
- API keys, tokens, passwords, or any credential material.

If a generated candidate contains any of the above, it must be
discarded — not "scrubbed and reused".

## 3. Required structure for every generated candidate

Every candidate the operator builds in the second week must include
**all** of the following sections. Missing sections invalidate the
exercise even if `validate_fixtures.py` returns `PASS`.

- `setup` — anonymized description of the chart / context setup.
- `edge` — why the operator believes this setup has a defined edge,
  in anonymized terms only.
- `entry_tactic` — how an entry would be sequenced, expressed via
  `anon-pivot-*` tags.
- `trigger_level` — the anonymized trigger reference
  (`anon-pivot-X` / `Y` / `Z`).
- `failure_level` — the anonymized invalidation reference
  (`anon-failure-X` / `Y` / `Z`).
- `stop_logic` — written description of how the stop is decided.
- `stop_level` — the anonymized stop reference
  (`anon-stop-X` / `Y` / `Z`).
- `sell_rules` — anonymized exit / scale-out logic.
- `human_gate` — explicit statement that a human operator decision
  is required before any action; must not be auto-satisfied.
- `signal_safety` — explicit statement that this candidate is a
  training artifact, that PASS is not execution permission, and that
  no automatic execution is authorized.

## 4. Workflow

1. Operator drafts a candidate locally (outside the repo working
   tree, e.g., in a private scratch directory).
2. Operator runs `validate_fixtures.py` against a **local** copy
   placed in a throwaway path. The committed fixtures S1–S6 must not
   be edited or replaced.
3. Operator reviews the result in their private journal.
4. Operator deletes the local artifact at end-of-day. Nothing is
   committed.

## 5. What `PASS` means and does not mean

- `PASS` means the JSON conforms to the validator's schema and
  rule set.
- `PASS` does **not** mean buy. It does **not** mean sell. It does
  **not** authorize any order, any alert delivery, or any automated
  pipeline.
- The human gate remains the only path to action, and action remains
  out of scope for this PR.
