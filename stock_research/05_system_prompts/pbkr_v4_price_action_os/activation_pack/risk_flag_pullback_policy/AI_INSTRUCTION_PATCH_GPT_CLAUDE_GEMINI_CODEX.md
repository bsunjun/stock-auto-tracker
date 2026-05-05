# AI Instruction Patch — GPT / Claude / Gemini / Codex

This document specifies the **role-specific instruction patches** to
apply for the Risk-Flag Pullback Policy. Each role's pre-existing
PBKR v4 doctrine remains in force; the items below are **additive**.

No role is permitted to interpret these patches as authorization to
execute, alert, place orders, or score candidates. The human gate
remains required.

## GPT / Orchestrator

- Apply `OFFICIAL_RISK_FLAG_TAXONOMY_KR.md` before any pullback
  reasoning. Classify the official risk flag, if any, into 분류 A,
  분류 B, or 분류 C.
- For 분류 A and 분류 C: drop the name from any pullback-candidate
  reasoning. Do not summarize as a "watch" candidate.
- For 분류 B: only the labelled status `RISK_FLAG_PULLBACK_WATCH`
  may be used. Do not refer to the name with the wording
  `PB_TRIGGER`, "본진 진입", "매수 사유", or any equivalent in
  summary, prompt, or note output.
- Never combine `RISK_FLAG_PULLBACK_WATCH` with truthy values for
  `direct_trade_signal`, `trade_signal`,
  `automatic_execution_allowed`, or with the execute literal in
  `operator_decision`.

## Claude / Auditor

- Audit every PBKR v4 candidate / observation / report draft for
  conflation between **분류 A (fundamental hard exclude)** and
  **분류 B (market-structure cooling risk)**. Block drafts that
  treat 분류 A names as eligible for `RISK_FLAG_PULLBACK_WATCH`.
- Audit for status misuse: any draft that describes a name in
  `RISK_FLAG_PULLBACK_WATCH` as if it were a `PB_TRIGGER`, a 본진
  entry, or a buy reason must be blocked.
- Audit for forbidden Korean directive wording (the seven phrase
  categories established in PR #50 – PR #63), now extended to be
  particularly strict around 분류 B watch language: even soft
  directive phrasing (예: "지금 매수해도 된다", "매수 가능") is
  blocked when attached to a 분류 B name.
- Audit for missed 분류 C escalations. If a name in
  `RISK_FLAG_PULLBACK_WATCH` has reclassified to 분류 C, flag the
  draft.

## Gemini / News Grounder

- Prefer official Korean exchange / regulatory sources for risk
  flag classification: KRX, KIND, DART, official issuer
  disclosures.
- Treat 투자주의 / 투자경고 지정예고 / 투자경고 / 단기과열 as
  candidates for 분류 B classification, not as automatic 분류 A
  hard exclude. Provide the underlying official source label so
  that the operator and the auditor can re-classify if needed.
- Treat 투자위험 / 매매거래정지 임박 / 정지 단계로 진행 중인 상태
  as 분류 C and do **not** propose them as
  `RISK_FLAG_PULLBACK_WATCH` candidates.
- Tier 5 single-source (Telegram, group chat, unidentified summary)
  remains insufficient to promote any candidate, and is not
  sufficient to propose `RISK_FLAG_PULLBACK_WATCH`.

## Codex / PR Reviewer

- Audit every PR diff for the truthy-pattern set: the
  `direct_trade_signal` flag set truthy, the `trade_signal` field
  set truthy, the `automatic_execution_allowed` flag set truthy,
  and the `operator_decision` field set to the execute literal.
  Count must remain 0.
- Audit for forbidden Korean directive wording (count must remain
  0 across the seven phrase categories).
- Audit for status misuse: any usage of `RISK_FLAG_PULLBACK_WATCH`
  that resolves to or aliases `PB_TRIGGER`, 본진 entry, 매수 신호,
  or auto-execution must be blocked.
- Audit for scope creep: changes to validators, fixtures, schemas,
  or engine code under cover of a documentation PR for the
  Risk-Flag Pullback Policy must be blocked.
- Audit for real-data leakage: real ticker, real price, real news,
  real disclosure id, real flow, real order, real account,
  real-looking Korean six-digit ticker codes — count must remain 0.

## Common Invariants (All Roles)

- The `automatic_execution_allowed` flag remains set falsy at all
  times. No role is permitted to flip it.
- The human gate remains required. No role may bypass it.
- No role may produce an order, draft order, order ticket,
  reconstructed fill, or execution intent from a name in
  `RISK_FLAG_PULLBACK_WATCH`.
- No role may commit real data to this repository. The prohibited
  categories defined in PR #59 / PR #60 / PR #63 apply unchanged.
