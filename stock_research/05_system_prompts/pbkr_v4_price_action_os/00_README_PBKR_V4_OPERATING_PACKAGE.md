# PBKR v4 Operating Package — README

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Purpose of PR #51

PR #50 merged the **Core Doctrine** for PBKR v4 onto `main`:

- `PBKR_V4_SUPREME_DOCTRINE.md`
- `PBKR_V4_GROWTH_POLICY.md`
- `PBKR_V4_KOREAN_MARKET_ADAPTATION.md`
- `ENTRY_TACTICS_SPEC.md`
- `SELL_RULES_POSITION_MANAGEMENT.md`
- `POSITION_SIZING_TOTAL_OPEN_RISK.md`
- `MARKET_CYCLE_SYSTEM_KR.md`
- `SCREENING_WATCHLIST_SYSTEM.md`
- `SNIPE_DAILY_PROCESS.md`

PR #51 layers an **Operating Package** *on top of* the Core Doctrine.
The Core Doctrine is **not modified by this PR**; this PR only adds
new files under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/`.

---

## 2. Scope (What This PR Adds)

| Category | Subdirectory | Purpose |
|---|---|---|
| AI project instructions | `ai_project_instructions/` | Per-role agent project prompts |
| Daily prompts (KR) | `daily_prompts/` | Cadence-bound operator prompts |
| JSON schemas | `schemas/` | Canonical payload shapes |
| Ticket templates | `ticket_templates/` | Per-decision artifacts |
| Modelbook templates | `modelbook_templates/` | Pattern memory artifacts |
| Weekly review | `weekly_review/` | Weekly hygiene artifacts |
| Manifest | `MANIFEST_PR51.json` | Inventory + safety attestations |

---

## 3. Doctrinal Invariants Re-Stated

These are **enforced** at the schema level and at the audit level by the
PR Reviewer (Codex) role described in
`ai_project_instructions/PBKR_V4_AUDITOR_INSTRUCTIONS.md`:

1. **Price Action First.** The tape ranks above estimates and
   narratives.
2. **Growth-Aware, not Growth-Ignoring.** Growth is a *structural
   edge* that classifies trade type and shapes conviction / size cap.
   Growth is **not** an entry trigger.
3. **Risk-First.** Stop sets the position; the portfolio risk budget
   caps the book.
4. **Entry Tactic before Execution.** No execution without an entry
   tactic that has explicit `trigger_level`, `failure_level`, and
   `stop_logic`.
5. **Tight and Logical Stop before Position.** Stop is pre-defined;
   position is derived from the stop.
6. **Total Open Risk-based Sizing.** TOR ceiling and stage multiplier
   `K` cap concurrent exposure.
7. **Sell Rules / Position Management Required.** Trims, structural
   exits, and time stops are pre-planned.
8. **Market Cycle is an Exposure Dial, Not a Signal.** MCS-KR does
   not authorize entries; it modulates the envelope.
9. **Screening is Candidate Generation, Not a Signal.** The screen
   produces *candidates*; transactions require human-gated audited
   tickets.
10. **Human Gate Required Before Any Execution.** No artifact in this
    operating package authorizes automated execution.

---

## 4. Hard Rules of This Operating Package

- **No engine code modified.** Parser / bridge / merge / build /
  emit / ticker_map / Kiwoom / WiseReport / Drive scripts are
  out of scope.
- **No automated execution authorized.** No agent, schema, or template
  emits or tolerates a machine-actionable trade signal.
- **Screening is candidate generation only.**
- **Market Cycle is exposure dial only.**
- **Human gate required before any execution.**
- **No real PDF / screenshot / extracted text / output JSON / CSV
  committed.**
- **No API key / token / password committed.**
- **No real ticker name, real order, or real recommendation phrase
  introduced.**

These rules apply to every file added by this PR.

---

## 5. Signal Safety Invariants

Embedded into every payload-bearing schema in `schemas/`:

```yaml
direct_trade_signal: false             # const
trade_signal: null | false             # enum
automatic_execution_allowed: false     # const
human_gate_required: true              # required
```

No file under this directory may set any of the first three to a
truthy value, and no schema accepts truthy assignments.

---

## 6. How the Operating Package Composes With Core Doctrine

```
Core Doctrine (PR #50, merged)
   └── defines rules

Operating Package (PR #51, this PR)
   ├── ai_project_instructions/   ← per-role enforcement of rules
   ├── daily_prompts/              ← operator cadence per S.N.I.P.E.
   ├── schemas/                    ← machine-checkable rule shapes
   ├── ticket_templates/           ← per-decision artifact shapes
   ├── modelbook_templates/        ← pattern memory artifact shapes
   └── weekly_review/              ← weekly hygiene artifact shapes
```

Reading order for a new operator:

1. Core Doctrine top-down (`PBKR_V4_SUPREME_DOCTRINE.md` first).
2. `ai_project_instructions/PBKR_V4_HUMAN_GATE_INSTRUCTIONS.md`.
3. `daily_prompts/01_pre_open_planner_ko.md` through `06_event_risk_recheck_ko.md`.
4. `ticket_templates/trade_ticket_template.md` and its JSON.
5. `weekly_review/weekly_review_template.md`.

---

## 7. Disclaimers

This package is an educational operating system for human research and
discipline. It is not investment advice, does not constitute a
recommendation regarding any specific security, and does not authorize
any automated execution path. The human operator is the gate.
