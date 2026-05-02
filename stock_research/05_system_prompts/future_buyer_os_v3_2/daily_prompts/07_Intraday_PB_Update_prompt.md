# 07_Intraday_PB_Update — Prompt

## 목적

장중(예: 13:30 KST) 기준 PB state 의 부분 갱신. 본진 매수 신호가 아니라 **상태 갱신** 입니다.

## 입력

- 오전 산출된 super_pack_v3_2.
- 장중 갱신된 키움 매수주체 net flow (Layer 6 partial).
- 장중 갱신된 차트 zone (Layer 7 partial).
- 장중 발표된 신규 risk flag (Layer 8 partial).

## 산출

- 갱신된 `pb_state_decision_pack` (오전 대비 변화 항목만).
- 변화 사유(`change_reason`) 필드 필수.

## 규칙

- 강등 (PB_TRIGGER → PB_SCOUT, PB_SCOUT → PB_READY 등)은 **즉시 반영**.
- 승격은 hard rules 를 모두 만족해야만 가능. 승격 자동 실행 금지(human gate).
- `direct_trade_signal=false`, `trade_signal in (null, false)`.
- 가격 도달만으로 승격하지 않음. 가격은 신호가 아니다.

## 금지

- "지금 매수" 출력.
- intraday 캡처에서 사용자 계좌정보 노출.
