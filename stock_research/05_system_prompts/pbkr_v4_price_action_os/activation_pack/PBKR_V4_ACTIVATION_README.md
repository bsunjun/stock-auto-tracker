# PBKR v4 Activation README

> Educational. Not advice. Not a signal source.
> `direct_trade_signal = false`. `trade_signal = null` or `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 1. Purpose of PR #53

PR #50 merged the **Core Doctrine**. PR #52 merged the **Operating
Package** (AI project instructions, daily prompts, JSON schemas,
ticket templates, modelbook templates, weekly review templates).

PR #53 layers an **Activation / Operator Runbook** *on top of* both
prior layers. This PR documents **how a human operator actually
runs the system day to day**: which agent uses which prompt, what
the handoff order is, what the dry-run protocol looks like, and
what the post-merge installation steps are.

This PR is **documentation only**. It does not modify any earlier
file. It does not introduce any executable code, real ticker, real
order, or real output artifact.

---

## 2. Scope (What This PR Adds)

All eight files live in
`stock_research/05_system_prompts/pbkr_v4_price_action_os/activation_pack/`:

| File | Purpose |
|---|---|
| `PBKR_V4_ACTIVATION_README.md` | This file. Activation layer overview. |
| `AI_SERVICE_MAPPING.md` | Maps GPT Pro / Claude Code / Gemini / Human roles to specific PR #52 instruction files. |
| `DAILY_OPERATOR_RUNBOOK_KR.md` | Hour-by-hour daily routine in KST, linking to the relevant prompts / templates / schemas. |
| `HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md` | Stepwise handoff flow with input / output / fallback per stage. |
| `MANUAL_VALIDATION_CHECKLIST.md` | Pre-operation checks the human runs before activating the system. |
| `DRY_RUN_PROTOCOL_ANONYMIZED.md` | Anonymized dry-run procedure (candidates A / B / C only, no real names). |
| `PR53_ACCEPTANCE_CRITERIA.md` | Acceptance criteria for merging this PR. |
| `POST_MERGE_INSTALLATION_GUIDE.md` | After-merge human steps to wire the operating package into actual GPT Pro / Claude Code / Gemini projects. |

---

## 3. Doctrinal Posture (Re-Stated Compactly)

- **Price Action First.** Tape ranks above estimates and narratives.
- **Growth-Aware, not Growth-Ignoring.** Growth is a structural edge,
  never an entry trigger.
- **Risk-First.** Stop sets the position; TOR caps the book.
- **Entry Tactic before Execution.** No execution without a tactic
  with explicit `trigger_level`, `failure_level`, `stop_logic`.
- **Total Open Risk-based Sizing.**
- **Sell Rules / Position Management Required.**
- **Market Cycle = Exposure Dial.** Not a signal.
- **Screening = Candidate Generation.** Not a signal.
- **Human Gate Required Before Any Execution.**

---

## 4. Hard Rules of This PR

- **No engine code modified.** Parser / bridge / merge / build /
  emit / ticker_map / Kiwoom / WiseReport / Drive scripts are
  out of scope and not modified.
- **No automated execution authorized.** Nothing in activation_pack
  authorizes any agent or pipeline to transact without an explicit
  human-gate `pass` followed by an explicit human operator decision.
- **No real ticker / order / recommendation phrase committed.**
- **No real PDF / screenshot / extracted text / real output JSON / CSV
  committed.**
- **No API key / token / password committed.**
- **No `direct_trade_signal` flag set truthy. No `trade_signal`
  field set truthy. No `automatic_execution_allowed` flag set
  truthy.**
- **PR #50 Core Doctrine files are not modified by this PR.**
- **PR #52 Operating Package files are not modified by this PR.**

---

## 5. Reading Order

If you have not read the prior layers, do so first:

1. PR #50 Core Doctrine (top-level `*.md` in the parent directory).
2. PR #52 Operating Package
   (`00_README_PBKR_V4_OPERATING_PACKAGE.md` and the six
   subdirectories).
3. This Activation README.
4. `AI_SERVICE_MAPPING.md` — agent-to-instruction bindings.
5. `MANUAL_VALIDATION_CHECKLIST.md` — pre-flight checks.
6. `DAILY_OPERATOR_RUNBOOK_KR.md` — actual daily flow in KST.
7. `HANDOFF_PROTOCOL_GPT_CLAUDE_GEMINI.md` — agent handoff order.
8. `DRY_RUN_PROTOCOL_ANONYMIZED.md` — first-week dry-run procedure.
9. `POST_MERGE_INSTALLATION_GUIDE.md` — after merging, wire it in.

`PR53_ACCEPTANCE_CRITERIA.md` is the merge gate for this PR.

---

## 6. Disclaimers

- This activation pack is an educational operating procedure.
- Nothing in it is investment advice or a recommendation regarding
  any specific security.
- The human operator is solely responsible for any decisions taken
  outside this repository.
