# Fixture Validation Notes

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.
>
> **No automated validator is provided in this PR.** Validation is
> manual; the steps below are the canonical procedure.

---

## 1. Scope

This document maps each fixture in `dry_run_fixtures/` to:

- the dry-run scenario from `../DRY_RUN_PROTOCOL_ANONYMIZED.md`,
- the PR #52 schemas it should align to,
- the PR #52 ticket / modelbook / weekly-review template it
  illustrates (where applicable),
- the doctrinal expectations the fixture demonstrates.

A future PR (e.g., PR #55) **may** add a non-execution validator
script. Until then, the operator validates manually using §3.

---

## 2. Fixture Map

| Fixture file | Scenario | Schemas referenced | Templates referenced | Expected outcome |
|---|---|---|---|---|
| `scenario_s1_clean_pass.fixture.json` | S1 | `market_cycle.schema.json`, `news_grounding_pack.schema.json`, `daily_focus_list.schema.json`, `audit_pack.schema.json`, `trade_ticket.schema.json` | `trade_ticket_template.{md,json}` | Audit `pass`; gate `pass`; `operator_decision = pending`. |
| `scenario_s2_hard_veto.fixture.json` | S2 | `daily_focus_list.schema.json`, `audit_pack.schema.json` | `audit_ticket_template.md` | Auditor `block` finding `A001` (entry_tactic missing fields); chain stops at audit. |
| `scenario_s3_tier5_demote.fixture.json` | S3 | `news_grounding_pack.schema.json`, `audit_pack.schema.json` | `audit_ticket_template.md` | Tier-5-only evidence; finding `A204` (missing_evidence); never enters snipe queue. |
| `scenario_s4_tor_saturation.fixture.json` | S4 | `daily_focus_list.schema.json`, `audit_pack.schema.json` | — | Lower-priority entry → `revise_required` finding `A102` (TOR breach); focus list compresses. |
| `scenario_s5_gate_deny.fixture.json` | S5 | `trade_ticket.schema.json`, `position_update.schema.json` (n/a) | `trade_ticket_template.{md,json}` | Gate `deny`; `unchecked_items` contains `sell_rules.time_stop_window_sessions`. |
| `scenario_s6_no_action_day.fixture.json` | S6 | `market_cycle.schema.json`, `daily_focus_list.schema.json` | `no_action_journal_template.md` | Empty focus list; reason `regime_defensive`; `operator_decision = abstain` on the no-action journal. |

---

## 3. Manual Validation Procedure

For each fixture:

1. **Open the fixture.** Confirm it is JSON-parseable
   (`python3 -c "import json; json.load(open('<path>'))"`).
2. **Check anonymization invariants** (per
   `README_DRY_RUN_FIXTURES.md` §4):
   - `name` ∈ {`Candidate A`, `Candidate B`, `Candidate C`}.
   - Identifiers contain `cand-A-anon` / `cand-B-anon` /
     `cand-C-anon` substrings only.
   - All level fields are text placeholders prefixed `anon-`.
   - All dates are synthetic (`2099-...`).
   - All sources are synthetic (`synthetic-tier...-...`).
   - `operator_decision` is `pending` or `abstain` (never
     `execute`).
3. **Check signal-safety invariants:**
   - `direct_trade_signal == false`.
   - `trade_signal ∈ {null, false}`.
   - `automatic_execution_allowed == false`.
   - `human_gate_required == true`.
4. **Open each schema in `schema_refs`** and walk the fixture's
   relevant artifact against the schema:
   - All required fields present.
   - No `additionalProperties` outside what the schema permits.
   - Enum-valued fields use the documented enum literal.
5. **Confirm the `expected_outcome` section** of the fixture
   matches the scenario's documented outcome in
   `../DRY_RUN_PROTOCOL_ANONYMIZED.md` §2.

If any step fails, file a follow-up commit on this branch (no
force-push) and re-validate.

---

## 4. Forbidden in All Fixtures

- Real ticker symbols, company names, KR exchange codes, DART
  numbers, real news headlines.
- Real price, quantity, order id, fill price.
- `operator_decision = "execute"`.
- Any safety flag set truthy.
- `screenshot_*`, `pdf_*`, `output_*` keys (these signal real-data
  attachments).
- Buy / sell recommendation wording in any language.

---

## 5. Acceptance for This PR

- 8 files added under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/dry_run_fixtures/`.
- 6 `.fixture.json` files parse cleanly as JSON.
- Anonymization invariants satisfied across all fixtures.
- Signal-safety invariants satisfied across all fixtures.
- No PR #50 / PR #52 / PR #53 file modified.
- No engine code modified.
- No real-data artifact (`.csv`, `.parquet`, `.xlsx`, `.pdf`,
  `.png`, `.jpg`, `.jpeg`, `.webp`) committed.

---

## 6. Future Validation Script (Non-Binding)

If a future PR adds a validator:

- Validator must be **read-only** (no file writes, no network).
- Validator must not connect to any brokerage / market-data feed.
- Validator failure does not authorize automated execution; it
  signals a fixture or schema drift only.
- Validator output is reproducible from the committed fixtures
  alone — no operator-private inputs required.
