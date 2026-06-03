# Google Drive Sync Note (Operational Mirror Only)

This document describes how the Risk-Flag Pullback Policy may be
mirrored to a Google Drive document for day-to-day operator
reference. The Drive copy is a **mirror only**. The repository
remains the **source of truth**. PR #64 does **not** create the
Drive document, does **not** wire any auto-sync, and does **not**
record any actual Drive link or file id.

## Mirror Document Title

A single Google Drive document may be created by the operator with
the title:

> PBKR v4 — Risk-Flag Pullback Policy

The title is illustrative; the operator chooses the final filename.
Any actual Drive URL or file id is **not** committed to this
repository, on any branch.

## Mirror Sections

When the operator creates the mirror, the following sections — in
this order — should be copied from the documents in this PR.
Section names are preserved so that auditing the mirror against the
repository is straightforward.

- Summary
- Risk Flag Taxonomy
- Risk-Flag Pullback Watch Checklist
- AI Role Updates
- Forbidden Interpretations
- 적용 예시 (illustrative interpretation only — see "Out of Scope"
  below)

The "적용 예시" section in the Drive mirror may contain
**illustrative wording only**. It must not contain real ticker
codes, real corporate names, real prices, real headlines, real
disclosure numbers, real flow figures, real orders, or real account
information.

## Source-of-Truth Statement

- The repository is the **source of truth**. If the Drive mirror
  drifts, the repository wins.
- Any change to the policy must originate in a repository PR. Drive
  edits that have not been mirrored back to a PR are **not
  authoritative**.
- The Drive mirror is read-only relative to the policy. It may
  carry operator working notes, but those notes are not part of the
  policy.

## Drive Storage Hard Rules

- No real Korean six-digit ticker codes in the Drive mirror.
- No real corporate names tied to a specific risk-flag situation in
  the Drive mirror.
- No real prices, real flow figures, or real disclosure numbers in
  the Drive mirror.
- No real account, order, fill, or broker response payloads in the
  Drive mirror.
- No API tokens, API keys, passwords, or session cookies in the
  Drive mirror.
- No private Telegram screenshots, group-chat screenshots, or
  paywalled-PDF text dumps in the Drive mirror.
- No automated execution path is wired between the Drive mirror and
  any system. The mirror is reference text, not a control surface.

## What This PR Does Not Do

- Does **not** open, create, or update any Google Drive document.
- Does **not** add any Drive URL or file id.
- Does **not** add any Drive auto-sync, OAuth client, service
  account, or webhook.
- Does **not** add any code that talks to Drive in any direction.
- Does **not** modify validators, fixtures, schemas, or engine
  code.

## Out of Scope

- The actual Drive URL and file id (operator-private; recorded only
  in the operator's private journal if at all).
- Any actual operator working notes inside the Drive mirror.
- Any automated mirroring tool.
- Any sample ticker, sample price, sample disclosure number, or
  sample chart screenshot inside the Drive mirror.
