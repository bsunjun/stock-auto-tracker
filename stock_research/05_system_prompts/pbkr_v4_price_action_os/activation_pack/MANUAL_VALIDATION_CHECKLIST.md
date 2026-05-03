# Manual Validation Checklist (Pre-Activation)

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. When to Run This

Run this checklist:

- Before activating the operating system for the first time after
  PR #53 is merged.
- After any PR that touches files under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/`.
- Periodically (monthly) as a sanity check.

The checklist is **manual** by design. No automated job is
authorized to gate operations on its result.

---

## 1. PR #50 Core Doctrine Files Present (9)

- [ ] `../PBKR_V4_SUPREME_DOCTRINE.md`
- [ ] `../PBKR_V4_GROWTH_POLICY.md`
- [ ] `../PBKR_V4_KOREAN_MARKET_ADAPTATION.md`
- [ ] `../ENTRY_TACTICS_SPEC.md`
- [ ] `../SELL_RULES_POSITION_MANAGEMENT.md`
- [ ] `../POSITION_SIZING_TOTAL_OPEN_RISK.md`
- [ ] `../MARKET_CYCLE_SYSTEM_KR.md`
- [ ] `../SCREENING_WATCHLIST_SYSTEM.md`
- [ ] `../SNIPE_DAILY_PROCESS.md`

---

## 2. PR #52 Operating Package Files Present

### 2.1 README + Manifest

- [ ] `../00_README_PBKR_V4_OPERATING_PACKAGE.md`
- [ ] `../MANIFEST_PR51.json`

### 2.2 AI Project Instructions (5)

- [ ] `../ai_project_instructions/PBKR_V4_ORCHESTRATOR_INSTRUCTIONS.md`
- [ ] `../ai_project_instructions/PBKR_V4_AUDITOR_INSTRUCTIONS.md`
- [ ] `../ai_project_instructions/PBKR_V4_NEWS_GROUNDER_INSTRUCTIONS.md`
- [ ] `../ai_project_instructions/PBKR_V4_HUMAN_GATE_INSTRUCTIONS.md`
- [ ] `../ai_project_instructions/PBKR_V4_JOURNAL_REVIEW_INSTRUCTIONS.md`

### 2.3 Daily Prompts (6, KR)

- [ ] `../daily_prompts/01_pre_open_planner_ko.md`
- [ ] `../daily_prompts/02_opening_discovery_ko.md`
- [ ] `../daily_prompts/03_primary_window_snipe_check_ko.md`
- [ ] `../daily_prompts/04_close_review_ko.md`
- [ ] `../daily_prompts/05_post_close_next_day_prep_ko.md`
- [ ] `../daily_prompts/06_event_risk_recheck_ko.md`

### 2.4 Schemas (10, JSON Schema draft-07)

- [ ] `../schemas/pbkr_v4_common.schema.json`
- [ ] `../schemas/market_cycle.schema.json`
- [ ] `../schemas/watchlist_item.schema.json`
- [ ] `../schemas/daily_focus_list.schema.json`
- [ ] `../schemas/snipe_candidate.schema.json`
- [ ] `../schemas/trade_ticket.schema.json`
- [ ] `../schemas/position_update.schema.json`
- [ ] `../schemas/audit_pack.schema.json`
- [ ] `../schemas/news_grounding_pack.schema.json`
- [ ] `../schemas/weekly_review.schema.json`

### 2.5 Ticket Templates (6)

- [ ] `../ticket_templates/trade_ticket_template.md`
- [ ] `../ticket_templates/trade_ticket_template.json`
- [ ] `../ticket_templates/position_management_ticket_template.md`
- [ ] `../ticket_templates/position_management_ticket_template.json`
- [ ] `../ticket_templates/audit_ticket_template.md`
- [ ] `../ticket_templates/no_action_journal_template.md`

### 2.6 Modelbook Templates (4)

- [ ] `../modelbook_templates/modelbook_entry_template.md`
- [ ] `../modelbook_templates/modelbook_index_template.json`
- [ ] `../modelbook_templates/failure_case_review_template.md`
- [ ] `../modelbook_templates/best_case_review_template.md`

### 2.7 Weekly Review (2)

- [ ] `../weekly_review/weekly_review_template.md`
- [ ] `../weekly_review/weekly_review_prompt_ko.md`

---

## 3. Forbidden-Phrase Audits (Manual Grep)

Run these greps under
`stock_research/05_system_prompts/pbkr_v4_price_action_os/`:

- [ ] Korean retail-trading buy / sell exhortations and their
      urgency / certainty equivalents → expected count: 0. (Maintain
      the canonical detection pattern set in the operator's private
      rule store; no enumerated forbidden phrase appears in this
      checklist by design.)
- [ ] English imperative buy / sell phrasing ("buy now", "sell now",
      "strong buy", "actionable buy/sell", price targets) →
      expected count: 0.
- [ ] `direct_trade_signal[[:space:]]*[:=][[:space:]]*[Tt]rue` →
      expected count: 0.
- [ ] `trade_signal[[:space:]]*[:=][[:space:]]*([Tt]rue|1)` (excluding
      `direct_trade_signal`) → expected count: 0.
- [ ] `automatic_execution_allowed[[:space:]]*[:=][[:space:]]*[Tt]rue` →
      expected count: 0.
- [ ] API key / token / password / bearer-token strings → expected
      count: 0.

---

## 4. Engine Code Modification Audit

- [ ] `git diff --name-only main..<your branch>` shows **only**
      paths under
      `stock_research/05_system_prompts/pbkr_v4_price_action_os/`.
- [ ] No file under engine paths (parser / bridge / merge / build /
      emit / ticker_map / Kiwoom / WiseReport / Drive script) is
      modified.
- [ ] No Python (`*.py`), shell (`*.sh`), notebook (`*.ipynb`), or
      workflow YAML (`.github/workflows/*.yml`) is modified by the
      branch.

---

## 5. Real-Artifact Audit

The following file types must **not** appear in the branch's
additions:

- [ ] `*.csv` (any csv).
- [ ] `*.parquet`.
- [ ] `*.xlsx`.
- [ ] `*.pdf`.
- [ ] `*.png` / `*.jpg` / `*.jpeg` / `*.webp` / `*.gif`.
- [ ] `*.zip` / `*.tar.gz` / any archive.
- [ ] Any "output" JSON or extracted text dump produced from real
      market data.

---

## 6. Branch / Main Safety Audit

- [ ] Working branch is **not** `main`.
- [ ] Working branch tracks a remote of the form `origin/<branch>`
      where `<branch> != main`.
- [ ] No direct push to `origin main` performed by this session.
- [ ] No force-push performed.
- [ ] No `git rebase` performed against `main`.
- [ ] All commits in the branch were authored by the operator and
      not by an automation account.

---

## 7. Schema Sanity Check

- [ ] Every JSON schema parses cleanly (`python3 -c "import json;
      json.load(open(<path>))"`).
- [ ] Every payload-bearing schema requires
      `direct_trade_signal: false`, `trade_signal: null|false`,
      `automatic_execution_allowed: false`, `human_gate_required: true`.

---

## 8. Doctrine Consistency Check

- [ ] `daily_focus_list` schema enum for `trade_class` includes
      `leader_grade_position`.
- [ ] `trade_ticket` schema lists every required field documented in
      `PR53_ACCEPTANCE_CRITERIA.md` §4.
- [ ] No new prompt / template introduces buy / sell recommendation
      wording.

---

## 9. Sign-Off

The operator records, in their journal:

- Date / time of checklist run.
- All checklist items passed (or which failed and what corrective
  action was taken).
- A 1-line attestation that activation will not connect to any
  brokerage or auto-execution path.

If any item failed, do not activate. File a follow-up PR or fix
the source artifact before retrying.
