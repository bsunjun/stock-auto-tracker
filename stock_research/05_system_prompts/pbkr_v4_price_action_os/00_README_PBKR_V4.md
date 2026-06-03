# PBKR v4 — Operating Package README

> Educational doctrine. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null`.
> `human_gate_required = true`.

---

## What This Directory Is

This directory is the canonical home of the **PBKR v4 Price-Action Operating
System** — a price-action-first, growth-aware, risk-first doctrine for human
operators working the Korean equity market with AI-assisted research support.

The operating system is composed of two layers:

1. **Core Doctrine** (top-level markdown files in this directory). These are
   the rules of the game. They are stable; revisions require explicit
   doctrinal justification.
2. **AI Operating Package** (subdirectories `03_…`, `04_…`, `05_…`, `07_…`).
   These are the tools that let the operator and a small set of AI agents
   execute the doctrine consistently, day after day.

Both layers share one invariant: **no automated trade execution and no
machine-actionable trade signals**. The operating system supports human
decisioning; the human is always the gate.

---

## Directory Layout

```
stock_research/05_system_prompts/pbkr_v4_price_action_os/
├── 00_README_PBKR_V4.md                     ← this file
├── PBKR_V4_SUPREME_DOCTRINE.md              ← top-level doctrine
├── PBKR_V4_GROWTH_POLICY.md                 ← growth as structural edge
├── PBKR_V4_KOREAN_MARKET_ADAPTATION.md      ← KR-specific rules
├── ENTRY_TACTICS_SPEC.md                    ← Edges / Setups / Entry Tactics
├── SELL_RULES_POSITION_MANAGEMENT.md        ← exits and management
├── POSITION_SIZING_TOTAL_OPEN_RISK.md       ← sizing and TOR
├── MARKET_CYCLE_SYSTEM_KR.md                ← MCS-KR
├── SCREENING_WATCHLIST_SYSTEM.md            ← funnel and watchlist
├── SNIPE_DAILY_PROCESS.md                   ← S.N.I.P.E. day structure
│
├── 03_ai_project_instructions/              ← per-agent project prompts
│   ├── GPT_PBKR_Orchestrator_v4.md
│   ├── Claude_PBKR_Auditor_v4.md
│   ├── Gemini_NewsGrounder_v4.md
│   ├── ClaudeCode_Automation_v4.md
│   └── Codex_Reviewer_v4.md
│
├── 04_daily_prompts/                        ← cadence-bound chat prompts
│   ├── MORNING_PROMPTS.md
│   ├── INTRADAY_PROMPTS.md
│   └── CLOSE_REVIEW_PROMPTS.md
│
├── 05_schemas/                              ← canonical JSON schemas
│   ├── PBKR_V4_candidate_schema.json
│   ├── PBKR_V4_ticket_schema.json
│   ├── PBKR_V4_audit_schema.json
│   ├── PBKR_V4_focus_list_schema.json
│   └── PBKR_V4_modelbook_schema.json
│
└── 07_templates/                            ← human-fillable templates
    ├── Daily_Focus_Ticket_Template.md
    ├── Weekly_Review_Template.md
    ├── Modelbook_Template.md
    └── Postmortem_Template.md
```

(The `06_` slot is reserved.)

---

## Agent Roles in the Operating System

Five AI roles, each with a single function, each forbidden from acting as
a signal source:

| Role | Agent | Single function |
|---|---|---|
| **Orchestrator** | GPT (`03_ai_project_instructions/GPT_PBKR_Orchestrator_v4.md`) | Compresses candidates into a daily focus list with thesis, edge, setup, tactic, stop, size plan |
| **Auditor** | Claude (`03_ai_project_instructions/Claude_PBKR_Auditor_v4.md`) | Hard veto on rule violations; supplies a counter-thesis to every focus name |
| **NewsGrounder** | Gemini (`03_ai_project_instructions/Gemini_NewsGrounder_v4.md`) | Macro / news / policy / technology / newspaper-flow grounding |
| **Repo Automation** | Claude Code (`03_ai_project_instructions/ClaudeCode_Automation_v4.md`) | Schema validation, dry-run linting; never executes orders |
| **PR Reviewer** | Codex (`03_ai_project_instructions/Codex_Reviewer_v4.md`) | Reviews PRs; detects forbidden-phrase / signal-leak attempts |

**No single agent — and no combination of agents — produces an executable
order.** The human operator reads the synthesized output and decides.

---

## Daily Cadence

Run by `04_daily_prompts/`:

- **Morning (`MORNING_PROMPTS.md`)** — pre-open prep: stage read, focus
  list build, ticket fill.
- **Intraday (`INTRADAY_PROMPTS.md`)** — primary-window confirmation
  reads, exit triggers; explicitly forbids new entries during opening
  auction and closing auction windows.
- **Close Review (`CLOSE_REVIEW_PROMPTS.md`)** — journal, modelbook,
  postmortem, next-day focus prep.

The cadence is the **S.N.I.P.E.** day structure defined in
`SNIPE_DAILY_PROCESS.md`.

---

## Hard Operating Rules

The following invariants apply across every file in this directory:

1. `direct_trade_signal = false` is the only acceptable value at any flag
   site. No pipeline ever sets it `true`.
2. `trade_signal = null` is the only acceptable value at any flag site. No
   pipeline ever sets it truthy.
3. `human_gate_required = true` for every transaction-adjacent decision.
4. A name without **(setup + entry tactic + `trigger_level` + `failure_level` +
   `stop_logic` + size plan + sell plan)** cannot enter the daily focus
   list, regardless of how compelling its thesis sounds.
5. Growth is a **structural edge**, never an entry trigger and never a
   tape override. Growth shapes leader quality, conviction, holding-period
   class, and `conviction_cap` / `setup_quality_cap` only.
6. Screening produces *candidates*, not transactions. The screen is a
   radar, not a signal.
7. No real screenshots, real PDFs, real-data JSON / CSV outputs, or Drive
   write actions are committed under this directory.
8. No buy / sell recommendation wording in any language (English
   imperative buy/sell phrasing, Korean retail-trading exhortations,
   urgency or certainty equivalents) appears anywhere in this
   operating system.

Violations of any of the above are the explicit subject of the Codex PR
reviewer (see `03_ai_project_instructions/Codex_Reviewer_v4.md`).

---

## How to Read This Directory

- **First time:** `PBKR_V4_SUPREME_DOCTRINE.md` →
  `PBKR_V4_GROWTH_POLICY.md` → `ENTRY_TACTICS_SPEC.md` →
  `SELL_RULES_POSITION_MANAGEMENT.md` →
  `POSITION_SIZING_TOTAL_OPEN_RISK.md` → `MARKET_CYCLE_SYSTEM_KR.md` →
  `SCREENING_WATCHLIST_SYSTEM.md` → `SNIPE_DAILY_PROCESS.md`.
- **Setting up an AI project:** `03_ai_project_instructions/<role>_v4.md`.
- **Running a session:** `04_daily_prompts/MORNING_PROMPTS.md` first.
- **Logging a position:** `07_templates/Daily_Focus_Ticket_Template.md`,
  validated against `05_schemas/PBKR_V4_ticket_schema.json`.
- **Weekly hygiene:** `07_templates/Weekly_Review_Template.md`.

---

## Versioning

- v4.0 — Core Doctrine (PR #50, merged on main).
- v4.1 — Operating Package (this PR).
- Future revisions require an explicit changelog entry.

---

## Disclaimer

This directory is an educational operating system for human research and
discipline. It is not investment advice, it is not a recommendation
regarding any specific security, and it is not a system that emits
machine-actionable trade signals. Anyone using these documents is
responsible for their own decisions.
