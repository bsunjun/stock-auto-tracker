# 03 본장 스나이프 체크 (Primary Window, KST 09:15–11:30)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 본 단계가 하는 일

본장 09:15–11:30 구간에서 일일 포커스 리스트의 각 종목에 대해
**S.N.I.P.E. 체크**를 수행한다. 모든 박스가 통과해야 인간 게이트
(Human Gate) 단계로 넘어간다. 인간 게이트가 통과해야 인간 운영자가
실행을 결정한다.

---

## 1. S.N.I.P.E. 체크 (각 후보별)

```
S — Setup confirmed?      (셋업 구조 유지 / 손상 여부)
N — Number / TOR ok?      (TOR + R_new ≤ K * tor_ceiling)
I — Indicator alignment?  (range expansion + volume + close strength + macro non-contradiction)
P — Price at trigger?     (trigger_level 도달 / 가격 발견 종료 후 confirmation)
E — Exit defined?         (stop_logic, sell_plan, time_stop_window 모두 명시)
```

각 항목에 대해 `yes` / `no` 만 적는다. 5개 모두 `yes` 일 때만 다음
단계로 넘어간다. 4개 이하면 종목은 **watch** 상태로 둔다.

---

## 2. 항목별 세부 체크

### 2.1 S — Setup
- 어제 / 오늘 시초 사이에 셋업 구조가 손상되지 않았는가?
- 그룹/섹터 컨텍스트가 여전히 후보를 지지하는가?

### 2.2 N — Number / TOR
- `total_open_risk_after = TOR + R_new` 계산.
- `TOR + R_new ≤ K * tor_ceiling_pct` 인가?
- 섹터 캡 / 상관관계 throttle 미위반인가?

### 2.3 I — Indicator alignment
- Range expansion: 최근 평균 대비 일중 폭이 의미 있게 확장되었는가?
- Volume: 최근 평균 대비 의미 있게 증가했는가?
- Close strength: 일중 또는 한 시간 봉 종가가 상위 구간에 있는가?
- Macro non-contradiction: 당일 매크로 이벤트나 사이드카/서킷
  브레이커가 인쇄를 왜곡하지 않는가?

### 2.4 P — Price at trigger
- `trigger_level` 에 도달했거나 도달 후 재시험을 통과했는가?
- 09:00–09:15 가격 발견 구간 인쇄에 의존하지 않는가?
- 추격 금지: trigger 위로 의미 있게 벌어진 인쇄에는 진입하지 않는다.

### 2.5 E — Exit
- `stop_level` 이 사전 정의되어 있고 종가 또는 하드 스탑 기준이
  명시되어 있는가?
- `sell_plan` 에 trim-into-strength 트리거 1개 이상, structural exit
  트리거 1개 이상이 정의되어 있는가?
- `time_stop_window_sessions` 가 정의되어 있는가?

---

## 3. 인간 게이트로의 전달

5/5 모두 `yes` 인 종목에 대해서만:

- `ticket_templates/trade_ticket_template.md` 의 모든 필드를 채운다.
- `schemas/trade_ticket.schema.json` 으로 검증한다.
- 인간 게이트(`PBKR_V4_HUMAN_GATE_INSTRUCTIONS.md`) 입력으로 보낸다.

게이트가 `pass` 를 반환해야 인간 운영자가 실행을 결정한다.
**게이트의 `pass` 자체는 실행 명령이 아니다.**

---

## 4. 보유 포지션 동시 모니터링

각 보유 종목에 대해 동시에:

- Risk stop 침범 여부 (종가 또는 하드 기준).
- Structural exit 트리거: failed higher-low, distribution print, two
  closes below MA, failure_level 침범, 섹터 붕괴, key reversal bar.
- Trim-into-strength 트리거: +5% partial / R-multiple partial /
  base extension 20–25% partial / climax-style session.
- Trim-into-weakness 트리거: 첫 close below MA / failed higher-low
  test / adverse group signal.
- Time-stop window 만료 여부.

각 트리거 발동 시 `ticket_templates/position_management_ticket_template.md`
를 작성하고 인간 게이트로 보낸다.

---

## 5. 금지

- 5/5 미만 종목 진입 금지.
- 인간 게이트 우회 금지.
- 사전 정의되지 않은 stop으로 진입 금지.
- `trigger_level` / `failure_level` 의 세션 중 임의 조정 금지
  (그것은 `tactic_drift` mistake).
- 단정적 매수 / 매도 표현 금지.
- 안전 플래그 변경 금지.

---

## 6. 산출물

- S.N.I.P.E. 체크 표 (포커스 리스트 × 5 항목).
- 통과 종목의 `trade_ticket` 검증된 인스턴스.
- 보유 종목의 `position_update` 인스턴스 (트리거 발동 시).
- 인간 게이트 입력으로 보낸 항목 ID 리스트.
