# No-Real-Data Boundary

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Purpose

PBKR v4 explicitly separates the **dry-run domain** (synthetic,
anonymized, schema-validated, repo-committable) from the
**real-data domain** (anything else).

The first week after PR #56 merge is a dry-run-only period. This
document defines the boundary precisely so that no slip occurs by
accident.

---

## 2. Allowed in Dry-Run (Repository-Committable)

These shapes appear inside the committed fixtures and templates,
and the operator may use them freely during dry-run sessions:

| Category | Allowed values |
|---|---|
| Names | `Candidate A` / `Candidate B` / `Candidate C` only |
| Identifiers | `cand-A-anon` / `cand-B-anon` / `cand-C-anon` and derivatives (`fl-`, `tkt-`, `aud-`, `pu-`, `mb-`, `naj-`, `ng-`, `mc-`, `wl-` prefixes followed by anonymized substrings) |
| Dates | `2099-01-01` through `2099-01-06` (synthetic future dates) and similar `2099-…` patterns |
| Times | ISO-8601 `2099-…T…+09:00` |
| Trigger / failure / stop levels | text placeholders such as `anon-pivot-A`, `anon-failure-A`, `anon-stop-A`, `anon-stop-logic-A`, `anon-stop-plan-A` |
| Volatility / R / size summaries | text placeholders such as `anon-size-plan-A`, `anon-sell-plan-A`; numeric values **only** when explicitly part of the schema (`tor_pct`, `k`, `stop_distance_pct`, etc.) and synthetic by construction |
| Sources | `synthetic-tier1-disclosure`, `synthetic-tier2-ir-material`, `synthetic-tier3-broker-note`, `synthetic-tier4-newspaper`, `synthetic-tier5-unattributable-channel` |

These are the **only** data shapes that the repository accepts
during the first-week dry-run period (and indefinitely thereafter,
unless a future PR explicitly defines a new shape).

---

## 3. Forbidden in Dry-Run (Repository-Committable AND Private Journal)

The following are forbidden in **any** committed file and in the
operator's **private journal**:

- Real ticker symbols (e.g., the 6-digit KR equity code pattern
  `\b\d{6}\b`).
- Real company names.
- Real KR exchange codes (KOSPI / KOSDAQ / KONEX listings).
- Real DART filing numbers (`rcpNo`-like long numeric ids,
  `\b\d{14}\b` etc.).
- Real news headlines verbatim, including paywalled material.
- Real prices, quantities, fills, order ids, account numbers.
- Real chart images, real trading-platform screenshots, real PDF
  research reports.
- Real volume, real foreign-investor flow data, real intraday
  microstructure data.
- Real broker / brokerage names.
- API keys, OAuth tokens, bearer tokens, cookies, session ids,
  passwords, pass-phrases.
- Real URLs to brokerage portals, exchange portals, or any
  authenticated surface.

This list is non-exhaustive. The principle: if it could in any way
identify a real position, a real intent, or a real authenticated
context, it does not belong in the dry-run domain.

---

## 4. Boundary in Practice

### 4.1 In Committed Files

Enforced at multiple layers:

- The validator (`validate_fixtures.py`) detects 6-digit numeric
  patterns, 10+ digit patterns, URLs, brokerage / market-data /
  credential substrings, non-Candidate names, and non-`2099-` date
  prefixes inside `.fixture.json` files.
- Codex PR review enforces the same rules across `.md` files.
- Operator self-audit re-confirms before each commit.

### 4.2 In Private Journal

Enforced only by operator discipline. The private journal exists
outside the repository and is not subject to validator runs. The
operator therefore commits to the same anonymization rules
voluntarily and verifies them per
`PRIVATE_JOURNAL_GUIDE.md` §3.

### 4.3 In AI-Generated Drafts

When the operator uses
`activation_pack/dry_run_reports/DRY_RUN_REPORT_PROMPT_KO.md` to
ask Claude Code or GPT to draft a report, the prompt itself
forbids real-data leakage. The operator still reviews the AI
output line-by-line and discards any draft that crosses the
boundary.

---

## 5. Crossing the Boundary Requires a Separate PR

The dry-run domain cannot transition to the real-data domain
silently. Any attempt to:

- Commit a real ticker, real price, or real news headline.
- Connect an agent to a brokerage API or market-data feed.
- Capture a screenshot of a live chart for journaling.
- Set the `automatic_execution_allowed` flag truthy.
- Allow `operator_decision = "execute"` in any artifact.

…requires one of:

1. A separate, explicit PR with its own acceptance criteria, its
   own review gates, its own architectural justification, and an
   explicit human approval trail.
2. A doctrinal review-and-revise cycle that updates the existing
   PR #50 / #52 / #53 hard rules to remove the prohibition.

Neither path exists at the time of writing. The default during
the first-week dry-run period is: **stay inside the dry-run
boundary**.

---

## 6. Edge Cases

### 6.1 "But the validator just runs schema checks; can I drop a real ticker in temporarily?"

No. The validator's safety-leak audits would catch the 6-digit
ticker pattern and report `FAIL`. Even if it didn't, the boundary
is operational, not just technical. Putting a real ticker in a
fixture for "five minutes" is the kind of habit that produces
leaks.

### 6.2 "But the journal is private; can I write a real headline in it?"

Strongly discouraged. The private journal must remain free of
real data so it can serve as pattern memory without becoming an
operational risk. Use a synthetic re-statement of the news
("synthetic-tier4 commentary about Candidate B's group resolved
constructively") instead of the real headline.

### 6.3 "But I want to test how the system handles a real KR exchange designation."

Use `Candidate C` with `kr_designation_status: "investment_attention"`
in a synthetic fixture. The schema enum already lists every
designation; no real example is needed.

### 6.4 "But Codex / Claude already saw real data in another repo."

Out of scope. The PBKR v4 operating system enforces the boundary
**within this repository**. Other contexts the operator works in
are governed by their own rules.

---

## 7. Hard Bans (Apply to the Entire Operating System Indefinitely)

- No real ticker / company name / KR exchange code / DART filing
  number anywhere in committed files.
- No real price / quantity / order id / fill / news headline.
- No real screenshot / PDF / extracted text / output JSON / CSV.
- No API key / token / password.
- No automatic execution path connected.
- No safety flag flipped truthy.
- No `operator_decision = "execute"` in any artifact.
- No buy / sell recommendation wording in any language.
- No silent transition from dry-run to real-data mode.

---

## 8. Disclaimers

- This boundary document is part of the educational PBKR v4
  operating package.
- Nothing in it constitutes investment advice or a recommendation
  regarding any specific security.
- The operator is solely responsible for any decisions taken
  outside this repository, and for honoring the boundary in
  contexts the repository does not directly govern.
