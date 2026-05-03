# Post-Merge Installation Guide

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. When to Read This

After PR #53 is merged into `main`, the operator follows this guide
to wire the operating package into the actual GPT Pro / Claude Code /
Gemini projects on the operator's own accounts. This guide does
**not** modify the repository — it describes manual operator-side
setup steps that happen outside the repo.

---

## 1. GPT Pro — Orchestrator Project

1. Create a new GPT Pro project named, for example,
   `PBKR v4 — Orchestrator`.
2. Open the project's instructions / system-prompt area.
3. Copy the contents of
   `stock_research/05_system_prompts/pbkr_v4_price_action_os/ai_project_instructions/PBKR_V4_ORCHESTRATOR_INSTRUCTIONS.md`
   into the project's instructions.
4. Add a project-level reminder noting the four safety invariants:
   ```
   direct_trade_signal: false
   trade_signal: null or false
   automatic_execution_allowed: false
   human_gate_required: true
   ```
5. Do not connect the project to any brokerage, trading API, or
   order-execution path. The Orchestrator's outputs are drafts for
   downstream audit, never executable orders.
6. Optional: add a project-level reading of
   `00_README_PBKR_V4_OPERATING_PACKAGE.md`,
   `PBKR_V4_SUPREME_DOCTRINE.md`, and
   `ENTRY_TACTICS_SPEC.md` as context references.

---

## 2. Claude Code — Auditor + Human Gate + Journal Review

Claude Code may run as either a project-style assistant or a
context-bound CLI session. Either way:

1. Bind the following three files as the project's instructions /
   context:
   - `ai_project_instructions/PBKR_V4_AUDITOR_INSTRUCTIONS.md`
   - `ai_project_instructions/PBKR_V4_HUMAN_GATE_INSTRUCTIONS.md`
   - `ai_project_instructions/PBKR_V4_JOURNAL_REVIEW_INSTRUCTIONS.md`
2. Bind the schemas under `schemas/` so Claude Code can request /
   verify schema validation when auditing.
3. Bind the templates under `ticket_templates/`,
   `modelbook_templates/`, and `weekly_review/` so Claude Code can
   produce / verify template-shaped artifacts.
4. Do not authorize Claude Code to modify any engine path or to
   push to `main`. Branch-only edits, draft PRs only, no
   force-push, no rebase. (PR #50 / #52 / #53 conventions.)
5. The first time Claude Code is invoked, run the dry-run
   scenarios in `DRY_RUN_PROTOCOL_ANONYMIZED.md`.

---

## 3. Gemini — News Grounder

1. Create a Gemini project (or system-prompt context) named
   `PBKR v4 — News Grounder`.
2. Copy the contents of
   `ai_project_instructions/PBKR_V4_NEWS_GROUNDER_INSTRUCTIONS.md`
   into the project's instructions.
3. Reinforce the source-tier rules: Tier 5 (Telegram-only) is
   never load-bearing for leader / position trades. The Auditor
   issues a `missing_evidence` finding (`A204`) if such a candidate
   is forwarded.
4. Do not authorize Gemini to fetch paywalled content verbatim.
5. Do not connect Gemini to any execution venue.

---

## 4. Daily Prompt Order (Operator Action Sequence)

Each trading day, the operator runs the following in order:

1. **08:00–08:50 — Pre-open.** Send
   `daily_prompts/01_pre_open_planner_ko.md` flow:
   - Compose the `market_cycle` snapshot.
   - Request `news_grounding_pack` from Gemini.
   - Request `daily_focus_list` draft from GPT Orchestrator.
   - Request `audit_pack` from Claude Auditor.
   - Fill tickets per `ticket_templates/trade_ticket_template.md`.
   - Build the snipe queue under TOR headroom.
2. **09:00–09:15 — Opening discovery.** Run
   `daily_prompts/02_opening_discovery_ko.md`. Observe only.
3. **09:15–11:30 — Primary window.** Run
   `daily_prompts/03_primary_window_snipe_check_ko.md`. Run S.N.I.P.E.
   per name. Pass through Claude Human Gate for any 5/5-yes
   candidate.
4. **11:30–13:30 — Mid-day caution.** Continue mid-day filters.
5. **13:30–15:10 — Afternoon.** Continue monitoring. Structural
   exits priority.
6. **15:10–15:30 — Closing window.** No new entries. Risk-stop /
   structural only.
7. **15:30–17:00 — Post-close.** Run
   `daily_prompts/04_close_review_ko.md` then
   `daily_prompts/05_post_close_next_day_prep_ko.md`.

Event-risk recheck `daily_prompts/06_event_risk_recheck_ko.md` is
invoked at any time during the day when a new disclosure / news
item lands.

---

## 5. Weekly Review Order

On the last trading session of the week, after post-close:

1. Run `weekly_review/weekly_review_prompt_ko.md` (Korean prompt).
2. Produce a `weekly_review` payload conforming to
   `schemas/weekly_review.schema.json` and / or fill
   `weekly_review/weekly_review_template.md`.
3. Compute expectancy; decide next-week `K` adjustment.
4. Update modelbook entries for closed and missed trades.
5. Commit nothing of the operational results to the repository.
   The repository holds templates and rules only.

---

## 6. Local / Cloud Environment Rules

- **Do not store any API key, token, password, or bearer credential
  in the repository or in any file under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/`.**
- Operator-side credentials live only in the operator's secret
  manager (OS keychain, password manager, or environment variables
  outside the repo).
- Do not connect any agent to a brokerage API, an order-execution
  path, or a webhook that consumes the operating-package artifacts
  as a signal feed.
- Do not commit any output (focus list / audit pack / ticket /
  journal entry / modelbook entry / weekly review payload) that
  references a real ticker or real numbers. Operational artifacts
  are private and live in the operator's local journal, never in
  the repository.

---

## 7. First-Week Dry-Run Recommendation

For the first **five trading sessions** after this PR is merged:

- Run only the dry-run scenarios in
  `DRY_RUN_PROTOCOL_ANONYMIZED.md`.
- Do not consume any real candidate.
- Do not transact based on any artifact produced.
- At the end of the five sessions, run the manual validation
  checklist (`MANUAL_VALIDATION_CHECKLIST.md`) plus a postmortem
  on each scenario.

Only after a clean dry-run week does the operator move to processing
real candidates — and even then, **with full safety flags intact and
human gate as the final decider**.

---

## 8. Hard Bans (Apply Indefinitely)

- No automatic execution path connected.
- No safety flag flipped to a forbidden value.
- No forced re-binding of a service to an unauthorized role.
- No engine code modified to satisfy operating-package needs (use
  a separate PR with a separate review).
- No real artifacts committed to the repository.
- No direct push to `main`.
- No force-push.
- No rebase of merged commits.
