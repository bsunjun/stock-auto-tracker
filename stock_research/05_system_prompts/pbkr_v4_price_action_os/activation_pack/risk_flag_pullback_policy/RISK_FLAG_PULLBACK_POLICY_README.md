# PBKR v4 Risk-Flag Pullback Policy (PR #64)

## Purpose

This PR introduces the **Risk-Flag Pullback Policy** — a doctrinal
clarification on how PBKR v4 treats Korean exchange official risk
flags such as 투자주의, 투자경고 지정예고, 투자경고, and 단기과열.

The core observation is:

- An official **risk flag is not automatically a corporate
  fundamental concern**.
- Some risk flags (투자주의 / 투자경고 지정예고 / 투자경고 / 단기과열)
  are primarily **market-structure cooling** indicators — the
  exchange is signaling that price/volume action has overheated, not
  that the issuer's business has deteriorated.
- Other risk flags (관리종목, 거래정지, 상장폐지 단계, 불성실공시 등)
  are **fundamental / corporate** concerns and remain hard exclude.

This PR documents that distinction, but it does **not** turn any
risk flag into a buy idea. It creates a separate observation status
called `RISK_FLAG_PULLBACK_WATCH`, used only as a high-risk watch
posture, and explicitly **not** promoted to a normal `PB_TRIGGER`.

## Position Within the PBKR v4 Activation Pack

- PR #50 — Core Doctrine
- PR #52 — Operating Package
- PR #53 — Activation / Operator Runbook
- PR #54 – PR #58 — Anonymized dry-run material
- PR #59 — Real-Data Boundary Planning
- PR #60 — Read-Only Real-Data Observation Plan
- PR #61 — Read-Only Observation Approval Packet
- PR #62 — Read-Only Observation Start Gate
- PR #63 — Private-Journal-Only Observation Runbook
- **PR #64 — Risk-Flag Pullback Policy (this PR)**

## What This PR Is

- A markdown-only documentation PR.
- Seven documents under
  `stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/risk_flag_pullback_policy/`.
- A taxonomy of official risk flags (Fundamental / Cooling /
  Extreme), the conditions for `RISK_FLAG_PULLBACK_WATCH`, the role
  patches for GPT / Claude / Gemini / Codex, the daily audit prompt
  patch (Korean), the Google Drive mirror note, and PR #64
  acceptance criteria.

## What This PR Is NOT

- It is **not** a buy signal generator.
- It is **not** a permission to enter a 투자경고 name automatically.
- It is **not** a promotion of any risk-flag situation to
  `PB_TRIGGER` or to "본진" entry.
- It does **not** modify validators, fixtures, schemas, or engine
  code.
- It does **not** add Python or shell code.
- It does **not** add any broker, API, Kiwoom, WiseReport, or Drive
  connection.
- It does **not** introduce real ticker, real price, real news, real
  disclosure id, real flow, real order, or real account data.
- It does **not** authorize any automated execution under any
  condition.
- Its merge alone does **not** start any cycle, observation, or
  candidate scoring.

## Hard Rules Carried Forward

- The `direct_trade_signal` flag set truthy is not permitted.
- The `trade_signal` field set truthy is not permitted.
- The `automatic_execution_allowed` flag set truthy is not permitted.
- The `operator_decision` field set to the execute literal is not
  permitted.
- The seven Korean trade-instruction phrase categories established
  in PR #50 – PR #63 (imperative buy, imperative sell, emphatic buy,
  certainty assertion, sharp-rise prediction, buy-signal label,
  sell-signal label) remain not permitted in any document.
- Real ticker, real name, real price, real news, real disclosure id,
  real flow, real order, and real account data are not permitted in
  the repository.
- `RISK_FLAG_PULLBACK_WATCH` is **never** treated as a
  trigger / 매수 사유. It is a watch posture only, with a small
  size-limit envelope and a strict abort posture.

## Reading Order

1. `RISK_FLAG_PULLBACK_POLICY_README.md` (this file)
2. `OFFICIAL_RISK_FLAG_TAXONOMY_KR.md`
3. `RISK_FLAG_PULLBACK_WATCH_CHECKLIST.md`
4. `AI_INSTRUCTION_PATCH_GPT_CLAUDE_GEMINI_CODEX.md`
5. `DAILY_AUDIT_PROMPT_PATCH_KR.md`
6. `GOOGLE_DRIVE_SYNC_NOTE.md`
7. `PR64_ACCEPTANCE_CRITERIA.md`

## Merge Posture

- Opened as a **draft**.
- Codex review is required before merge.
- Merge of this PR alone does **not** start automated execution,
  order placement, candidate scoring, or candidate recommendation.
- Merge is **not** performed by the agent that opens the PR.
