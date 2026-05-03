# Dry-Run Protocol (Anonymized)

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.
>
> **Dry-run results are not committed. Dry-run is operational
> verification, not a transaction recommendation.**

---

## 0. Purpose

Validate the operating-package flow end-to-end **without** real
tickers, real prices, real orders, real quantities, or any real
market data. The dry-run confirms:

- The schemas link cleanly across the handoff chain.
- Each role refuses input that would violate its boundaries.
- The hard veto trips when expected.
- The human gate denies / passes correctly.
- The no-action journal can be filled when the day produces nothing.

---

## 1. Naming Conventions

Use only these placeholder identifiers:

- **Candidate A** — anonymized identifier `cand-A-anon`.
- **Candidate B** — `cand-B-anon`.
- **Candidate C** — `cand-C-anon`.

Forbidden in dry-run artifacts:

- Any real ticker symbol or company name.
- Any real price level, quantity, or notional value.
- Any real order placeholder.
- Any real KR exchange code (e.g., 005930-style codes).

If you find yourself reaching for a real name, stop the dry-run and
restart with anonymized labels.

---

## 2. Dry-Run Scenarios (Recommended Sequence)

### 2.1 Scenario S1 — Clean Pass

**Goal:** verify a clean entry advances all the way to a human-gate
`pass`.

- News pack (Gemini): one Tier-1 official disclosure for Candidate A;
  Tier-3 secondary commentary; no Tier-5-only items.
- Focus list (Orchestrator): A as `swing` trade-class with
  `BaseBreakout` setup and `ConsolidationPivotBreakout` tactic.
- Audit (Auditor): `pass` with a specific counter-thesis (e.g.,
  "leadership group thinning relative to last week").
- Gate (Verifier): all checklist items pass.
- Journal: ticket logged with `operator_decision = pending` (no
  actual transaction in dry-run).

Expected outcome: end-to-end artifacts validate against schemas;
human gate produces `pass`.

### 2.2 Scenario S2 — Hard Veto

**Goal:** verify the auditor blocks correctly.

- Focus list: candidate B with `entry_tactic` missing
  `failure_level`.
- Audit: `block`, finding `A001` (entry_tactic missing fields).
- Downstream: gate verifier refuses to evaluate; operator records
  the rejection.

Expected outcome: chain stops at audit; no ticket reaches the gate.

### 2.3 Scenario S3 — Telegram-Only Evidence

**Goal:** verify Tier-5-only candidates are demoted.

- News pack: candidate C cited only by Tier-5 (Telegram channel).
- Focus list (Orchestrator): if Orchestrator nonetheless promotes,
  Auditor returns `block` finding `A204` (Tier-5-only sourcing for
  leader / position class) and `A301` if any urgency wording was
  produced.
- If Orchestrator correctly drops C upstream, the chain ends at
  focus-list construction.

Expected outcome: C never enters the snipe queue; reason captured
in journal.

### 2.4 Scenario S4 — TOR Saturation

**Goal:** verify TOR headroom enforcement.

- TOR state: `tor_pct` already near `K * tor_ceiling_pct`.
- Focus list: A and B both pass tactic-level checks.
- Audit: `revise_required` for the lower-priority entry due to TOR
  breach (`A102`).
- Operator: focus list compresses to one entry.

Expected outcome: TOR ceiling is honored mechanically.

### 2.5 Scenario S5 — Gate Deny

**Goal:** verify the gate denies when a checklist item is missing.

- Ticket: missing `time_stop_window_sessions`.
- Gate verifier: `deny`, `unchecked_items: ["sell_rules.time_stop_window_sessions"]`.
- Operator: does not transact; logs `gate_deny` in journal.

Expected outcome: missing item flagged; no transaction.

### 2.6 Scenario S6 — No-Action Day

**Goal:** verify the no-action journal flow when the focus list is
empty.

- Pre-open: market regime classifies `stage_4`; `K = 0.10`.
- Focus list: empty.
- Operator: fills `../ticket_templates/no_action_journal_template.md`
  with reason `regime_defensive`.

Expected outcome: empty focus list is a valid daily outcome; cash
is the prescribed posture.

---

## 3. Dry-Run Artifacts

For each scenario, the operator constructs minimal in-memory or
local-only artifacts:

- News pack draft.
- Focus list draft.
- Audit pack.
- Gate-result block.
- Ticket (with `operator_decision = pending`).
- Journal entry (no-action / pending / dry-run-tagged).

These artifacts are **operational test inputs**. They are **not
committed to the repository**. The operator may store them in a
local scratch directory; that path is not under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/`.

---

## 4. Pass / Fail Criteria for the Dry-Run

A dry-run **passes** when:

- All scenarios produce expected outcomes.
- All schemas validate.
- All four safety flags remain at `false / null|false / false / true`
  in every artifact produced.
- No real ticker / price / quantity / order leaked into any
  artifact.
- Each role refused inputs that would violate its boundaries.

A dry-run **fails** if any of the above is not true. Failure means
the operating system is not ready to process real candidates. The
operator does **not** activate.

---

## 5. Frequency

- **First week after PR #53 is merged:** dry-run only. No real
  candidates processed.
- **Thereafter:** rerun the dry-run on any of the following
  occurrences:
  - Any PR that touches files under
    `stock_research/05_system_prompts/pbkr_v4_price_action_os/`.
  - Any change in the operator's AI service stack (e.g., model
    version upgrade).
  - Any postmortem flagged with `signal_leak`, `gate_override`, or
    `audit_override` in the prior week.

---

## 6. Hard Bans (Apply Always)

- No real ticker, real order, real recommendation phrase.
- No screenshots of real charts.
- No paywalled content.
- No API key / token / password.
- No automatic execution path connected.
- No safety flag set to a forbidden value.
- Dry-run output not committed to the repo.
