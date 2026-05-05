# Risk-Flag Pullback Watch Checklist

This checklist defines the conditions under which a name carrying a
**market-structure cooling risk flag** (분류 B from
`OFFICIAL_RISK_FLAG_TAXONOMY_KR.md`) may be classified into the
high-risk watch posture `RISK_FLAG_PULLBACK_WATCH`.

`RISK_FLAG_PULLBACK_WATCH` is a **watch posture only**. It is not a
buy idea, not a 매매 신호, not a `PB_TRIGGER`, not a 본진 entry, and
not an automation hook. It exists to give the operator a labelled
status for a high-risk situation that nonetheless deserves
observation.

## Pre-Conditions (All Must Be True)

- [ ] The name's risk flag belongs to **분류 B** in
      `OFFICIAL_RISK_FLAG_TAXONOMY_KR.md` (투자주의 / 투자경고
      지정예고 / 투자경고 / 단기과열 예고 / 단기과열 지정 / 공매도
      과열).
- [ ] The name does **not** belong to **분류 A**
      (`HARD_EXCLUDE`: 관리종목, 상장폐지 실질심사, 거래정지,
      불성실공시, 감사의견 문제, 횡령/배임, 회생/파산).
- [ ] The name does **not** belong to **분류 C**
      (`EXTREME_RISK_FLAG_WATCH`: 투자위험 지정예고, 투자위험종목,
      투자경고 후 정지 임박 단계).
- [ ] The name does **not** belong to **분류 D**
      (`NO_ENTRY`: 매매거래정지, 상장폐지 실질심사 관련 정지,
      공시불이행 등 거래정지).
- [ ] The name is in a **leading sector / leading theme** during the
      relevant period.
- [ ] Either an **upward estimate revision** or a **structural
      catalyst** (industry inflection, policy tailwind, product
      cycle, end-demand shift) is identifiable from official / Tier 1
      / Tier 2 sources.
- [ ] The price action is at a **first pullback** after a primary
      advance, not a recovery from a sustained downtrend.
- [ ] **Pullback volume contracts** relative to the up-leg volume.
- [ ] **Demand re-ignition** is observable on the pullback's
      resolution (volume returns, supply-state label improves).
- [ ] A **short, logical stop level** exists. If the stop is wide or
      arbitrary, the watch posture is not entered.

## Sizing and Posture

- [ ] **TOR is set small.** The position-size envelope for any name
      in `RISK_FLAG_PULLBACK_WATCH` is strictly limited.
- [ ] Promotion is bounded by **`PB_SCOUT` or below** within the
      operator's existing pullback ladder. Promotion to `PB_TRIGGER`
      from this status is **prohibited** by this policy. A name may
      only reach `PB_TRIGGER` after the cooling-risk flag is
      formally lifted by the exchange and the name re-qualifies via
      the normal pullback path.
- [ ] No automation, no auto-alert, no auto-order is wired to this
      status.

## Hard Prohibitions

- Direct promotion to `PB_TRIGGER` while the name still carries a
  분류 B flag.
- 본진 (core position) entry while the name still carries a 분류 B
  flag.
- Adding to the position to "average down" if the price drops below
  the stop.
- Treating the lifting of the flag as an automatic re-entry
  trigger. Re-qualification follows the normal pullback path.
- Treating `RISK_FLAG_PULLBACK_WATCH` as equivalent to
  `PB_TRIGGER` in any status field, summary, or alert.

## Abort Conditions

A name in `RISK_FLAG_PULLBACK_WATCH` is removed from the watch
posture immediately if any of the following occurs:

- The name reclassifies into 분류 A (`HARD_EXCLUDE`).
- The name reclassifies into 분류 C (`EXTREME_RISK_FLAG_WATCH`).
  In that case the watch posture is replaced by
  `EXTREME_RISK_FLAG_WATCH` and new entry is held while that flag
  is active.
- The name reclassifies into 분류 D (`NO_ENTRY`).
- Pullback volume expands abnormally with adverse supply-state
  label.
- The short, logical stop level is broken intraday.
- The leading-sector / leading-theme thesis breaks.
- Any automation, auto-alert, or auto-order path is detected as
  having been wired to this status.

## Statements

- `RISK_FLAG_PULLBACK_WATCH` is a **labelled posture**, not a buy
  signal.
- The checklist's PASS state grants only watch standing — no
  authorization to execute, alert, or auto-act.
- The size envelope is intentionally smaller than a normal pullback
  setup. The risk that the cooling flag escalates (분류 C) is real
  and does not depend on the operator's view.

## Out of Scope for This PR

- Schema for the `RISK_FLAG_PULLBACK_WATCH` status field.
- Engine / validator code that consumes this status.
- Sample tickers, sample prices, sample disclosure numbers.
- Automated detection of the conditions above.
