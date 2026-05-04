# Observation Output Private Journal Policy

This document defines where read-only observation output is allowed
to live, what kinds of summary are acceptable in the private journal,
and what is forbidden everywhere. PR #62 records the policy. PR #62
does **not** produce any actual observation output.

## Storage Rule

- All actual read-only observation output lives in the operator's
  **private journal** only.
- The private journal is **not** committed to this repository, on
  any branch, in any form.
- This applies to summaries, notes, classifications, screenshots,
  exports, derived numbers, and any other artifact produced during
  a future cycle.

## Acceptable Private-Journal Summaries

Within the private journal, the following kinds of summary are
acceptable, provided they contain **no** raw values from the
prohibited list:

- `source_tier` classification summary — counts or notes about how
  many items fell into Tier 1 – Tier 5 during the cycle.
- Risk flag category summary — counts or notes about which risk flag
  categories were observed (warning, designation, suspension,
  administrative issue), without identifying instruments.
- Allowed / prohibited field audit summary — confirmation that only
  allowlisted labels were used and no prohibited categories were
  captured.
- Human review note — operator-written reflection on whether the
  cycle should continue, pause, or abort.

## Forbidden Everywhere

The following are forbidden everywhere — repository **and** private
journal — and must not be transcribed even in summary form:

- Raw ticker code.
- Raw price / volume / order-book value.
- Raw news headline.
- Raw disclosure number.
- Order intent — text or structure that could be interpreted as a
  decision to place a real order.
- Execution ticket — any artifact that resembles or could be
  promoted to a tradable order.
- Live broker response — raw or summarized.
- API token, API key, password, session cookie.
- Private Telegram screenshot, group-chat screenshot, or DM
  screenshot.
- Real chart screenshot tied to an identifiable instrument and
  timestamp.

## Status Semantics

- A successful read-only observation cycle, as recorded in the
  private journal, is **not** execution permission.
- A successful read-only observation cycle is **not** candidate
  scoring permission.
- A successful read-only observation cycle is **not** order
  preparation permission.
- A successful read-only observation cycle is **not** an alerting
  trigger.
- The status `APPROVED_FOR_READ_ONLY_OBSERVATION` (defined in PR
  #61's record template) governs only the cycle being recorded. It
  does not roll forward.

## Commit Posture

- The repository receives **zero** observation output.
- Any commit that would introduce observation output to this
  repository is treated as an `OBSERVATION_ABORT_CONDITIONS.md`
  trigger, and the cycle is aborted accordingly.

## Out of Scope for This PR

- The actual location of the operator's private journal.
- The format of any actual private-journal entry.
- Any actual journal contents.
