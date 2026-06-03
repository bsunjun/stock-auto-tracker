# AI Instruction Patch — GPT / Claude / Gemini / Codex

This document specifies the **role-specific instruction patches** to
apply for the Risk-Flag Pullback Policy. Each role's pre-existing
PBKR v4 doctrine remains in force; the items below are **additive**.

No role is permitted to interpret these patches as authorization to
execute, alert, place orders, or score candidates. The human gate
remains required.

## GPT / Orchestrator

- Apply `OFFICIAL_RISK_FLAG_TAXONOMY_KR.md` before any pullback
  reasoning. Classify the official risk flag, if any, into 분류 A
  (`HARD_EXCLUDE`), 분류 B (`REGULAR_PB_EXCLUDE` with optional
  `RISK_FLAG_PULLBACK_WATCH`), 분류 C (`EXTREME_RISK_FLAG_WATCH`),
  or 분류 D (`NO_ENTRY`).
- For 분류 A (`HARD_EXCLUDE`) and 분류 D (`NO_ENTRY`): drop the
  name from any pullback-candidate reasoning. Do not summarize as a
  "watch" candidate.
- For 분류 C (`EXTREME_RISK_FLAG_WATCH`): label as
  `EXTREME_RISK_FLAG_WATCH`, hold new entry while the flag is
  active, and never label as `RISK_FLAG_PULLBACK_WATCH` until the
  flag is formally lifted to 분류 B or below.
- For 분류 B: only the labelled status `RISK_FLAG_PULLBACK_WATCH`
  may be used (when the checklist passes). Do not refer to the
  name with the wording `PB_TRIGGER`, "본진 진입", "매수 사유", or
  any equivalent in summary, prompt, or note output. While 분류 B
  is active, the name is also `REGULAR_PB_EXCLUDE` for the normal
  pullback path.
- Never combine `RISK_FLAG_PULLBACK_WATCH` or
  `EXTREME_RISK_FLAG_WATCH` with the truthy patterns: the
  `direct_trade_signal` flag set truthy, the `trade_signal` field
  set truthy, the `automatic_execution_allowed` flag set truthy,
  or the `operator_decision` field set to the execute literal.

## Claude / Auditor

- Audit every PBKR v4 candidate / observation / report draft for
  conflation between **분류 A (`HARD_EXCLUDE`)** and **분류 B
  (`REGULAR_PB_EXCLUDE` / optional `RISK_FLAG_PULLBACK_WATCH`)**.
  Block drafts that treat 분류 A names as eligible for
  `RISK_FLAG_PULLBACK_WATCH`.
- Audit for misuse of 분류 D (`NO_ENTRY`). Block drafts that
  treat a 분류 D name as eligible for `RISK_FLAG_PULLBACK_WATCH`,
  `EXTREME_RISK_FLAG_WATCH`, or any candidate posture.
- Audit for status misuse: any draft that describes a name in
  `RISK_FLAG_PULLBACK_WATCH` or `EXTREME_RISK_FLAG_WATCH` as if it
  were a `PB_TRIGGER`, a 본진 entry, or a buy reason must be
  blocked.
- Audit for forbidden Korean directive wording (the seven phrase
  categories established in PR #50 – PR #63), now extended to be
  particularly strict around 분류 B / 분류 C watch language: even
  soft directive phrasing attached to a 분류 B or 분류 C name is
  blocked.
- Audit for missed 분류 C escalations. If a name in
  `RISK_FLAG_PULLBACK_WATCH` has reclassified to 분류 C, the draft
  must move it to `EXTREME_RISK_FLAG_WATCH` and hold new entry.
- Audit for missed 분류 D escalations. If a name in any watch
  posture has reclassified to 분류 D, the draft must move it to
  `NO_ENTRY` and remove the watch posture.

## Gemini / News Grounder

- Prefer official Korean exchange / regulatory sources for risk
  flag classification: KRX, KIND, DART, official issuer
  disclosures.
- Treat 투자주의 / 투자경고 지정예고 / 투자경고 / 단기과열 예고
  / 단기과열 지정 / 공매도 과열 as candidates for 분류 B
  classification (`REGULAR_PB_EXCLUDE`), not as automatic 분류 A
  hard exclude. Provide the underlying official source label so
  that the operator and the auditor can re-classify if needed.
- Treat 투자위험 지정예고 / 투자위험종목 / 투자경고 후 정지 임박
  단계 as 분류 C (`EXTREME_RISK_FLAG_WATCH`) and do **not** propose
  them as `RISK_FLAG_PULLBACK_WATCH` candidates while the flag is
  active.
- Treat 매매거래정지 / 상장폐지 실질심사 관련 정지 / 공시불이행
  거래정지 as 분류 D (`NO_ENTRY`). Do **not** propose them as
  any watch candidate.
- Treat 관리종목 / 상장폐지 실질심사 / 거래정지 (펀더멘털 사유) /
  불성실공시 / 감사의견 문제 / 횡령/배임 / 회생/파산 as 분류 A
  (`HARD_EXCLUDE`).
- Tier 5 single-source (Telegram, group chat, unidentified summary)
  remains insufficient to promote any candidate, and is not
  sufficient to propose `RISK_FLAG_PULLBACK_WATCH` or
  `EXTREME_RISK_FLAG_WATCH`.

## Codex / PR Reviewer

- Audit every PR diff for the truthy-pattern set: the
  `direct_trade_signal` flag set truthy, the `trade_signal` field
  set truthy, the `automatic_execution_allowed` flag set truthy,
  and the `operator_decision` field set to the execute literal.
  Count must remain 0.
- Audit for forbidden Korean directive wording (count must remain
  0 across the seven phrase categories).
- Audit for status misuse: any usage of `RISK_FLAG_PULLBACK_WATCH`
  or `EXTREME_RISK_FLAG_WATCH` that resolves to or aliases
  `PB_TRIGGER`, 본진 entry, 매수 신호, or auto-execution must be
  blocked. Any usage of `HARD_EXCLUDE` or `NO_ENTRY` as if it were
  a watch posture must also be blocked.
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
  `RISK_FLAG_PULLBACK_WATCH`, `EXTREME_RISK_FLAG_WATCH`,
  `HARD_EXCLUDE`, `REGULAR_PB_EXCLUDE`, or `NO_ENTRY`.
- No role may commit real data to this repository. The prohibited
  categories defined in PR #59 / PR #60 / PR #63 apply unchanged.
