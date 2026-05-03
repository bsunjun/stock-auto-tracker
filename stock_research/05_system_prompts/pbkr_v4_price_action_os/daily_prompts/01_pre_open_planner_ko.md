# 01 장전 플래너 (Pre-Open Planner, KST 08:00–08:50)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 목적

장 시작 전 50분 내에 **시장 레짐 → 주도 업종 → 후보 → entry tactic
후보 → TOR headroom** 순서로 정리해서 오늘 세션의 일일 포커스 리스트를
확정한다. 본 단계는 **실행 단계가 아니다**. 실행은 본장(09:15 이후)
S.N.I.P.E. 루틴에서만 일어난다.

---

## 1. 시장 레짐 (Market Cycle)

`schemas/market_cycle.schema.json` 형식으로 한 줄 요약을 만든다.

```yaml
date: YYYY-MM-DD
kospi_stage: stage_1 | stage_2 | stage_3 | stage_4
kosdaq_stage: stage_1 | stage_2 | stage_3 | stage_4
sub_grade: weak | normal | strong | n_a
k_multiplier: 0.10 | 0.50 | 1.00
stage_cap_pct: <초기 종목당 비중 한도>
inputs_summary: <한 줄, 21EMA/50SMA/200SMA, 폭, 외인, 환율, 변동성, 리더 액션, 최근 10거래 피드백>
```

레짐은 **노출 다이얼**이다. 매매 신호가 아니다.

---

## 2. 주도 업종 (Leading Groups)

- 오늘 KOSPI / KOSDAQ에서 구조적으로 견조한 업종 3개 이내.
- 각 업종에 대해: 추세 상태(`stage_2_strong` / `stage_2_normal` /
  `stage_3` 등), 최근 5세션 RS, 그룹 내 새 고가 종목 수.
- 방어주가 주도하면 그것 자체가 stage_3 신호로 기록한다.

---

## 3. 후보 정리 (Candidates)

`schemas/watchlist_item.schema.json` 형식의 watchlist에서:

- `setup_proximity = tactic_ready` 또는 `approaching` 인 종목만 선택.
- 각 후보에 대해 다음을 확정한다:
  - `edges[]` (HVE / HVIPO / HV1 / RelativeStrength / NFactor /
    GroupMove / GrowthAcceleration 중 하나 이상).
  - `setup` (LaunchPad / Gapper / BaseBreakout /
    BreakoutFirstPullback / ContinuationFlag / ReversalOfTrend).
  - 트레이드 분류 (`trade_class`): short_term / swing / position /
    leader_grade_position.
  - 성장 근거 (`growth_evidence[]`) — leader / position 분류는
    최소 두 분기 이상 누적 근거 요구.
  - **Telegram-only sourcing 후보는 daily focus 이상 승격 금지.**

---

## 4. Entry Tactic 후보

각 후보에 대해 오늘 적용 가능한 entry tactic을 1개씩만 명시한다.
`ENTRY_TACTICS_SPEC.md` §5의 9가지 중 하나.

각 tactic마다 다음을 미리 적는다 (실행 시점이 아니라 장전에):

- `trigger_level` (구체적인 가격 또는 인디케이터 레벨, 텍스트로 OK)
- `failure_level`
- `stop_logic`
- `kr_caveat` (장 시작 / 마감 호가 단일가, 가격제한, 사이드카, 점심
  거래 약화, 공시 클러스터 등)

세 필드 중 하나라도 비면 그 종목은 daily focus에서 제외한다.

---

## 5. TOR Headroom

- 현재 `total_open_risk_pct` 와 `K * tor_ceiling_pct` 비교.
- 신규 후보 N개를 모두 받았을 때의 가상 `total_open_risk_after`
  계산.
- headroom 부족 시: 우선순위 낮은 후보부터 제외하고 **5개 한도** 안에서
  **이상적으로 1~3개**까지 압축.

---

## 6. Daily Focus List 확정

`schemas/daily_focus_list.schema.json` 형식으로 1~5개 항목을 확정한다.
각 항목에 4종 안전 플래그 (`direct_trade_signal=false`,
`trade_signal=null`, `automatic_execution_allowed=false`,
`human_gate_required=true`) 가 반드시 들어가야 한다.

각 항목마다 ticket 작성을 즉시 시작한다 — 단,
`ticket_templates/trade_ticket_template.md` 형식만 채울 뿐 **실행은
하지 않는다**.

---

## 7. 금지

- 본 단계에서 신규 매매 실행 금지.
- 단정적 매수 / 매도 표현 금지.
- 가격 예측 / 목표가 금지.
- Tier-5 (Telegram-only) 단일 근거로 leader / position 분류 금지.
- `direct_trade_signal` / `trade_signal` / `automatic_execution_allowed`
  를 truthy 로 설정 금지.

---

## 8. 산출물

- 1개의 `market_cycle` 요약.
- 주도 업종 메모.
- 1~5개의 `daily_focus_list` 엔트리.
- 각 엔트리에 대한 `trade_ticket_template` 초안.

이 산출물은 audit 단계로 넘어간다 (`audit_pack`).
