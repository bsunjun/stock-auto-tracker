# 05 익일 준비 (Post-Close Next-Day Prep, KST 16:30–17:30)

> 교육용 운영 절차서. 매매 추천이 아니다.
> `direct_trade_signal = false`. `trade_signal = null` 또는 `false`.
> `automatic_execution_allowed = false`. `human_gate_required = true`.

---

## 0. 목적

다음 거래일의 daily focus list 1~5개 (이상적으로 1~3개) 를 준비한다.
이는 다음날 아침 01 장전 플래너의 **입력**이지 **최종 출력**이 아니다.
다음날 아침 시장 레짐과 갭/시초가에 따라 재검증된다.

---

## 1. Watchlist 재스코어링

`schemas/watchlist_item.schema.json` 항목별로:

- setup_proximity 갱신 (`tactic_ready` / `approaching` / `far`).
- group_state 갱신 (`constructive` / `neutral` / `deteriorating`).
- 트레이드 분류 (`trade_class`) 변경 필요성.
- thesis 약화 → `cold` 강등.
- thesis 무효 → `retired` (모델북에 회고 기록).

---

## 2. 다음날 후보 풀

후보 풀 (≤10) 을 만든다. 우선순위:

1. setup_proximity = `tactic_ready`.
2. group_state = `constructive`.
3. 다중 edge.
4. 트레이드 분류 일관성 (현재 MCS-KR 레짐과).
5. KR 지정 / 거래정지 / 자본 이벤트 부재.

---

## 3. 잠정 Daily Focus List

후보 풀에서 **1~5개** (이상적으로 1~3개) 를 선택해서 잠정 focus list
를 만든다. 각 항목에:

- `edge[]` / `setup`
- `entry_tactic` 후보 (1개) 와 `trigger_level` / `failure_level` /
  `stop_logic` / `kr_caveat` 잠정 값.
- 잠정 size_plan (current equity, 현재 stage_cap 적용).
- 잠정 sell_plan (트림 트리거, structural exit 트리거, time-stop window).

---

## 4. 다음날 아침 재검증 사항

다음 항목은 익일 아침 (01 단계) 에서 갱신한다:

- KOSPI / KOSDAQ 갭 / 시초 추정.
- 외인 / 기관 추정.
- 야간 매크로 / FX / 미 시장.
- 다음날 실시간 ETF 리밸런스 / 옵션 만기 / 공시 클러스터.
- 새로 발생한 KR 지정 / 거래정지.

---

## 5. 알림 / 트리거 준비

각 잠정 focus 항목에 대해 다음날 모니터링할 트리거 노트:

- trigger_level 도달 알림 (개인 환경 가정).
- failure_level 침범 알림.
- 그룹 변동성 변화 알림.

본 PR 패키지는 알림 시스템 자체를 만들지 않는다 — 운영자 환경의 알림
기능을 사용한다는 것을 전제한다.

---

## 6. 다음 주 리뷰 트리거 체크

오늘이 주중 마지막 거래일인 경우:

- `weekly_review/weekly_review_template.md` 를 작성한다.
- 모델북 / 저널 항목을 일주일치 통합한다.
- expectancy 와 process adherence 를 산출한다.

분기 마지막 거래일인 경우:

- 분기 실적 발표 일정 확인 후 watchlist 전체 자격 재평가 예약.

---

## 7. 금지

- 본 단계에서 신규 진입 금지.
- 단정적 매수 / 매도 표현 금지.
- 익일 진입 의무 부여 금지 — focus list 는 후보일 뿐 약속이 아니다.
- 안전 플래그 변경 금지.

---

## 8. 산출물

- 갱신된 watchlist (cold / retired 라벨 포함).
- 잠정 daily focus list (≤5).
- 항목별 잠정 trigger / failure / stop / size / sell plan 노트.
- 다음 주 / 분기 리뷰 트리거 메모 (해당 시).
